from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.schemas.booking import (
    BookingActionResponse,
    BookingCreateRequest,
    BookingListResponse,
    BookingResponse,
    OwnerBookingReviewListResponse,
)
from app.schemas.common import CurrentUser
from app.services.booking_service import (
    BookingFailure,
    approve_booking_payment,
    complete_owner_booking,
    create_private_booking,
    list_owner_booking_reviews,
    list_player_bookings,
)


router = APIRouter()


@router.get("/me", response_model=BookingListResponse)
def list_my_bookings(
    current_user: CurrentUser = Depends(require_role("player")),
    db: Session = Depends(get_db),
) -> BookingListResponse:
    return list_player_bookings(db, current_user)


@router.get("/owner/reviews", response_model=OwnerBookingReviewListResponse)
def list_owner_reviews(
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> OwnerBookingReviewListResponse:
    return list_owner_booking_reviews(db, current_user)


@router.post("", response_model=BookingResponse)
def create_booking(
    payload: BookingCreateRequest,
    current_user: CurrentUser = Depends(require_role("player")),
    db: Session = Depends(get_db),
) -> BookingResponse:
    try:
        return create_private_booking(db, current_user, payload)
    except BookingFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/{booking_public_id}/payment-proof")
def upload_payment_proof(booking_public_id: str) -> dict[str, str]:
    return {"booking_public_id": booking_public_id, "status": "queued_for_review"}


@router.post("/{booking_public_id}/approve", response_model=BookingActionResponse)
def approve_booking(
    booking_public_id: str,
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> BookingActionResponse:
    try:
        return approve_booking_payment(db, current_user, booking_public_id)
    except BookingFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/{booking_public_id}/complete", response_model=BookingActionResponse)
def complete_booking(
    booking_public_id: str,
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> BookingActionResponse:
    try:
        return complete_owner_booking(db, current_user, booking_public_id)
    except BookingFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/{booking_public_id}/reject")
def reject_booking(booking_public_id: str) -> dict[str, str]:
    return {"booking_public_id": booking_public_id, "status": "rejected"}
