import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.owner_branding import OwnerBrandingSettings
from app.models.user import Owner
from app.schemas.common import CurrentUser
from app.schemas.owner_branding import OwnerBrandingPayload, OwnerBrandingResponse


DEFAULT_DASHBOARD_PANELS = ["recent-transactions"]


def _owner_brand_name(owner: Owner | None, current_user: CurrentUser | None = None) -> str:
    if owner is not None:
        return owner.business_name or owner.full_name

    if current_user is not None:
        return current_user.name

    return "Owner"


def _parse_dashboard_panels(value: str | None) -> list[str]:
    if not value:
        return DEFAULT_DASHBOARD_PANELS.copy()

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return DEFAULT_DASHBOARD_PANELS.copy()

    if not isinstance(parsed, list):
        return DEFAULT_DASHBOARD_PANELS.copy()

    panels = [
        panel
        for panel in parsed
        if panel in DEFAULT_DASHBOARD_PANELS
    ]
    return panels or DEFAULT_DASHBOARD_PANELS.copy()


def build_default_owner_branding(
    owner: Owner | None = None,
    current_user: CurrentUser | None = None,
) -> OwnerBrandingResponse:
    return OwnerBrandingResponse(
        brand_name=_owner_brand_name(owner, current_user),
        logo_image_url=None,
        primary_color="#65c466",
        sidebar_color="#0f172a",
        surface_color="#f8fafc",
        density="comfortable",
        style="soft",
        navigation_layout="sidebar",
        dashboard_panels=DEFAULT_DASHBOARD_PANELS.copy(),
        is_customized=False,
    )


def serialize_owner_branding(
    branding: OwnerBrandingSettings | None,
    owner: Owner | None = None,
    current_user: CurrentUser | None = None,
) -> OwnerBrandingResponse:
    if branding is None:
        return build_default_owner_branding(owner, current_user)

    return OwnerBrandingResponse(
        brand_name=branding.brand_name,
        logo_image_url=branding.logo_image_url,
        primary_color=branding.primary_color,
        sidebar_color=branding.sidebar_color,
        surface_color=branding.surface_color,
        density=branding.density,
        style=branding.style,
        navigation_layout=branding.navigation_layout,
        dashboard_panels=_parse_dashboard_panels(branding.dashboard_panels),
        is_customized=True,
    )


def get_owner_branding(
    db: Session,
    current_user: CurrentUser,
) -> OwnerBrandingResponse:
    owner = db.scalar(select(Owner).where(Owner.id == current_user.id))
    branding = db.scalar(
        select(OwnerBrandingSettings).where(
            OwnerBrandingSettings.owner_id == current_user.id
        )
    )
    return serialize_owner_branding(branding, owner, current_user)


def get_public_owner_branding(
    db: Session,
    owner: Owner | None,
) -> OwnerBrandingResponse:
    if owner is None:
        return build_default_owner_branding()

    branding = db.scalar(
        select(OwnerBrandingSettings).where(OwnerBrandingSettings.owner_id == owner.id)
    )
    return serialize_owner_branding(branding, owner)


def update_owner_branding(
    db: Session,
    current_user: CurrentUser,
    payload: OwnerBrandingPayload,
) -> OwnerBrandingResponse:
    branding = db.scalar(
        select(OwnerBrandingSettings).where(
            OwnerBrandingSettings.owner_id == current_user.id
        )
    )

    if branding is None:
        branding = OwnerBrandingSettings(owner_id=current_user.id, brand_name=payload.brand_name)
        db.add(branding)

    branding.brand_name = payload.brand_name
    branding.logo_image_url = payload.logo_image_url
    branding.primary_color = payload.primary_color
    branding.sidebar_color = payload.sidebar_color
    branding.surface_color = payload.surface_color
    branding.density = payload.density
    branding.style = payload.style
    branding.navigation_layout = payload.navigation_layout
    branding.dashboard_panels = json.dumps(payload.dashboard_panels)

    db.commit()
    db.refresh(branding)
    owner = db.scalar(select(Owner).where(Owner.id == current_user.id))
    return serialize_owner_branding(branding, owner, current_user)
