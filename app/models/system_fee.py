from sqlalchemy import BigInteger, DECIMAL, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


mysql_unsigned_bigint = BigInteger().with_variant(BIGINT(unsigned=True), "mysql")


class OwnerSystemFeeSetting(Base, TimestampMixin):
    __tablename__ = "owner_system_fee_settings"
    __table_args__ = (UniqueConstraint("owner_id", name="uq_owner_system_fee_owner"),)

    id: Mapped[int] = mapped_column(
        mysql_unsigned_bigint,
        primary_key=True,
        autoincrement=True,
    )
    owner_id: Mapped[int] = mapped_column(
        mysql_unsigned_bigint,
        ForeignKey("owners.id"),
        nullable=False,
    )
    fee_per_transaction: Mapped[float] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=10,
    )
