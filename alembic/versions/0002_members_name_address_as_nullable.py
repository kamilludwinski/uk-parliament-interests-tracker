"""name_address_as may be null from API

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("members", schema=None) as batch_op:
        batch_op.alter_column(
            "name_address_as",
            existing_type=sa.Text(),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("members", schema=None) as batch_op:
        batch_op.alter_column(
            "name_address_as",
            existing_type=sa.Text(),
            nullable=False,
        )
