"""initial parties and members tables

Revision ID: 0001
Revises:
Create Date: 2026-04-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "parties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("abbreviation", sa.String(length=32), nullable=False),
        sa.Column("is_independent", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name_list_as", sa.Text(), nullable=False),
        sa.Column("name_display_as", sa.Text(), nullable=False),
        sa.Column("name_full_title", sa.Text(), nullable=False),
        sa.Column("name_address_as", sa.Text(), nullable=False),
        sa.Column("gender", sa.String(length=8), nullable=False),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("party_id", sa.Integer(), nullable=True),
        sa.Column("constituency", sa.Text(), nullable=True),
        sa.Column("constituency_id", sa.Integer(), nullable=True),
        sa.Column("house", sa.Integer(), nullable=True),
        sa.Column("membership_start_date", sa.Text(), nullable=True),
        sa.Column("membership_end_date", sa.Text(), nullable=True),
        sa.Column("status_is_active", sa.Boolean(), nullable=True),
        sa.Column("status_description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["party_id"],
            ["parties.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("members")
    op.drop_table("parties")
