from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PartyRow(Base):
    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    abbreviation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_independent: Mapped[bool] = mapped_column(Boolean(), nullable=False)


class MemberRow(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_list_as: Mapped[str] = mapped_column(Text(), nullable=False)
    name_display_as: Mapped[str] = mapped_column(Text(), nullable=False)
    name_full_title: Mapped[str] = mapped_column(Text(), nullable=False)
    name_address_as: Mapped[str | None] = mapped_column(Text(), nullable=True)
    gender: Mapped[str] = mapped_column(String(8), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text(), nullable=True)

    party_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("parties.id", ondelete="SET NULL"), nullable=True
    )

    constituency: Mapped[str | None] = mapped_column(Text(), nullable=True)
    constituency_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    house: Mapped[int | None] = mapped_column(Integer, nullable=True)
    membership_start_date: Mapped[str | None] = mapped_column(Text(), nullable=True)
    membership_end_date: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status_is_active: Mapped[bool | None] = mapped_column(Boolean(), nullable=True)
    status_description: Mapped[str | None] = mapped_column(Text(), nullable=True)
