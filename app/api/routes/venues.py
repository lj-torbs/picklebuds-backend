from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.venue import (
    VenueAvailabilityResponse,
    VenueDetailResponse,
    VenueListResponse,
)
from app.services.venue_service import (
    VenueNotFound,
    get_venue_detail,
    list_venue_availability,
    list_venues as list_venues_service,
)


router = APIRouter()


@router.get("", response_model=VenueListResponse)
def list_venues(
    db: Session = Depends(get_db),
) -> VenueListResponse:
    return list_venues_service(db)


@router.get("/{venue_public_id}", response_model=VenueDetailResponse)
def get_venue(
    venue_public_id: str,
    db: Session = Depends(get_db),
) -> VenueDetailResponse:
    try:
        return get_venue_detail(db, venue_public_id)
    except VenueNotFound as exc:
        raise HTTPException(status_code=404, detail="Venue not found.") from exc


@router.get("/{venue_public_id}/availability", response_model=VenueAvailabilityResponse)
def get_venue_availability(
    venue_public_id: str,
    date_from: date | None = None,
    days: int = Query(default=7, ge=1, le=31),
    db: Session = Depends(get_db),
) -> VenueAvailabilityResponse:
    try:
        return list_venue_availability(db, venue_public_id, date_from, days)
    except VenueNotFound as exc:
        raise HTTPException(status_code=404, detail="Venue not found.") from exc
