"""registered_interests table

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "registered_interests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("category_name", sa.Text(), nullable=False),
        sa.Column("category_sort_order", sa.Integer(), nullable=True),
        sa.Column("parent_interest_id", sa.Integer(), nullable=True),
        sa.Column("interest_text", sa.Text(), nullable=False),
        sa.Column("created_when", sa.Text(), nullable=True),
        sa.Column("last_amended_when", sa.Text(), nullable=True),
        sa.Column("deleted_when", sa.Text(), nullable=True),
        sa.Column("is_correction", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["parent_interest_id"],
            ["registered_interests.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_registered_interests_member_id",
        "registered_interests",
        ["member_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_registered_interests_member_id", table_name="registered_interests")
    op.drop_table("registered_interests")
