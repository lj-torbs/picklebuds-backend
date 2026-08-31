from datetime import date, datetime

from sqlalchemy import BigInteger, DECIMAL, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    original_player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    court_id: Mapped[int | None] = mapped_column(ForeignKey("courts.id"))
    booking_type: Mapped[str] = mapped_column(
        Enum("private", "open_play", "whole_gym", name="booking_type"),
        nullable=False,
        default="private",
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    participant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        Enum("pending", "confirmed", "completed", "cancelled", name="booking_status"),
        nullable=False,
        default="pending",
    )
    payment_status: Mapped[str] = mapped_column(
        Enum("unpaid", "paid", "refunded", name="booking_payment_status"),
        nullable=False,
        default="unpaid",
    )
    booked_by_name_snapshot: Mapped[str] = mapped_column(String(120), nullable=False)
    booked_by_email_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    owner_name_snapshot: Mapped[str | None] = mapped_column(String(120))
    owner_email_snapshot: Mapped[str | None] = mapped_column(String(160))
    base_amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0)
    rental_amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0)


class BookingSlot(Base):
    __tablename__ = "booking_slots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    slot_label: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class BookingPayment(Base, TimestampMixin):
    __tablename__ = "booking_payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True, nullable=False)
    venue_payment_method_id: Mapped[int | None] = mapped_column(
        ForeignKey("venue_payment_methods.id")
    )
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    payment_method_label: Mapped[str] = mapped_column(String(120), nullable=False)
    review_status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", name="payment_review_status"),
        nullable=False,
        default="pending",
    )
    payment_status: Mapped[str] = mapped_column(
        Enum("unpaid", "paid", "refunded", name="payment_status"),
        nullable=False,
        default="unpaid",
    )
    reference_number: Mapped[str | None] = mapped_column(String(120))
    sender_account_name: Mapped[str | None] = mapped_column(String(160))
    receipt_file_name: Mapped[str | None] = mapped_column(String(255))
    receipt_image_url: Mapped[str | None] = mapped_column(Text)
    receipt_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime)
    review_note: Mapped[str | None] = mapped_column(Text)
    approved_by_owner_id: Mapped[int | None] = mapped_column(ForeignKey("owners.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime)


class BookingRental(Base):
    __tablename__ = "booking_rentals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    rental_item_id: Mapped[int] = mapped_column(ForeignKey("rental_items.id"), nullable=False)
    item_name_snapshot: Mapped[str] = mapped_column(String(120), nullable=False)
    category_snapshot: Mapped[str] = mapped_column(
        Enum("paddle", "ball", "shoes", "net", "other", name="booking_rental_category"),
        nullable=False,
    )
    price_per_session_snapshot: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
