from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingSlot
from app.models.user import Owner
from app.models.venue import (
    Court,
    CourtAvailableSlot,
    RentalItem,
    Venue,
    VenueAvailableSlot,
    VenueBookingSettings,
    VenuePaymentMethod,
)
from app.schemas.venue import (
    VenueAvailabilityItemResponse,
    VenueAvailabilityResponse,
    VenueCourtAvailabilityResponse,
    VenueCourtResponse,
    VenueDetailResponse,
    VenueListItemResponse,
    VenueListResponse,
    VenuePaymentMethodResponse,
    VenueRentalItemResponse,
    VenueWholeGymAvailabilityResponse,
    VenueWholeGymBookingResponse,
)


class VenueNotFound(Exception):
    pass


def _build_court_slots_map(db: Session, court_ids: list[int]) -> dict[int, list[str]]:
    slots_map: dict[int, list[str]] = {court_id: [] for court_id in court_ids}
    if not court_ids:
        return slots_map

    for row in db.scalars(
        select(CourtAvailableSlot)
        .where(CourtAvailableSlot.court_id.in_(court_ids))
        .order_by(
            CourtAvailableSlot.court_id.asc(),
            CourtAvailableSlot.sort_order.asc(),
            CourtAvailableSlot.id.asc(),
        )
    ).all():
        slots_map.setdefault(row.court_id, []).append(row.slot_label)

    return slots_map


def _build_venue_slots(db: Session, venue_id: int) -> list[str]:
    return db.scalars(
        select(VenueAvailableSlot.slot_label)
        .where(VenueAvailableSlot.venue_id == venue_id)
        .order_by(VenueAvailableSlot.sort_order.asc(), VenueAvailableSlot.id.asc())
    ).all()


def list_venues(db: Session) -> VenueListResponse:
    venues = db.scalars(select(Venue).order_by(Venue.name.asc())).all()
    if not venues:
        return VenueListResponse(items=[])

    venue_ids = [venue.id for venue in venues]
    settings_map = {
        row.venue_id: row
        for row in db.scalars(
            select(VenueBookingSettings).where(VenueBookingSettings.venue_id.in_(venue_ids))
        ).all()
    }
    courts = db.scalars(select(Court).where(Court.venue_id.in_(venue_ids))).all()
    court_counts: dict[int, int] = {venue_id: 0 for venue_id in venue_ids}
    has_open_play: dict[int, bool] = {venue_id: False for venue_id in venue_ids}

    for court in courts:
        court_counts[court.venue_id] = court_counts.get(court.venue_id, 0) + 1
        if court.booking_mode == "open_play":
            has_open_play[court.venue_id] = True

    return VenueListResponse(
        items=[
            VenueListItemResponse(
                public_id=venue.public_id,
                name=venue.name,
                address=venue.address,
                phone=venue.phone,
                status=venue.status,
                image_url=venue.image_url,
                court_count=court_counts.get(venue.id, 0),
                has_open_play=has_open_play.get(venue.id, False),
                whole_gym_enabled=bool(
                    settings_map.get(venue.id) and settings_map[venue.id].whole_gym_enabled
                ),
            )
            for venue in venues
        ]
    )


def get_venue_detail(db: Session, venue_public_id: str) -> VenueDetailResponse:
    venue = db.scalar(select(Venue).where(Venue.public_id == venue_public_id))
    if venue is None:
        raise VenueNotFound

    owner = db.scalar(select(Owner).where(Owner.id == venue.owner_id))
    settings = db.scalar(select(VenueBookingSettings).where(VenueBookingSettings.venue_id == venue.id))
    payment_methods = db.scalars(
        select(VenuePaymentMethod)
        .where(VenuePaymentMethod.venue_id == venue.id)
        .order_by(VenuePaymentMethod.id.asc())
    ).all()
    rental_items = db.scalars(
        select(RentalItem)
        .where(RentalItem.venue_id == venue.id)
        .order_by(RentalItem.name.asc())
    ).all()
    courts = db.scalars(
        select(Court).where(Court.venue_id == venue.id).order_by(Court.name.asc())
    ).all()
    court_slots_map = _build_court_slots_map(db, [court.id for court in courts])
    whole_gym_slots = _build_venue_slots(db, venue.id)

    return VenueDetailResponse(
        public_id=venue.public_id,
        owner_public_id=owner.public_id if owner else "",
        name=venue.name,
        address=venue.address,
        phone=venue.phone,
        status=venue.status,
        image_url=venue.image_url,
        payment_methods=[
            VenuePaymentMethodResponse(
                id=method.id,
                provider=method.provider,
                display_name=method.display_name,
                account_name=method.account_name,
                account_number=method.account_number,
                instructions=method.instructions,
                qr_code_image_url=method.qr_code_image_url,
                qr_code_file_name=method.qr_code_file_name,
                is_active=method.is_active,
            )
            for method in payment_methods
        ],
        whole_gym_booking=(
            VenueWholeGymBookingResponse(
                enabled=settings.whole_gym_enabled,
                price_per_hour=(
                    float(settings.whole_gym_price_per_hour)
                    if settings.whole_gym_price_per_hour is not None
                    else None
                ),
                available_slots=whole_gym_slots,
                notes=settings.whole_gym_notes,
            )
            if settings is not None
            else None
        ),
        rental_items=[
            VenueRentalItemResponse(
                public_id=item.public_id,
                name=item.name,
                category=item.category,
                price_per_session=float(item.price_per_session),
                quantity_available=item.quantity_available,
                status=item.status,
                description=item.description,
            )
            for item in rental_items
        ],
        courts=[
            VenueCourtResponse(
                public_id=court.public_id,
                name=court.name,
                surface=court.surface,
                capacity_label=court.capacity_label,
                price_per_hour=float(court.price_per_hour),
                status=court.status,
                booking_mode=court.booking_mode,
                open_play_capacity=court.open_play_capacity,
                available_slots=court_slots_map.get(court.id, []),
                image_url=court.image_url,
            )
            for court in courts
        ],
    )


