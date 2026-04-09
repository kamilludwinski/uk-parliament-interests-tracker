from __future__ import annotations

import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Literal

import requests
from sqlalchemy import select

from db import session_scope, upgrade_head
from db.persist_interests import interest_rows_from_payload, replace_member_interests
from db.schema import MemberRow

_PROJECT_ROOT = Path(__file__).resolve().parent
_DEFAULT_LOG_PATH = _PROJECT_ROOT / "registered_interests.log"

_BASE_URL_FMT = (
    "https://members-api.parliament.uk/api/Members/{member_id}/RegisteredInterests"
)

_REQUEST_TIMEOUT = (15.0, 45.0)
_PROGRESS_EVERY = 5
_HEARTBEAT_INTERVAL_S = 12.0
_WORKERS_DEFAULT = 1
_WORKERS_MAX = 8

# Transient API / rate-limit responses — retry with backoff instead of aborting the run.
_RETRYABLE_HTTP = frozenset({429, 500, 502, 503, 504})
_MAX_FETCH_ATTEMPTS = 5
_RETRY_BACKOFF_CAP_S = 30.0


def _retry_delay_s(attempt_index: int) -> float:
    return min(_RETRY_BACKOFF_CAP_S, 2.0**attempt_index)


class _FlushingStreamHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


class _FlushingFileHandler(logging.FileHandler):
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


def _configure_logging(log_path: Path) -> logging.Logger:
    # Must run after Alembic's fileConfig (see upgrade_head): that call disables
    # loggers not listed in alembic.ini, which would silence a pre-existing logger.
    log = logging.getLogger("registered_interests")
    log.disabled = False
    log.setLevel(logging.DEBUG)
    log.handlers.clear()
    log.propagate = False

    fh = _FlushingFileHandler(log_path, encoding="utf-8", mode="a")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    sh = _FlushingStreamHandler(sys.stderr)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter("%(message)s"))

    log.addHandler(fh)
    log.addHandler(sh)
    return log


