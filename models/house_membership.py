from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .membership_status import MembershipStatus


@dataclass(frozen=True)
class HouseMembership:
    constituency: str
    constituency_id: int
    house: int
    membership_start_date: str
    membership_end_date: Optional[str]
    status: MembershipStatus
