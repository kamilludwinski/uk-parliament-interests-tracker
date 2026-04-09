from __future__ import annotations

import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

from db import save_members, session_scope, upgrade_head
from models import Member

_PROJECT_ROOT = Path(__file__).resolve().parent
_DEFAULT_LOG_PATH = _PROJECT_ROOT / "members.log"

_TAKE = 20
_BASE_URL_FMT = (
    "https://members-api.parliament.uk/api/Members/Search?skip={skip}&take={take}"
)
_REQUEST_TIMEOUT = (15.0, 45.0)
_PROGRESS_EVERY = 5
_HEARTBEAT_INTERVAL_S = 12.0
_WORKERS_DEFAULT = 1
_WORKERS_MAX = 8


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
    log = logging.getLogger("members")
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


def _get_url(skip: int = 0) -> str:
    return _BASE_URL_FMT.format(skip=skip, take=_TAKE)


def _fetch_search_json(skip: int) -> tuple[dict[str, Any], float]:
    log = logging.getLogger("members")
    url = _get_url(skip)
    log.debug("http_request_start skip=%s url=%s", skip, url)
    t_fetch = time.monotonic()
    try:
        response = requests.get(url, timeout=_REQUEST_TIMEOUT)
    except requests.RequestException:
        log.exception("http_request_error skip=%s", skip)
        raise
    fetch_s = time.monotonic() - t_fetch
    log.debug(
        "http_request_done skip=%s status=%s fetch_ms=%.0f",
        skip,
        response.status_code,
        fetch_s * 1000.0,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Members search failed (skip={skip}): HTTP {response.status_code}"
        )
    return response.json(), fetch_s


def _members_from_page(skip: int) -> tuple[int, list[Member], float, float]:
    data, fetch_s = _fetch_search_json(skip)
    t_parse0 = time.monotonic()
    items = data.get("items") or []
    members = [Member.from_dict(row) for row in items]
    parse_s = time.monotonic() - t_parse0
    return skip, members, fetch_s, parse_s


def main(*, workers: int = _WORKERS_DEFAULT, log_path: Path | None = None) -> None:
    path = log_path or _DEFAULT_LOG_PATH
    upgrade_head()
    log = _configure_logging(path)

    workers = min(workers, _WORKERS_MAX)
    max_workers = max(_WORKERS_DEFAULT, workers)

    log.info(
        "Log file (verbose): %s | Syncing members (take=%s, %s workers).",
        path.resolve(),
        _TAKE,
        max_workers,
    )

    data0, fetch0 = _fetch_search_json(0)
    total = int(data0["totalResults"])
    t_parse0 = time.monotonic()
    page0 = [Member.from_dict(row) for row in data0.get("items") or []]
    parse0 = time.monotonic() - t_parse0

    log.debug(
        "page skip=0 members=%s fetch_ms=%.0f parse_ms=%.0f total_reported=%s",
        len(page0),
        fetch0 * 1000.0,
        parse0 * 1000.0,
        total,
    )

    if page0:
        t_save0 = time.monotonic()
        with session_scope() as session:
            save_members(session, page0)
        log.debug(
            "save skip=0 batch_size=%s save_ms=%.0f",
            len(page0),
            (time.monotonic() - t_save0) * 1000.0,
        )
        log.info(
            "saved %s members (skip=0 / ~%s total)",
            len(page0),
            total,
        )

    remaining = list(range(_TAKE, total, _TAKE))
    if not remaining:
        if page0:
            log.info("example: %r", page0[0])
        log.info("done: %s members (see %s for DEBUG)", len(page0), path.resolve())
        return

    save_lock = threading.Lock()
    saved = len(page0)
    t0 = time.monotonic()
    completed = 0

    heartbeat_stop = threading.Event()
    progress_snapshot: dict[str, int] = {
        "saved": saved,
        "pages_done": 0,
        "pages_total": len(remaining),
    }

    def _heartbeat_loop() -> None:
        while not heartbeat_stop.wait(_HEARTBEAT_INTERVAL_S):
            log.info(
                "heartbeat | cumulative members %s/%s | pages %s/%s | %.0fs — "
                "see %s for HTTP DEBUG",
                progress_snapshot["saved"],
                total,
                progress_snapshot["pages_done"],
                progress_snapshot["pages_total"],
                time.monotonic() - t0,
                path.resolve(),
            )

    hb = threading.Thread(target=_heartbeat_loop, daemon=True)
    hb.start()

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_members_from_page, sk): sk for sk in remaining}
            for fut in as_completed(futures):
                skip, batch, fetch_s, parse_s = fut.result()
                completed += 1
                progress_snapshot["pages_done"] = completed
                if not batch:
                    log.debug("empty_batch skip=%s", skip)
                    continue

                t_save_start = time.monotonic()
                with save_lock:
                    with session_scope() as session:
                        save_members(session, batch)
                save_s = time.monotonic() - t_save_start

                saved += len(batch)
                progress_snapshot["saved"] = saved
                elapsed = time.monotonic() - t0

                log.debug(
                    "skip=%s batch_size=%s fetch_ms=%.0f parse_ms=%.0f save_ms=%.0f "
                    "cumulative_members=%s",
                    skip,
                    len(batch),
                    fetch_s * 1000.0,
                    parse_s * 1000.0,
                    save_s * 1000.0,
                    saved,
                )

                if (
                    completed == 1
                    or completed % _PROGRESS_EVERY == 0
                    or completed == len(remaining)
                    or saved >= total
                ):
                    log.info(
                        "saved %s members (skip=%s, cumulative=%s/%s) | %.0fs",
                        len(batch),
                        skip,
                        saved,
                        total,
                        elapsed,
                    )
    finally:
        heartbeat_stop.set()

    elapsed = time.monotonic() - t0
    log.info(
        "done: %s members persisted (reported total=%s) in %.0fs — DEBUG: %s",
        saved,
        total,
        elapsed,
        path.resolve(),
    )


if __name__ == "__main__":
    main(workers=8)
