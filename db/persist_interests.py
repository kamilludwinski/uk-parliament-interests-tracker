from __future__ import annotations

from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from db.schema import RegisteredInterestRow


def _str_or_none(v: Any) -> str | None:
    if v is None:
        return None
    return str(v)


def _bool_or_none(v: Any) -> bool | None:
    if v is None:
        return None
    return bool(v)


def interest_rows_from_payload(
    member_id: int, data: dict[str, Any]
) -> list[RegisteredInterestRow]:
    rows: list[RegisteredInterestRow] = []
    for cat in data.get("value") or []:
        cat_id = int(cat["id"])
        cat_name = str(cat["name"])
        sort_raw = cat.get("sortOrder")
        sort_order: int | None = int(sort_raw) if sort_raw is not None else None
        for node in cat.get("interests") or []:
            _append_interest_tree(
                member_id,
                cat_id,
                cat_name,
                sort_order,
                node,
                None,
                rows,
            )
    return rows


def _append_interest_tree(
    member_id: int,
    category_id: int,
    category_name: str,
    category_sort_order: int | None,
    node: dict[str, Any],
    parent_interest_id: int | None,
    rows: list[RegisteredInterestRow],
) -> None:
    rows.append(
        RegisteredInterestRow(
            member_id=member_id,
            interest_id=int(node["id"]),
            category_id=category_id,
            category_name=category_name,
            category_sort_order=category_sort_order,
            parent_interest_id=parent_interest_id,
            interest_text=str(node["interest"]),
            created_when=_str_or_none(node.get("createdWhen")),
            last_amended_when=_str_or_none(node.get("lastAmendedWhen")),
            deleted_when=_str_or_none(node.get("deletedWhen")),
            is_correction=_bool_or_none(node.get("isCorrection")),
        )
    )
    for child in node.get("childInterests") or []:
        _append_interest_tree(
            member_id,
            category_id,
            category_name,
            category_sort_order,
            child,
            int(node["id"]),
            rows,
        )


def replace_member_interests(
    session: Session,
    member_id: int,
    rows: list[RegisteredInterestRow],
) -> None:
    session.execute(
        delete(RegisteredInterestRow).where(
            RegisteredInterestRow.member_id == member_id
        )
    )
    for row in rows:
        session.add(row)
