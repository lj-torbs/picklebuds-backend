from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.schemas.common import CurrentUser
from app.schemas.owner_manage import (
    OwnerCourtUpsertRequest,
    OwnerStatusUpdateRequest,
    OwnerVenueUpsertRequest,
)
from app.schemas.owner import (
    OwnerDashboardResponse,
    OwnerTransactionsResponse,
    OwnerVenueListResponse,
)
from app.services.owner_service import (
    get_owner_dashboard,
    create_owner_court,
    create_owner_venue,
    delete_owner_court,
    list_owner_transactions,
    list_owner_venues,
    OwnerManageFailure,
    set_owner_court_status,
    set_owner_venue_status,
    update_owner_court,
    update_owner_venue,
)
from app.schemas.venue import VenueDetailResponse

router = APIRouter()


@router.get("/me")
def owner_me(
    current_user: CurrentUser = Depends(require_role("owner")),
) -> CurrentUser:
    return current_user


@router.get("/dashboard", response_model=OwnerDashboardResponse)
def owner_dashboard(
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> OwnerDashboardResponse:
    return get_owner_dashboard(db, current_user)


@router.get("/venues", response_model=OwnerVenueListResponse)
def owner_venues(
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> OwnerVenueListResponse:
    return list_owner_venues(db, current_user)


@router.get("/transactions", response_model=OwnerTransactionsResponse)
def owner_transactions(
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> OwnerTransactionsResponse:
    return list_owner_transactions(db, current_user)


@router.post("/venues", response_model=VenueDetailResponse)
def create_venue(
    payload: OwnerVenueUpsertRequest,
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> VenueDetailResponse:
    try:
        return create_owner_venue(db, current_user, payload)
    except OwnerManageFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.put("/venues/{venue_public_id}", response_model=VenueDetailResponse)
def update_venue(
    venue_public_id: str,
    payload: OwnerVenueUpsertRequest,
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> VenueDetailResponse:
    try:
        return update_owner_venue(db, current_user, venue_public_id, payload)
    except OwnerManageFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.patch("/venues/{venue_public_id}/status", response_model=VenueDetailResponse)
def update_venue_status(
    venue_public_id: str,
    payload: OwnerStatusUpdateRequest,
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> VenueDetailResponse:
    try:
        return set_owner_venue_status(db, current_user, venue_public_id, payload)
    except OwnerManageFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/venues/{venue_public_id}/courts", response_model=VenueDetailResponse)
def create_court(
    venue_public_id: str,
    payload: OwnerCourtUpsertRequest,
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> VenueDetailResponse:
    try:
        return create_owner_court(db, current_user, venue_public_id, payload)
    except OwnerManageFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.put("/venues/{venue_public_id}/courts/{court_public_id}", response_model=VenueDetailResponse)
def update_court(
    venue_public_id: str,
    court_public_id: str,
    payload: OwnerCourtUpsertRequest,
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> VenueDetailResponse:
    try:
        return update_owner_court(
            db,
            current_user,
            venue_public_id,
            court_public_id,
            payload,
        )
    except OwnerManageFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.patch("/venues/{venue_public_id}/courts/{court_public_id}/status", response_model=VenueDetailResponse)
def update_court_status(
    venue_public_id: str,
    court_public_id: str,
    payload: OwnerStatusUpdateRequest,
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> VenueDetailResponse:
    try:
        return set_owner_court_status(
            db,
            current_user,
            venue_public_id,
            court_public_id,
            payload,
        )
    except OwnerManageFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete("/venues/{venue_public_id}/courts/{court_public_id}", response_model=VenueDetailResponse)
def delete_court(
    venue_public_id: str,
    court_public_id: str,
    current_user: CurrentUser = Depends(require_role("owner")),
    db: Session = Depends(get_db),
) -> VenueDetailResponse:
    try:
        return delete_owner_court(
            db,
            current_user,
            venue_public_id,
            court_public_id,
        )
    except OwnerManageFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
