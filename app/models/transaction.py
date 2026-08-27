from datetime import datetime

from sqlalchemy import BigInteger, DECIMAL, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True, nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    court_id: Mapped[int | None] = mapped_column(ForeignKey("courts.id"))
    booking_type: Mapped[str] = mapped_column(
        Enum("private", "open_play", "whole_gym", name="transaction_booking_type"),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    payment_method_label: Mapped[str] = mapped_column(String(120), nullable=False)
    payment_status: Mapped[str] = mapped_column(
        Enum("unpaid", "paid", "refunded", name="transaction_payment_status"),
        nullable=False,
        default="paid",
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "confirmed", "completed", "cancelled", name="transaction_status"),
        nullable=False,
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
