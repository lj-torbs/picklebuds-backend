from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


mysql_unsigned_bigint = BigInteger().with_variant(BIGINT(unsigned=True), "mysql")


class OwnerBrandingSettings(Base, TimestampMixin):
    __tablename__ = "owner_branding_settings"
    __table_args__ = (UniqueConstraint("owner_id", name="uq_owner_branding_owner"),)

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
    brand_name: Mapped[str] = mapped_column(String(160), nullable=False)
    logo_image_url: Mapped[str | None] = mapped_column(
        Text().with_variant(LONGTEXT, "mysql")
    )
    primary_color: Mapped[str] = mapped_column(String(16), nullable=False, default="#65c466")
    sidebar_color: Mapped[str] = mapped_column(String(16), nullable=False, default="#0f172a")
    surface_color: Mapped[str] = mapped_column(String(16), nullable=False, default="#f8fafc")
    density: Mapped[str] = mapped_column(
        Enum("comfortable", "compact", name="owner_branding_density"),
        nullable=False,
        default="comfortable",
    )
    style: Mapped[str] = mapped_column(
        Enum("soft", "vivid", "executive", name="owner_branding_style"),
        nullable=False,
        default="soft",
    )
    navigation_layout: Mapped[str] = mapped_column(
        Enum("sidebar", "navbar", name="owner_navigation_layout"),
        nullable=False,
        default="sidebar",
    )
    dashboard_panels: Mapped[str | None] = mapped_column(Text)