def list_venue_availability(
    db: Session,
    venue_public_id: str,
    date_from: date | None = None,
    days: int = 7,
) -> VenueAvailabilityResponse:
    venue = db.scalar(select(Venue).where(Venue.public_id == venue_public_id))
    if venue is None:
        raise VenueNotFound

    start_date = date_from or date.today()
    if days < 1:
        days = 1
    if days > 31:
        days = 31
    end_date = start_date + timedelta(days=days - 1)

    courts = db.scalars(
        select(Court).where(Court.venue_id == venue.id).order_by(Court.name.asc())
    ).all()
    court_ids = [court.id for court in courts]
    court_slots_map = _build_court_slots_map(db, court_ids)
    whole_gym_slots = _build_venue_slots(db, venue.id)

    bookings = db.scalars(
        select(Booking)
        .where(
            Booking.venue_id == venue.id,
            Booking.booking_date >= start_date,
            Booking.booking_date <= end_date,
            Booking.status != "cancelled",
        )
        .order_by(Booking.booking_date.asc(), Booking.id.asc())
    ).all()
    booking_ids = [booking.id for booking in bookings]
    slot_rows = db.scalars(
        select(BookingSlot).where(BookingSlot.booking_id.in_(booking_ids))
    ).all() if booking_ids else []
    booking_slots_map: dict[int, list[str]] = {booking.id: [] for booking in bookings}
    for row in slot_rows:
        booking_slots_map.setdefault(row.booking_id, []).append(row.slot_label)

    whole_gym_booked: dict[tuple[str, str], Booking] = {}
    private_booked: dict[tuple[int, str, str], Booking] = {}
    open_play_seats: dict[tuple[int, str, str], int] = {}
    open_play_booking_ref: dict[tuple[int, str, str], str] = {}

    for booking in bookings:
        booking_date = booking.booking_date.isoformat()
        for slot_label in booking_slots_map.get(booking.id, []):
            if booking.booking_type == "whole_gym":
                whole_gym_booked[(booking_date, slot_label)] = booking
            elif booking.booking_type == "private" and booking.court_id is not None:
                private_booked[(booking.court_id, booking_date, slot_label)] = booking
            elif booking.booking_type == "open_play" and booking.court_id is not None:
                key = (booking.court_id, booking_date, slot_label)
                open_play_seats[key] = open_play_seats.get(key, 0) + booking.participant_count
                open_play_booking_ref.setdefault(key, booking.public_id)

    court_items: list[VenueCourtAvailabilityResponse] = []
    for court in courts:
        items: list[VenueAvailabilityItemResponse] = []
        available_slots = set(court_slots_map.get(court.id, []))
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            current_date_text = current_date.isoformat()
            for slot_label in court_slots_map.get(court.id, []):
                blocked_by_whole_gym = whole_gym_booked.get((current_date_text, slot_label))
                if court.status != "available" or slot_label not in available_slots:
                    items.append(
                        VenueAvailabilityItemResponse(
                            date=current_date,
                            slot_label=slot_label,
                            state="closed",
                        )
                    )
                    continue

                if blocked_by_whole_gym is not None:
                    items.append(
                        VenueAvailabilityItemResponse(
                            date=current_date,
                            slot_label=slot_label,
                            state="booked",
                            booking_public_id=blocked_by_whole_gym.public_id,
                            booking_type="whole_gym",
                        )
                    )
                    continue

                if court.booking_mode == "private":
                    private_booking = private_booked.get((court.id, current_date_text, slot_label))
                    items.append(
                        VenueAvailabilityItemResponse(
                            date=current_date,
                            slot_label=slot_label,
                            state="booked" if private_booking else "available",
                            booking_public_id=private_booking.public_id if private_booking else None,
                            booking_type="private" if private_booking else None,
                        )
                    )
                    continue

                seats_taken = open_play_seats.get((court.id, current_date_text, slot_label), 0)
                seats_capacity = court.open_play_capacity
                items.append(
                    VenueAvailabilityItemResponse(
                        date=current_date,
                        slot_label=slot_label,
                        state=(
                            "booked"
                            if seats_capacity is not None and seats_taken >= seats_capacity
                            else "available"
                        ),
                        booking_public_id=open_play_booking_ref.get((court.id, current_date_text, slot_label)),
                        booking_type="open_play" if seats_taken > 0 else None,
                        seats_taken=seats_taken,
                        seats_capacity=seats_capacity,
                    )
                )

        court_items.append(
            VenueCourtAvailabilityResponse(
                court_public_id=court.public_id,
                court_name=court.name,
                booking_mode=court.booking_mode,
                items=items,
            )
        )

    whole_gym_items: list[VenueAvailabilityItemResponse] = []
    if whole_gym_slots:
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            current_date_text = current_date.isoformat()
            for slot_label in whole_gym_slots:
                booking = whole_gym_booked.get((current_date_text, slot_label))
                whole_gym_items.append(
                    VenueAvailabilityItemResponse(
                        date=current_date,
                        slot_label=slot_label,
                        state="booked" if booking else "available",
                        booking_public_id=booking.public_id if booking else None,
                        booking_type="whole_gym" if booking else None,
                    )
                )

    return VenueAvailabilityResponse(
        venue_public_id=venue.public_id,
        date_from=start_date,
        days=days,
        courts=court_items,
        whole_gym=VenueWholeGymAvailabilityResponse(items=whole_gym_items)
        if whole_gym_slots
        else None,
    )