def _fetch_payload(
    member_id: int,
) -> tuple[int, dict[str, Any] | None, float, Literal["persist", "skip"]]:
    """Return JSON (or None for 404), total HTTP time, and whether to write DB.

    ``persist``: replace stored interests for this member (including empty when 404).
    ``skip``: do not change the DB — use after repeated network / server failures so a
    transient HTTP 500 does not wipe existing rows or stop the whole sync.
    """
    log = logging.getLogger("registered_interests")
    url = _BASE_URL_FMT.format(member_id=member_id)
    total_fetch_s = 0.0

    for attempt in range(_MAX_FETCH_ATTEMPTS):
        log.debug(
            "http_request_start member_id=%s url=%s attempt=%s/%s",
            member_id,
            url,
            attempt + 1,
            _MAX_FETCH_ATTEMPTS,
        )
        t_req = time.monotonic()
        try:
            response = requests.get(url, timeout=_REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            total_fetch_s += time.monotonic() - t_req
            log.warning(
                "http_request_error member_id=%s attempt=%s/%s: %s",
                member_id,
                attempt + 1,
                _MAX_FETCH_ATTEMPTS,
                exc,
            )
            if attempt == _MAX_FETCH_ATTEMPTS - 1:
                return member_id, None, total_fetch_s, "skip"
            time.sleep(_retry_delay_s(attempt))
            continue

        elapsed_req = time.monotonic() - t_req
        total_fetch_s += elapsed_req
        status = response.status_code
        log.debug(
            "http_request_done member_id=%s status=%s fetch_ms=%.0f (cumulative_http_ms=%.0f)",
            member_id,
            status,
            elapsed_req * 1000.0,
            total_fetch_s * 1000.0,
        )

        if status == 404:
            return member_id, None, total_fetch_s, "persist"
        if status == 200:
            return member_id, response.json(), total_fetch_s, "persist"
        if status in _RETRYABLE_HTTP and attempt < _MAX_FETCH_ATTEMPTS - 1:
            delay = _retry_delay_s(attempt)
            log.warning(
                "http_retry member_id=%s HTTP %s attempt=%s/%s sleeping %.1fs",
                member_id,
                status,
                attempt + 1,
                _MAX_FETCH_ATTEMPTS,
                delay,
            )
            time.sleep(delay)
            continue

        log.error(
            "http_give_up member_id=%s HTTP %s after %s attempts — leaving DB unchanged for this member",
            member_id,
            status,
            attempt + 1,
        )
        return member_id, None, total_fetch_s, "skip"

    return member_id, None, total_fetch_s, "skip"


def main(*, workers: int = 8, log_path: Path | None = None) -> None:
    path = log_path or _DEFAULT_LOG_PATH
    upgrade_head()
    log = _configure_logging(path)

    workers = min(workers, _WORKERS_MAX)
    max_workers = max(_WORKERS_DEFAULT, workers)

    with session_scope() as session:
        member_ids = list(session.scalars(select(MemberRow.id)).all())

    if not member_ids:
        log.info("No members found in database")
        return

    total = len(member_ids)
    save_lock = threading.Lock()
    done = 0
    skipped_members = 0
    total_interest_rows = 0
    t0 = time.monotonic()

    log.info(
        "Log file (verbose): %s | Fetching registered interests for %s members (%s workers).",
        path.resolve(),
        total,
        max_workers,
    )

    heartbeat_stop = threading.Event()
    progress_snapshot: dict[str, Any] = {
        "done": 0,
        "total": total,
        "rows": 0,
        "phase": "running",
        "active_member_id": None,
        "pending_rows": 0,
    }

    def _heartbeat_loop() -> None:
        while not heartbeat_stop.wait(_HEARTBEAT_INTERVAL_S):
            log.info(
                "heartbeat | done %s/%s | rows %s | %.0fs | phase=%s member=%s pending_rows=%s",
                progress_snapshot["done"],
                progress_snapshot["total"],
                progress_snapshot["rows"],
                time.monotonic() - t0,
                progress_snapshot["phase"],
                progress_snapshot["active_member_id"],
                progress_snapshot["pending_rows"],
            )

    heartbeat = threading.Thread(target=_heartbeat_loop, daemon=True)
    heartbeat.start()

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_fetch_payload, mid): mid for mid in member_ids}
            for fut in as_completed(futures):
                t_iter = time.monotonic()
                member_id, payload, fetch_s, write_mode = fut.result()

                if write_mode == "skip":
                    skipped_members += 1
                    done += 1
                    elapsed = time.monotonic() - t0
                    progress_snapshot["done"] = done
                    progress_snapshot["rows"] = total_interest_rows
                    log.warning(
                        "skipped member_id=%s (API failed after retries) — DB unchanged | "
                        "skipped_total=%s | done %s/%s",
                        member_id,
                        skipped_members,
                        done,
                        total,
                    )
                    if done == 1 or done % _PROGRESS_EVERY == 0 or done == total:
                        rate = done / elapsed if elapsed > 0 else 0.0
                        log.info(
                            "progress %s/%s | %.0fs | %.1f members/s | rows sum %s | skipped %s | last=%s",
                            done,
                            total,
                            elapsed,
                            rate,
                            total_interest_rows,
                            skipped_members,
                            member_id,
                        )
                    continue

                t_after_result = time.monotonic()
                if payload is None:
                    rows = []
                else:
                    rows = interest_rows_from_payload(member_id, payload)
                t_after_parse = time.monotonic()

                progress_snapshot["phase"] = "sqlite_save"
                progress_snapshot["active_member_id"] = member_id
                progress_snapshot["pending_rows"] = len(rows)

                with save_lock:
                    with session_scope() as session:
                        replace_member_interests(session, member_id, rows)
                t_after_save = time.monotonic()

                progress_snapshot["phase"] = "fetch_parse"
                progress_snapshot["active_member_id"] = None
                progress_snapshot["pending_rows"] = 0

                done += 1
                n = len(rows)
                total_interest_rows += n
                elapsed = time.monotonic() - t0

                parse_ms = (t_after_parse - t_after_result) * 1000.0
                save_ms = (t_after_save - t_after_parse) * 1000.0
                handle_ms = (t_after_save - t_iter) * 1000.0

                log.debug(
                    "member_id=%s rows=%s fetch_ms=%.0f parse_ms=%.0f save_ms=%.0f "
                    "handle_ms=%.0f cumulative_members=%s cumulative_rows=%s",
                    member_id,
                    n,
                    fetch_s * 1000.0,
                    parse_ms,
                    save_ms,
                    handle_ms,
                    done,
                    total_interest_rows,
                )

                progress_snapshot["done"] = done
                progress_snapshot["rows"] = total_interest_rows

                if done == 1 or done % _PROGRESS_EVERY == 0 or done == total:
                    rate = done / elapsed if elapsed > 0 else 0.0
                    log.info(
                        "progress %s/%s | %.0fs | %.1f members/s | "
                        "interest rows +%s (sum %s) | skipped %s | last member_id=%s",
                        done,
                        total,
                        elapsed,
                        rate,
                        n,
                        total_interest_rows,
                        skipped_members,
                        member_id,
                    )
    finally:
        heartbeat_stop.set()

    elapsed = time.monotonic() - t0
    log.info(
        "done: processed %s members, %s interest rows, %s skipped (API errors) in %.0fs — %s",
        total,
        total_interest_rows,
        skipped_members,
        elapsed,
        path.resolve(),
    )


if __name__ == "__main__":
    main(workers=8)
