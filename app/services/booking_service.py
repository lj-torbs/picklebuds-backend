import secrets
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingPayment, BookingRental, BookingSlot
from app.models.transaction import Transaction
from app.models.user import Player
from app.models.venue import Court, CourtAvailableSlot, RentalItem, Venue, VenuePaymentMethod
from app.schemas.booking import (
    BookingActionResponse,
    BookingCreateRequest,
    BookingListItemResponse,
    BookingListResponse,
    BookingRentalSnapshotResponse,
    BookingResponse,
    OwnerBookingReviewItemResponse,
    OwnerBookingReviewListResponse,
)
from app.schemas.common import CurrentUser


@dataclass
class BookingFailure(Exception):
    message: str
    status_code: int = 400


def _generate_booking_public_id(db: Session) -> str:
    for _ in range(10):
        public_id = f"PB-{secrets.token_hex(4).upper()}"
        exists = db.scalar(select(Booking.id).where(Booking.public_id == public_id))
        if exists is None:
            return public_id
    raise BookingFailure("Unable to generate a unique booking ID.", 500)


def _sorted_unique_slots(slot_labels: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for slot in slot_labels:
        cleaned = slot.strip()
        if cleaned and cleaned not in seen:
            normalized.append(cleaned)
            seen.add(cleaned)
    return normalized


def _build_rental_snapshot_map(db: Session, booking_ids: list[int]) -> dict[int, list[BookingRentalSnapshotResponse]]:
    if not booking_ids:
        return {}

    rental_rows = db.scalars(
        select(BookingRental)
        .where(BookingRental.booking_id.in_(booking_ids))
        .order_by(BookingRental.booking_id.asc(), BookingRental.id.asc())
    ).all()
    rental_item_ids = sorted({rental.rental_item_id for rental in rental_rows})
    rental_public_ids = (
        {
            item.id: item.public_id
            for item in db.scalars(select(RentalItem).where(RentalItem.id.in_(rental_item_ids))).all()
        }
        if rental_item_ids
        else {}
    )

    rental_map: dict[int, list[BookingRentalSnapshotResponse]] = {booking_id: [] for booking_id in booking_ids}
    for rental in rental_rows:
        rental_map.setdefault(rental.booking_id, []).append(
            BookingRentalSnapshotResponse(
                rental_item_public_id=rental_public_ids.get(
                    rental.rental_item_id,
                    f"rental-{rental.rental_item_id}",
                ),
                item_name=rental.item_name_snapshot,
                category=rental.category_snapshot,
                price_per_session=float(rental.price_per_session_snapshot),
                quantity=rental.quantity,
            )
        )
    return rental_map


def _build_slot_map(db: Session, booking_ids: list[int]) -> dict[int, list[str]]:
    slot_map: dict[int, list[str]] = {booking_id: [] for booking_id in booking_ids}
    if not booking_ids:
        return slot_map

    for slot in db.scalars(
        select(BookingSlot)
        .where(BookingSlot.booking_id.in_(booking_ids))
        .order_by(BookingSlot.booking_id.asc(), BookingSlot.sort_order.asc(), BookingSlot.id.asc())
    ).all():
        slot_map.setdefault(slot.booking_id, []).append(slot.slot_label)
    return slot_map


def list_player_bookings(db: Session, current_user: CurrentUser) -> BookingListResponse:
    bookings = db.scalars(
        select(Booking)
        .where(Booking.player_id == current_user.id)
        .order_by(Booking.booking_date.desc(), Booking.id.desc())
    ).all()

    if not bookings:
        return BookingListResponse(items=[])

    booking_ids = [booking.id for booking in bookings]
    venue_ids = sorted({booking.venue_id for booking in bookings})
    court_ids = sorted({booking.court_id for booking in bookings if booking.court_id is not None})

    venues = {
        venue.id: venue
        for venue in db.scalars(select(Venue).where(Venue.id.in_(venue_ids))).all()
    }
    courts = (
        {
            court.id: court
            for court in db.scalars(select(Court).where(Court.id.in_(court_ids))).all()
        }
        if court_ids
        else {}
    )
    slot_map = _build_slot_map(db, booking_ids)
    rental_map = _build_rental_snapshot_map(db, booking_ids)

    items: list[BookingListItemResponse] = []
    for booking in bookings:
        venue = venues.get(booking.venue_id)
        court = courts.get(booking.court_id) if booking.court_id is not None else None
        items.append(
            BookingListItemResponse(
                public_id=booking.public_id,
                venue_public_id=venue.public_id if venue else "",
                court_public_id=court.public_id if court else None,
                booking_type=booking.booking_type,
                booking_date=booking.booking_date,
                slot_labels=slot_map.get(booking.id, []),
                participant_count=booking.participant_count,
                status=booking.status,
                payment_status=booking.payment_status,
                total_amount=round(float(booking.total_amount), 2),
                venue_name=venue.name if venue else "Unknown venue",
                venue_address=venue.address if venue else "",
                court_name=court.name if court else None,
                booked_by_name=booking.booked_by_name_snapshot,
                booked_by_email=booking.booked_by_email_snapshot,
                rentals=rental_map.get(booking.id, []),
            )
        )

    return BookingListResponse(items=items)


def list_owner_booking_reviews(db: Session, current_user: CurrentUser) -> OwnerBookingReviewListResponse:
    bookings = db.scalars(
        select(Booking)
        .join(Venue, Venue.id == Booking.venue_id)
        .where(Venue.owner_id == current_user.id)
        .order_by(Booking.created_at.desc(), Booking.id.desc())
    ).all()

    if not bookings:
        return OwnerBookingReviewListResponse(items=[])

    booking_ids = [booking.id for booking in bookings]
    venue_ids = sorted({booking.venue_id for booking in bookings})
    court_ids = sorted({booking.court_id for booking in bookings if booking.court_id is not None})

    venues = {
        venue.id: venue
        for venue in db.scalars(select(Venue).where(Venue.id.in_(venue_ids))).all()
    }
    courts = (
        {
            court.id: court
            for court in db.scalars(select(Court).where(Court.id.in_(court_ids))).all()
        }
        if court_ids
        else {}
    )
    slot_map = _build_slot_map(db, booking_ids)
    rental_map = _build_rental_snapshot_map(db, booking_ids)
    payment_map = {
        payment.booking_id: payment
        for payment in db.scalars(
            select(BookingPayment).where(BookingPayment.booking_id.in_(booking_ids))
        ).all()
    }

    items: list[OwnerBookingReviewItemResponse] = []
    for booking in bookings:
        venue = venues.get(booking.venue_id)
        court = courts.get(booking.court_id) if booking.court_id is not None else None
        payment = payment_map.get(booking.id)
        items.append(
            OwnerBookingReviewItemResponse(
                public_id=booking.public_id,
                venue_public_id=venue.public_id if venue else "",
                venue_name=venue.name if venue else "Unknown venue",
                court_public_id=court.public_id if court else None,
                court_name=court.name if court else None,
                booking_type=booking.booking_type,
                booking_date=booking.booking_date,
                slot_labels=slot_map.get(booking.id, []),
                participant_count=booking.participant_count,
                amount=round(float(booking.total_amount), 2),
                status=booking.status,
                payment_status=booking.payment_status,
                payment_review_status=payment.review_status if payment else "pending",
                payment_method_label=payment.payment_method_label if payment else None,
                reference_number=payment.reference_number if payment else None,
                sender_account_name=payment.sender_account_name if payment else None,
                receipt_file_name=payment.receipt_file_name if payment else None,
                receipt_image_url=payment.receipt_image_url if payment else None,
                receipt_uploaded_at=payment.receipt_uploaded_at if payment else None,
                customer_name=booking.booked_by_name_snapshot,
                customer_email=booking.booked_by_email_snapshot,
                created_at=booking.created_at,
                rentals=rental_map.get(booking.id, []),
            )
        )

    return OwnerBookingReviewListResponse(items=items)


def approve_booking_payment(
    db: Session,
    current_user: CurrentUser,
    booking_public_id: str,
) -> BookingActionResponse:
    booking = db.scalar(
        select(Booking)
        .join(Venue, Venue.id == Booking.venue_id)
        .where(Booking.public_id == booking_public_id, Venue.owner_id == current_user.id)
    )
    if booking is None:
        raise BookingFailure("Booking not found for this owner.", 404)
    if booking.status != "pending":
        raise BookingFailure("Only pending bookings can be approved.", 400)

    payment = db.scalar(select(BookingPayment).where(BookingPayment.booking_id == booking.id))
    if payment is None:
        raise BookingFailure("No payment record found for this booking.", 404)
    if not payment.receipt_image_url or not payment.reference_number:
        raise BookingFailure("Payment proof is incomplete for this booking.", 400)

    now = datetime.utcnow()
    payment.review_status = "approved"
    payment.payment_status = "paid"
    payment.approved_by_owner_id = current_user.id
    payment.approved_at = now

    booking.status = "confirmed"
    booking.payment_status = "paid"
    booking.updated_at = now

    transaction = db.scalar(select(Transaction).where(Transaction.booking_id == booking.id))
    if transaction is not None:
        transaction.status = "confirmed"
        transaction.payment_status = "paid"

    db.commit()

    return BookingActionResponse(
        public_id=booking.public_id,
        status=booking.status,
        payment_status=booking.payment_status,
        payment_review_status=payment.review_status,
    )


def complete_owner_booking(
    db: Session,
    current_user: CurrentUser,
    booking_public_id: str,
) -> BookingActionResponse:
    booking = db.scalar(
        select(Booking)
        .join(Venue, Venue.id == Booking.venue_id)
        .where(Booking.public_id == booking_public_id, Venue.owner_id == current_user.id)
    )
    if booking is None:
        raise BookingFailure("Booking not found for this owner.", 404)
    if booking.status != "confirmed":
        raise BookingFailure("Only confirmed bookings can be marked completed.", 400)

    booking.status = "completed"
    booking.updated_at = datetime.utcnow()

    payment = db.scalar(select(BookingPayment).where(BookingPayment.booking_id == booking.id))
    transaction = db.scalar(select(Transaction).where(Transaction.booking_id == booking.id))
    if transaction is not None:
        transaction.status = "completed"

    db.commit()

    return BookingActionResponse(
        public_id=booking.public_id,
        status=booking.status,
        payment_status=booking.payment_status,
        payment_review_status=payment.review_status if payment else None,
    )


def create_private_booking(
    db: Session,
    current_user: CurrentUser,
    payload: BookingCreateRequest,
) -> BookingResponse:
    if payload.booking_type != "private":
        raise BookingFailure(
            "Only private court booking is implemented on the live backend right now.",
            400,
        )

    if payload.booking_date < date.today():
        raise BookingFailure("Booking date cannot be in the past.", 400)

    if payload.participant_count != 1:
        raise BookingFailure("Private court booking currently expects one booking record.", 400)

    slot_labels = _sorted_unique_slots(payload.slot_labels)
    if not slot_labels:
        raise BookingFailure("Select at least one time slot.", 400)

    venue = db.scalar(select(Venue).where(Venue.public_id == payload.venue_public_id))
    if venue is None:
        raise BookingFailure("Venue not found.", 404)
    if venue.status != "active":
        raise BookingFailure("This venue is not accepting bookings right now.", 400)

    if not payload.court_public_id:
        raise BookingFailure("A court is required for private booking.", 400)

    court = db.scalar(
        select(Court).where(
            Court.public_id == payload.court_public_id,
            Court.venue_id == venue.id,
        )
    )
    if court is None:
        raise BookingFailure("Court not found for this venue.", 404)
    if court.status != "available":
        raise BookingFailure("This court is not available for booking.", 400)
    if court.booking_mode != "private":
        raise BookingFailure("This court is not configured for private booking.", 400)

    available_slots = db.scalars(
        select(CourtAvailableSlot.slot_label).where(CourtAvailableSlot.court_id == court.id)
    ).all()
    available_slot_set = set(available_slots)
    invalid_slots = [slot for slot in slot_labels if slot not in available_slot_set]
    if invalid_slots:
        raise BookingFailure(
            f"Some selected slots are no longer available: {', '.join(invalid_slots)}.",
            400,
        )

    payment_method = db.scalar(
        select(VenuePaymentMethod).where(
            VenuePaymentMethod.venue_id == venue.id,
            VenuePaymentMethod.is_active.is_(True),
            (
                VenuePaymentMethod.id == payload.payment.venue_payment_method_id
                if payload.payment.venue_payment_method_id is not None
                else (
                    (VenuePaymentMethod.provider == payload.payment.provider)
                    & (VenuePaymentMethod.account_number == payload.payment.account_number)
                )
            ),
        )
    )
    if payment_method is None:
        raise BookingFailure("Selected payment method is not available.", 400)

    rental_items: list[tuple[RentalItem, int]] = []
    rental_amount = 0.0
    for rental in payload.rentals:
        item = db.scalar(
            select(RentalItem).where(
                RentalItem.public_id == rental.rental_item_public_id,
                RentalItem.venue_id == venue.id,
            )
        )
        if item is None or item.status != "available":
            raise BookingFailure(f"Rental item {rental.rental_item_public_id} is not available.", 400)

        existing_qty = (
            db.scalar(
                select(func.coalesce(func.sum(BookingRental.quantity), 0))
                .join(Booking, Booking.id == BookingRental.booking_id)
                .where(
                    BookingRental.rental_item_id == item.id,
                    Booking.booking_date == payload.booking_date,
                    Booking.status != "cancelled",
                )
            )
            or 0
        )
        if existing_qty + rental.quantity > item.quantity_available:
            raise BookingFailure(
                f"Only {max(0, item.quantity_available - existing_qty)} {item.name} left for {payload.booking_date}.",
                400,
            )

        rental_items.append((item, rental.quantity))
        rental_amount += float(item.price_per_session) * rental.quantity

    conflicting_slots = db.scalars(
        select(BookingSlot.slot_label)
        .join(Booking, Booking.id == BookingSlot.booking_id)
        .where(
            Booking.venue_id == venue.id,
            Booking.booking_date == payload.booking_date,
            Booking.status != "cancelled",
            BookingSlot.slot_label.in_(slot_labels),
            (
                ((Booking.booking_type == "private") & (Booking.court_id == court.id))
                | (Booking.booking_type == "whole_gym")
            ),
        )
    ).all()
    if conflicting_slots:
        taken = ", ".join(sorted(set(conflicting_slots)))
        raise BookingFailure(f"These slots have already been taken: {taken}.", 409)

    player = db.scalar(select(Player).where(Player.id == current_user.id))
    if player is None:
        raise BookingFailure("Player account not found.", 404)

    base_amount = float(court.price_per_hour) * len(slot_labels)
    total_amount = base_amount + rental_amount
    if round(total_amount, 2) != round(payload.total_amount, 2):
        raise BookingFailure(
            f"Booking price changed. Expected {total_amount:.2f}, received {payload.total_amount:.2f}.",
            409,
        )

    public_id = _generate_booking_public_id(db)
    created_at = datetime.utcnow()
    booking = Booking(
        public_id=public_id,
        player_id=player.id,
        original_player_id=player.id,
        venue_id=venue.id,
        court_id=court.id,
        booking_type="private",
        booking_date=payload.booking_date,
        participant_count=1,
        status="pending",
        payment_status="paid",
        booked_by_name_snapshot=player.full_name,
        booked_by_email_snapshot=player.email,
        owner_name_snapshot=player.full_name,
        owner_email_snapshot=player.email,
        base_amount=base_amount,
        rental_amount=rental_amount,
        total_amount=total_amount,
        created_at=created_at,
        updated_at=created_at,
    )
    db.add(booking)
    db.flush()

    for index, slot_label in enumerate(slot_labels, start=1):
        db.add(
            BookingSlot(
                booking_id=booking.id,
                slot_label=slot_label,
                sort_order=index,
            )
        )

    for item, quantity in rental_items:
        db.add(
            BookingRental(
                booking_id=booking.id,
                rental_item_id=item.id,
                item_name_snapshot=item.name,
                category_snapshot=item.category,
                price_per_session_snapshot=item.price_per_session,
                quantity=quantity,
            )
        )

    payment_label = f"{payment_method.provider} - {payment_method.account_number}"
    db.add(
        BookingPayment(
            booking_id=booking.id,
            venue_payment_method_id=payment_method.id,
            amount=total_amount,
            payment_method_label=payment_label,
            review_status="pending",
            payment_status="paid",
            reference_number=payload.payment.reference_number.strip(),
            sender_account_name=payload.payment.sender_account_name.strip(),
            receipt_file_name=payload.payment.receipt_file_name.strip(),
            receipt_image_url=payload.payment.receipt_image_url,
            receipt_uploaded_at=created_at,
        )
    )

    db.add(
        Transaction(
            public_id=public_id,
            booking_id=booking.id,
            player_id=player.id,
            venue_id=venue.id,
            court_id=court.id,
            booking_type="private",
            amount=total_amount,
            payment_method_label=payment_label,
            payment_status="paid",
            status="pending",
            created_at=created_at,
        )
    )

    db.commit()

    return BookingResponse(
        public_id=public_id,
        venue_public_id=venue.public_id,
        court_public_id=court.public_id,
        booking_type="private",
        booking_date=payload.booking_date,
        slot_labels=slot_labels,
        participant_count=1,
        status="pending",
        payment_status="paid",
        total_amount=round(total_amount, 2),
    )
