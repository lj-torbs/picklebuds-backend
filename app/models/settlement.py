from datetime import date, datetime

from sqlalchemy import BigInteger, DECIMAL, Date, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class OwnerSettlement(Base, TimestampMixin):
    __tablename__ = "owner_settlements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    gross_revenue: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0)
    system_share: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0)
    owner_total_profit: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0)
    payment_status: Mapped[str] = mapped_column(
        Enum("paid", "unpaid", name="owner_settlement_payment_status"),
        nullable=False,
        default="unpaid",
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime)
    note: Mapped[str | None] = mapped_column(Text)
