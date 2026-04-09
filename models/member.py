from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .house_membership import HouseMembership
from .membership_status import MembershipStatus
from .party import Party


@dataclass(frozen=True)
class Member:
    id: int
    name_list_as: str
    name_display_as: str
    name_full_title: str
    name_address_as: Optional[str]
    gender: str
    party: Optional[Party]
    latest_house_membership: Optional[HouseMembership]
    thumbnail_url: Optional[str]

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> Member:
        v = item["value"]
        party_data = v.get("latestParty")
        party: Optional[Party] = None
        if party_data:
            party = Party(
                id=party_data["id"],
                name=party_data["name"],
                abbreviation=party_data.get("abbreviation"),
                is_independent=party_data.get("isIndependentParty", False),
            )

        hm_data = v.get("latestHouseMembership")
        house_membership: Optional[HouseMembership] = None
        if hm_data:
            ms = hm_data.get("membershipStatus") or {}
            house_membership = HouseMembership(
                constituency=hm_data["membershipFrom"],
                constituency_id=hm_data["membershipFromId"],
                house=hm_data["house"],
                membership_start_date=hm_data["membershipStartDate"],
                membership_end_date=hm_data.get("membershipEndDate"),
                status=MembershipStatus(
                    is_active=ms.get("statusIsActive", False),
                    description=ms.get("statusDescription") or "",
                ),
            )

        return cls(
            id=v["id"],
            name_list_as=v["nameListAs"],
            name_display_as=v["nameDisplayAs"],
            name_full_title=v["nameFullTitle"],
            name_address_as=v.get("nameAddressAs"),
            gender=v["gender"],
            party=party,
            latest_house_membership=house_membership,
            thumbnail_url=v.get("thumbnailUrl"),
        )
