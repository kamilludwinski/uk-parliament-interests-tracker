from __future__ import annotations

from alembic import command
from alembic.config import Config

from db.config import PROJECT_ROOT


def upgrade_head() -> None:
    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.upgrade(cfg, "head")
