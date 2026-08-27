from sqlalchemy import BigInteger, DECIMAL, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Venue(Base, TimestampMixin):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(
        Enum("active", "inactive", name="venue_status"),
        nullable=False,
        default="active",
    )
    image_url: Mapped[str | None] = mapped_column(String(500))


class VenueBookingSettings(Base, TimestampMixin):
    __tablename__ = "venue_booking_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), unique=True, nullable=False)
    whole_gym_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    whole_gym_price_per_hour: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    whole_gym_notes: Mapped[str | None] = mapped_column(Text)


class VenueAvailableSlot(Base):
    __tablename__ = "venue_available_slots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    slot_label: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class VenuePaymentMethod(Base, TimestampMixin):
    __tablename__ = "venue_payment_methods"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    provider: Mapped[str] = mapped_column(
        Enum("GCash", "Bank Transfer", "Maya", "Other", name="payment_provider"),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    account_name: Mapped[str] = mapped_column(String(160), nullable=False)
    account_number: Mapped[str] = mapped_column(String(120), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text)
    qr_code_image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    qr_code_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)


class Court(Base, TimestampMixin):
    __tablename__ = "courts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    surface: Mapped[str] = mapped_column(String(120), nullable=False)
    capacity_label: Mapped[str] = mapped_column(String(120), nullable=False)
    price_per_hour: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("available", "maintenance", name="court_status"),
        nullable=False,
        default="available",
    )
    booking_mode: Mapped[str] = mapped_column(
        Enum("private", "open_play", name="court_booking_mode"),
        nullable=False,
        default="private",
    )
    open_play_capacity: Mapped[int | None] = mapped_column(Integer)
    image_url: Mapped[str | None] = mapped_column(String(500))


class CourtAvailableSlot(Base):
    __tablename__ = "court_available_slots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id"), nullable=False)
    slot_label: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class RentalItem(Base, TimestampMixin):
    __tablename__ = "rental_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(
        Enum("paddle", "ball", "shoes", "net", "other", name="rental_category"),
        nullable=False,
    )
    price_per_session: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        Enum("available", "unavailable", name="rental_item_status"),
        nullable=False,
        default="available",
    )
    description: Mapped[str | None] = mapped_column(Text)
