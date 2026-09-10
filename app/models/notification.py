from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    recipient_type: Mapped[str] = mapped_column(
        Enum("player", "owner", name="notification_recipient_type"),
        nullable=False,
    )
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("owners.id"))
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"))
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    action_url: Mapped[str | None] = mapped_column(String(255))
    is_read: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
