"""Read-only JSON API for the SQLite store (members + registered interests)."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import sessionmaker

from db.schema import MemberRow, PartyRow, RegisteredInterestRow
from db.session import get_engine

_SessionLocal = sessionmaker(autoflush=False, future=True)


def _session():
    return _SessionLocal(bind=get_engine())


app = FastAPI(title="UK Parliament Interests Tracker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PartyOut(BaseModel):
    id: int
    name: str
    abbreviation: str | None


class MemberListItem(BaseModel):
    id: int
    name_display_as: str
    name_full_title: str
    constituency: str | None
    party: PartyOut | None
    interest_count: int


class MemberDetail(BaseModel):
    id: int
    name_list_as: str
    name_display_as: str
    name_full_title: str
    name_address_as: str | None
    gender: str
    thumbnail_url: str | None
    party: PartyOut | None
    constituency: str | None
    house: int | None
    membership_start_date: str | None
    status_description: str | None


class RegisteredInterestOut(BaseModel):
    interest_id: int
    category_name: str
    parent_interest_id: int | None
    interest_text: str
    created_when: str | None


class PaginatedMembers(BaseModel):
    items: list[MemberListItem]
    total: int
    skip: int
    take: int


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/members", response_model=PaginatedMembers)
def list_members(
    skip: int = Query(0, ge=0),
    take: int = Query(50, ge=1, le=200),
    q: str | None = Query(None, description="Filter by name (contains, case-insensitive)"),
) -> PaginatedMembers:
    with _session() as session:
        interest_count = (
            select(
                RegisteredInterestRow.member_id.label("mid"),
                func.count().label("cnt"),
            )
            .group_by(RegisteredInterestRow.member_id)
            .subquery()
        )

        stmt = (
            select(MemberRow, PartyRow, interest_count.c.cnt)
            .outerjoin(PartyRow, MemberRow.party_id == PartyRow.id)
            .outerjoin(interest_count, MemberRow.id == interest_count.c.mid)
        )

        count_stmt = select(func.count()).select_from(MemberRow)
        if q:
            like = f"%{q.strip()}%"
            filt = or_(
                MemberRow.name_display_as.ilike(like),
                MemberRow.name_full_title.ilike(like),
                MemberRow.name_list_as.ilike(like),
            )
            stmt = stmt.where(filt)
            count_stmt = count_stmt.where(filt)

        total = session.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(MemberRow.name_list_as).offset(skip).limit(take)
        rows = session.execute(stmt).all()

        items: list[MemberListItem] = []
        for m, party, icnt in rows:
            p_out: PartyOut | None = None
            if party is not None:
                p_out = PartyOut(
                    id=party.id,
                    name=party.name,
                    abbreviation=party.abbreviation,
                )
            items.append(
                MemberListItem(
                    id=m.id,
                    name_display_as=m.name_display_as,
                    name_full_title=m.name_full_title,
                    constituency=m.constituency,
                    party=p_out,
                    interest_count=int(icnt or 0),
                )
            )

        return PaginatedMembers(items=items, total=total, skip=skip, take=take)


@app.get("/api/members/{member_id}", response_model=MemberDetail)
def get_member(member_id: int) -> MemberDetail:
    with _session() as session:
        row = session.execute(
            select(MemberRow, PartyRow)
            .outerjoin(PartyRow, MemberRow.party_id == PartyRow.id)
            .where(MemberRow.id == member_id)
        ).first()
        if row is None:
            raise HTTPException(status_code=404, detail="Member not found")
        m, party = row
        p_out: PartyOut | None = None
        if party is not None:
            p_out = PartyOut(
                id=party.id, name=party.name, abbreviation=party.abbreviation
            )
        return MemberDetail(
            id=m.id,
            name_list_as=m.name_list_as,
            name_display_as=m.name_display_as,
            name_full_title=m.name_full_title,
            name_address_as=m.name_address_as,
            gender=m.gender,
            thumbnail_url=m.thumbnail_url,
            party=p_out,
            constituency=m.constituency,
            house=m.house,
            membership_start_date=m.membership_start_date,
            status_description=m.status_description,
        )


@app.get("/api/members/{member_id}/interests", response_model=list[RegisteredInterestOut])
def get_interests(member_id: int) -> list[RegisteredInterestOut]:
    with _session() as session:
        exists = session.execute(
            select(MemberRow.id).where(MemberRow.id == member_id)
        ).first()
        if exists is None:
            raise HTTPException(status_code=404, detail="Member not found")

        stmt = (
            select(RegisteredInterestRow)
            .where(RegisteredInterestRow.member_id == member_id)
            .order_by(
                RegisteredInterestRow.category_sort_order.nulls_last(),
                RegisteredInterestRow.category_name,
                RegisteredInterestRow.interest_id,
            )
        )
        rows = session.execute(stmt).scalars().all()
        return [
            RegisteredInterestOut(
                interest_id=r.interest_id,
                category_name=r.category_name,
                parent_interest_id=r.parent_interest_id,
                interest_text=r.interest_text,
                created_when=r.created_when,
            )
            for r in rows
        ]


def main() -> None:
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["api", "db"],
    )


if __name__ == "__main__":
    main()
