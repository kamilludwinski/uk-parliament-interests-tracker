from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests

from db import save_members, session_scope, upgrade_head
from models import Member

_TAKE = 20
_BASE_URL_FMT = (
    "https://members-api.parliament.uk/api/Members/Search?skip={skip}&take={take}"
)
_REQUEST_TIMEOUT_S = 60
_WORKERS_MAX = 8


def _get_url(skip: int = 0) -> str:
    return _BASE_URL_FMT.format(skip=skip, take=_TAKE)


def _get_search_json(skip: int) -> dict[str, Any]:
    response = requests.get(_get_url(skip), timeout=_REQUEST_TIMEOUT_S)
    if response.status_code != 200:
        raise RuntimeError(
            f"Members search failed (skip={skip}): HTTP {response.status_code}"
        )
    return response.json()


def _members_from_page(skip: int) -> tuple[int, list[Member]]:
    data = _get_search_json(skip)
    items = data.get("items") or []
    return skip, [Member.from_dict(row) for row in items]


def main(*, workers: int = 1) -> None:
    upgrade_head()

    workers = min(workers, _WORKERS_MAX)

    first = _get_search_json(0)
    total = int(first["totalResults"])
    page0 = [Member.from_dict(row) for row in first.get("items") or []]

    if page0:
        with session_scope() as session:
            save_members(session, page0)
        print(f"saved {len(page0)} members (skip=0 / ~{total} total)", flush=True)

    remaining = list(range(_TAKE, total, _TAKE))
    if not remaining:
        if page0:
            print(f"example: {page0[0]!r}")
        return

    save_lock = threading.Lock()
    saved = len(page0)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(_members_from_page, sk): sk for sk in remaining}
        for fut in as_completed(futures):
            skip, batch = fut.result()
            if not batch:
                continue
            with save_lock:
                with session_scope() as session:
                    save_members(session, batch)
            saved += len(batch)
            print(
                f"saved {len(batch)} members (skip={skip}, cumulative={saved}/{total})",
                flush=True,
            )

    print(f"done: {saved} members persisted (reported total={total})")


if __name__ == "__main__":
    main(workers=8)
