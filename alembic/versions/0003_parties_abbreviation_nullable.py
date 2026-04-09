"""parties.abbreviation nullable (API may omit)

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("parties", schema=None) as batch_op:
        batch_op.alter_column(
            "abbreviation",
            existing_type=sa.String(length=32),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("parties", schema=None) as batch_op:
        batch_op.alter_column(
            "abbreviation",
            existing_type=sa.String(length=32),
            nullable=False,
        )
