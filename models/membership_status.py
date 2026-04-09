from dataclasses import dataclass


@dataclass(frozen=True)
class MembershipStatus:
    is_active: bool
    description: str
