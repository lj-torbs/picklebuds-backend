from typing import Literal

from pydantic import BaseModel, Field, field_validator


OwnerBrandingDensity = Literal["comfortable", "compact"]
OwnerBrandingStyle = Literal["soft", "vivid", "executive"]
OwnerNavigationLayout = Literal["sidebar", "navbar"]
OwnerDashboardPanel = Literal["recent-transactions"]


class OwnerBrandingPayload(BaseModel):
    brand_name: str = Field(min_length=1, max_length=160)
    logo_image_url: str | None = None
    primary_color: str
    sidebar_color: str
    surface_color: str
    density: OwnerBrandingDensity = "comfortable"
    style: OwnerBrandingStyle = "soft"
    navigation_layout: OwnerNavigationLayout = "sidebar"
    dashboard_panels: list[OwnerDashboardPanel] = Field(
        default_factory=lambda: ["recent-transactions"]
    )

    @field_validator("primary_color", "sidebar_color", "surface_color")
    @classmethod
    def validate_hex_color(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) == 4 and normalized.startswith("#"):
            normalized = "#" + "".join(character * 2 for character in normalized[1:])

        if len(normalized) != 7 or not normalized.startswith("#"):
            raise ValueError("Color must be a valid hex value.")

        try:
            int(normalized[1:], 16)
        except ValueError as exc:
            raise ValueError("Color must be a valid hex value.") from exc

        return normalized

    @field_validator("brand_name")
    @classmethod
    def normalize_brand_name(cls, value: str) -> str:
        return value.strip()


class OwnerBrandingResponse(OwnerBrandingPayload):
    is_customized: bool = False
