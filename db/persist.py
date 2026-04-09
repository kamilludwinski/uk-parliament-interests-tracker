from __future__ import annotations

from sqlalchemy.orm import Session

from db.schema import MemberRow, PartyRow
from models import Member, Party


def save_members(session: Session, members: list[Member]) -> None:
    parties: dict[int, Party] = {}
    for m in members:
        if m.party is not None:
            parties[m.party.id] = m.party

    for p in parties.values():
        session.merge(
            PartyRow(
                id=p.id,
                name=p.name,
                abbreviation=p.abbreviation,
                is_independent=p.is_independent,
            )
        )

    session.flush()

    for m in members:
        hm = m.latest_house_membership
        session.merge(
            MemberRow(
                id=m.id,
                name_list_as=m.name_list_as,
                name_display_as=m.name_display_as,
                name_full_title=m.name_full_title,
                name_address_as=m.name_address_as,
                gender=m.gender,
                thumbnail_url=m.thumbnail_url,
                party_id=m.party.id if m.party is not None else None,
                constituency=hm.constituency if hm is not None else None,
                constituency_id=hm.constituency_id if hm is not None else None,
                house=hm.house if hm is not None else None,
                membership_start_date=hm.membership_start_date
                if hm is not None
                else None,
                membership_end_date=hm.membership_end_date
                if hm is not None
                else None,
                status_is_active=hm.status.is_active if hm is not None else None,
                status_description=hm.status.description if hm is not None else None,
            )
        )
