"""Interest IDs are per-member; use (member_id, interest_id) PK

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_registered_interests_member_id", table_name="registered_interests")
    op.rename_table("registered_interests", "registered_interests_old")

    op.create_table(
        "registered_interests",
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("interest_id", sa.Integer(), nullable=False),
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
            ["member_id", "parent_interest_id"],
            ["registered_interests.member_id", "registered_interests.interest_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("member_id", "interest_id"),
    )
    op.create_index(
        "ix_registered_interests_member_id",
        "registered_interests",
        ["member_id"],
        unique=False,
    )

    # Bulk copy row order may not respect parent-before-child; FKs are restored post-copy.
    op.execute(text("PRAGMA foreign_keys=OFF"))
    op.execute(
        """
        INSERT INTO registered_interests (
            member_id, interest_id, category_id, category_name, category_sort_order,
            parent_interest_id, interest_text, created_when, last_amended_when,
            deleted_when, is_correction
        )
        SELECT
            member_id, id, category_id, category_name, category_sort_order,
            parent_interest_id, interest_text, created_when, last_amended_when,
            deleted_when, is_correction
        FROM registered_interests_old
        """
    )
    op.execute(text("PRAGMA foreign_keys=ON"))
    op.drop_table("registered_interests_old")


def downgrade() -> None:
    op.drop_index("ix_registered_interests_member_id", table_name="registered_interests")
    op.rename_table("registered_interests", "registered_interests_new")

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
    op.execute(
        """
        INSERT INTO registered_interests (
            id, member_id, category_id, category_name, category_sort_order,
            parent_interest_id, interest_text, created_when, last_amended_when,
            deleted_when, is_correction
        )
        SELECT
            interest_id, member_id, category_id, category_name, category_sort_order,
            parent_interest_id, interest_text, created_when, last_amended_when,
            deleted_when, is_correction
        FROM registered_interests_new
        """
    )
    op.drop_table("registered_interests_new")
