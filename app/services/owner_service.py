import secrets

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.transaction import Transaction
from app.models.venue import (
    Court,
    CourtAvailableSlot,
    RentalItem,
    Venue,
    VenueAvailableSlot,
    VenueBookingSettings,
    VenuePaymentMethod,
)
from app.schemas.common import CurrentUser
from app.schemas.owner_manage import (
    OwnerCourtUpsertRequest,
    OwnerStatusUpdateRequest,
    OwnerVenueUpsertRequest,
)
from app.schemas.owner import (
    OwnerDashboardResponse,
    OwnerDashboardStatsResponse,
    OwnerTransactionsResponse,
    OwnerVenueListResponse,
)
from app.services.booking_service import list_owner_booking_reviews
from app.services.venue_service import get_venue_detail
from app.schemas.venue import VenueDetailResponse


class OwnerManageFailure(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def list_owner_transactions(db: Session, current_user: CurrentUser) -> OwnerTransactionsResponse:
    reviews = list_owner_booking_reviews(db, current_user)
    return OwnerTransactionsResponse(items=reviews.items)


def get_owner_dashboard(db: Session, current_user: CurrentUser) -> OwnerDashboardResponse:
    venue_ids = db.scalars(
        select(Venue.id).where(Venue.owner_id == current_user.id)
    ).all()

    venue_count = len(venue_ids)
    court_count = (
        db.scalar(select(func.count(Court.id)).where(Court.venue_id.in_(venue_ids)))
        if venue_ids
        else 0
    ) or 0

    booking_rows = db.execute(
        select(
            Transaction.payment_status,
            Transaction.status,
            Transaction.amount,
        )
        .join(Booking, Booking.id == Transaction.booking_id)
        .where(Booking.venue_id.in_(venue_ids) if venue_ids else False)
    ).all()

    total_revenue = 0.0
    pending_count = 0
    completed_count = 0
    cancelled_count = 0

    for payment_status, status, amount in booking_rows:
        if payment_status == "paid":
            total_revenue += float(amount or 0)
        if status == "pending":
            pending_count += 1
        elif status == "completed":
            completed_count += 1
        elif status == "cancelled":
            cancelled_count += 1

    recent_transactions = list_owner_booking_reviews(db, current_user).items[:5]

    return OwnerDashboardResponse(
        stats=OwnerDashboardStatsResponse(
            total_revenue=round(total_revenue, 2),
            pending_count=pending_count,
            completed_count=completed_count,
            cancelled_count=cancelled_count,
            venue_count=venue_count,
            court_count=int(court_count),
        ),
        recent_transactions=recent_transactions,
    )


def list_owner_venues(db: Session, current_user: CurrentUser) -> OwnerVenueListResponse:
    venue_public_ids = db.scalars(
        select(Venue.public_id)
        .where(Venue.owner_id == current_user.id)
        .order_by(Venue.created_at.asc(), Venue.id.asc())
    ).all()

    return OwnerVenueListResponse(
        items=[get_venue_detail(db, venue_public_id) for venue_public_id in venue_public_ids]
    )


def _slugify(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    collapsed = "-".join(part for part in normalized.split("-") if part)
    return collapsed or "venue"


def _generate_public_id(db: Session, model: type[Venue] | type[Court] | type[RentalItem], prefix: str) -> str:
    for _ in range(10):
        public_id = f"{prefix}-{secrets.token_hex(4)}"
        exists = db.scalar(select(model.id).where(model.public_id == public_id))
        if exists is None:
            return public_id
    raise OwnerManageFailure("Unable to generate a unique identifier.", 500)


def _normalize_slots(slot_labels: list[str]) -> list[str]:
    slots: list[str] = []
    seen: set[str] = set()
    for slot in slot_labels:
        cleaned = slot.strip()
        if cleaned and cleaned not in seen:
            slots.append(cleaned)
            seen.add(cleaned)
    return slots


def _get_owner_venue_or_fail(db: Session, current_user: CurrentUser, venue_public_id: str) -> Venue:
    venue = db.scalar(
        select(Venue).where(
            Venue.public_id == venue_public_id,
            Venue.owner_id == current_user.id,
        )
    )
    if venue is None:
        raise OwnerManageFailure("Venue not found for this owner.", 404)
    return venue


def _get_owner_court_or_fail(
    db: Session,
    current_user: CurrentUser,
    venue_public_id: str,
    court_public_id: str,
) -> tuple[Venue, Court]:
    venue = _get_owner_venue_or_fail(db, current_user, venue_public_id)
    court = db.scalar(
        select(Court).where(
            Court.public_id == court_public_id,
            Court.venue_id == venue.id,
        )
    )
    if court is None:
        raise OwnerManageFailure("Court not found for this venue.", 404)
    return venue, court


def _replace_venue_payment_methods(
    db: Session,
    venue: Venue,
    payload: OwnerVenueUpsertRequest,
) -> None:
    existing_methods = db.scalars(
        select(VenuePaymentMethod).where(VenuePaymentMethod.venue_id == venue.id)
    ).all()
    existing_map = {
        (method.provider, method.account_number): method for method in existing_methods
    }
    payload_keys = {
        (method.provider, method.account_number.strip()) for method in payload.payment_methods
    }

    for method in existing_methods:
        if (method.provider, method.account_number) not in payload_keys:
            method.is_active = False

    for method in payload.payment_methods:
        account_number = method.account_number.strip()
        display_name = f"{method.provider} - {method.account_name.strip()}"
        record = existing_map.get((method.provider, account_number))
        if record is None:
            db.add(
                VenuePaymentMethod(
                    venue_id=venue.id,
                    provider=method.provider,
                    display_name=display_name,
                    account_name=method.account_name.strip(),
                    account_number=account_number,
                    instructions=method.instructions.strip() if method.instructions else None,
                    qr_code_image_url=method.qr_code_image_url,
                    qr_code_file_name=method.qr_code_file_name,
                    is_active=method.is_active,
                )
            )
            continue

        record.display_name = display_name
        record.account_name = method.account_name.strip()
        record.instructions = method.instructions.strip() if method.instructions else None
        record.qr_code_image_url = method.qr_code_image_url
        record.qr_code_file_name = method.qr_code_file_name
        record.is_active = method.is_active


def _replace_venue_rental_items(
    db: Session,
    venue: Venue,
    payload: OwnerVenueUpsertRequest,
) -> None:
    existing_items = {
        item.public_id: item
        for item in db.scalars(select(RentalItem).where(RentalItem.venue_id == venue.id)).all()
    }
    payload_ids = {item.public_id for item in payload.rental_items if item.public_id}

    for public_id, item in existing_items.items():
        if public_id not in payload_ids:
            item.status = "unavailable"

    for item in payload.rental_items:
        record = existing_items.get(item.public_id) if item.public_id else None
        if record is None:
            record = RentalItem(
                public_id=_generate_public_id(db, RentalItem, f"{_slugify(venue.name)}-gear"),
                venue_id=venue.id,
                name=item.name.strip(),
                category=item.category,
                price_per_session=item.price_per_session,
                quantity_available=item.quantity_available,
                status=item.status,
                description=item.description.strip() if item.description else None,
            )
            db.add(record)
            continue

        record.name = item.name.strip()
        record.category = item.category
        record.price_per_session = item.price_per_session
        record.quantity_available = item.quantity_available
        record.status = item.status
        record.description = item.description.strip() if item.description else None


def _replace_venue_whole_gym_settings(
    db: Session,
    venue: Venue,
    payload: OwnerVenueUpsertRequest,
) -> None:
    settings = db.scalar(
        select(VenueBookingSettings).where(VenueBookingSettings.venue_id == venue.id)
    )
    if settings is None:
        settings = VenueBookingSettings(venue_id=venue.id)
        db.add(settings)
        db.flush()

    whole_gym = payload.whole_gym_booking
    settings.whole_gym_enabled = bool(whole_gym and whole_gym.enabled)
    settings.whole_gym_price_per_hour = (
        whole_gym.price_per_hour if whole_gym and whole_gym.enabled else None
    )
    settings.whole_gym_notes = (
        whole_gym.notes.strip() if whole_gym and whole_gym.notes else None
    )

    db.execute(delete(VenueAvailableSlot).where(VenueAvailableSlot.venue_id == venue.id))
    if whole_gym and whole_gym.enabled:
        for index, slot_label in enumerate(_normalize_slots(whole_gym.available_slots), start=1):
            db.add(
                VenueAvailableSlot(
                    venue_id=venue.id,
                    slot_label=slot_label,
                    sort_order=index,
                )
            )


def create_owner_venue(
    db: Session,
    current_user: CurrentUser,
    payload: OwnerVenueUpsertRequest,
) -> VenueDetailResponse:
    venue = Venue(
        public_id=_generate_public_id(db, Venue, _slugify(payload.name)),
        owner_id=current_user.id,
        name=payload.name.strip(),
        address=payload.address.strip(),
        phone=payload.phone.strip() if payload.phone else None,
        status=payload.status,
        image_url=payload.image_url,
    )
    db.add(venue)
    db.flush()
    _replace_venue_payment_methods(db, venue, payload)
    _replace_venue_rental_items(db, venue, payload)
    _replace_venue_whole_gym_settings(db, venue, payload)
    db.commit()
    return get_venue_detail(db, venue.public_id)


def update_owner_venue(
    db: Session,
    current_user: CurrentUser,
    venue_public_id: str,
    payload: OwnerVenueUpsertRequest,
) -> VenueDetailResponse:
    venue = _get_owner_venue_or_fail(db, current_user, venue_public_id)
    venue.name = payload.name.strip()
    venue.address = payload.address.strip()
    venue.phone = payload.phone.strip() if payload.phone else None
    venue.status = payload.status
    venue.image_url = payload.image_url
    _replace_venue_payment_methods(db, venue, payload)
    _replace_venue_rental_items(db, venue, payload)
    _replace_venue_whole_gym_settings(db, venue, payload)
    db.commit()
    return get_venue_detail(db, venue.public_id)


def set_owner_venue_status(
    db: Session,
    current_user: CurrentUser,
    venue_public_id: str,
    payload: OwnerStatusUpdateRequest,
) -> VenueDetailResponse:
    if payload.status not in {"active", "inactive"}:
        raise OwnerManageFailure("Invalid venue status.", 422)
    venue = _get_owner_venue_or_fail(db, current_user, venue_public_id)
    venue.status = payload.status
    db.commit()
    return get_venue_detail(db, venue.public_id)


def create_owner_court(
    db: Session,
    current_user: CurrentUser,
    venue_public_id: str,
    payload: OwnerCourtUpsertRequest,
) -> VenueDetailResponse:
    if payload.booking_mode not in {"private", "open_play"}:
        raise OwnerManageFailure("Invalid court booking mode.", 422)
    venue = _get_owner_venue_or_fail(db, current_user, venue_public_id)
    court = Court(
        public_id=_generate_public_id(db, Court, f"{venue.public_id}-court"),
        venue_id=venue.id,
        name=payload.name.strip(),
        surface=payload.surface.strip(),
        capacity_label=payload.capacity_label.strip(),
        price_per_hour=payload.price_per_hour,
        status=payload.status,
        booking_mode=payload.booking_mode,
        open_play_capacity=payload.open_play_capacity if payload.booking_mode == "open_play" else None,
        image_url=payload.image_url,
    )
    db.add(court)
    db.flush()
    for index, slot_label in enumerate(_normalize_slots(payload.available_slots), start=1):
        db.add(
            CourtAvailableSlot(
                court_id=court.id,
                slot_label=slot_label,
                sort_order=index,
            )
        )
    db.commit()
    return get_venue_detail(db, venue.public_id)


def update_owner_court(
    db: Session,
    current_user: CurrentUser,
    venue_public_id: str,
    court_public_id: str,
    payload: OwnerCourtUpsertRequest,
) -> VenueDetailResponse:
    if payload.booking_mode not in {"private", "open_play"}:
        raise OwnerManageFailure("Invalid court booking mode.", 422)
    venue, court = _get_owner_court_or_fail(db, current_user, venue_public_id, court_public_id)
    court.name = payload.name.strip()
    court.surface = payload.surface.strip()
    court.capacity_label = payload.capacity_label.strip()
    court.price_per_hour = payload.price_per_hour
    court.status = payload.status
    court.booking_mode = payload.booking_mode
    court.open_play_capacity = (
        payload.open_play_capacity if payload.booking_mode == "open_play" else None
    )
    court.image_url = payload.image_url
    db.execute(delete(CourtAvailableSlot).where(CourtAvailableSlot.court_id == court.id))
    for index, slot_label in enumerate(_normalize_slots(payload.available_slots), start=1):
        db.add(
            CourtAvailableSlot(
                court_id=court.id,
                slot_label=slot_label,
                sort_order=index,
            )
        )
    db.commit()
    return get_venue_detail(db, venue.public_id)


def set_owner_court_status(
    db: Session,
    current_user: CurrentUser,
    venue_public_id: str,
    court_public_id: str,
    payload: OwnerStatusUpdateRequest,
) -> VenueDetailResponse:
    if payload.status not in {"available", "maintenance"}:
        raise OwnerManageFailure("Invalid court status.", 422)
    venue, court = _get_owner_court_or_fail(db, current_user, venue_public_id, court_public_id)
    court.status = payload.status
    db.commit()
    return get_venue_detail(db, venue.public_id)


def delete_owner_court(
    db: Session,
    current_user: CurrentUser,
    venue_public_id: str,
    court_public_id: str,
) -> VenueDetailResponse:
    venue, court = _get_owner_court_or_fail(db, current_user, venue_public_id, court_public_id)
    existing_booking = db.scalar(select(Booking.id).where(Booking.court_id == court.id))
    if existing_booking is not None:
        raise OwnerManageFailure(
            "This court already has booking history and cannot be deleted. Mark it as maintenance instead.",
            400,
        )
    db.execute(delete(CourtAvailableSlot).where(CourtAvailableSlot.court_id == court.id))
    db.delete(court)
    db.commit()
    return get_venue_detail(db, venue.public_id)
