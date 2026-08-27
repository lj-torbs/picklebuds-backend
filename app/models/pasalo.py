from datetime import datetime

from sqlalchemy import BigInteger, DECIMAL, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PasaloOffer(Base):
    __tablename__ = "pasalo_offers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True, nullable=False)
    seller_player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    asking_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Enum("open", "pending", "completed", "cancelled", name="pasalo_offer_status"),
        nullable=False,
        default="open",
    )
    offered_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class PasaloClaim(Base):
    __tablename__ = "pasalo_claims"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pasalo_offer_id: Mapped[int] = mapped_column(ForeignKey("pasalo_offers.id"), nullable=False)
    claimant_player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    reference_number: Mapped[str] = mapped_column(String(120), nullable=False)
    sender_account_name: Mapped[str] = mapped_column(String(160), nullable=False)
    receipt_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    receipt_image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    review_note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", "cancelled", name="pasalo_claim_status"),
        nullable=False,
        default="pending",
    )
    claimed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reviewed_by_owner_id: Mapped[int | None] = mapped_column(ForeignKey("owners.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
