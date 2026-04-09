from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Party:
    id: int
    name: str
    abbreviation: Optional[str]
    is_independent: bool
