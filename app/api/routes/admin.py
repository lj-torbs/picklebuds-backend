from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.schemas.admin import (
    AdminOwnerDetailResponse,
    AdminOwnerListResponse,
    AdminOwnerPaymentStatusUpdateRequest,
    AdminOwnerStatusUpdateRequest,
    AdminOwnerStatusActionResponse,
)
from app.schemas.common import CurrentUser
from app.services.admin_service import (
    AdminOwnerFailure,
    get_admin_owner_detail,
    list_admin_owners as list_admin_owner_summaries,
    lock_owner_access,
    set_owner_access_status,
    set_owner_system_payment_status,
    unlock_owner_access,
)

router = APIRouter()


@router.get("/owners", response_model=AdminOwnerListResponse)
def list_admin_owner_list(
    q: str | None = Query(default=None),
    payment_status: str | None = Query(default=None),
    access_status: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> AdminOwnerListResponse:
    return list_admin_owner_summaries(
        db,
        q=q,
        payment_status=payment_status,
        access_status=access_status,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/owners/{owner_public_id}", response_model=AdminOwnerDetailResponse)
def get_owner_detail(
    owner_public_id: str,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> AdminOwnerDetailResponse:
    try:
        return get_admin_owner_detail(
            db,
            owner_public_id,
            date_from=date_from,
            date_to=date_to,
        )
    except AdminOwnerFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/owners/{owner_public_id}/payment-status", response_model=AdminOwnerStatusActionResponse)
def update_owner_payment_status(
    owner_public_id: str,
    payload: AdminOwnerPaymentStatusUpdateRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> AdminOwnerStatusActionResponse:
    try:
        return set_owner_system_payment_status(db, owner_public_id, payload.status)
    except AdminOwnerFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/owners/{owner_public_id}/status", response_model=AdminOwnerStatusActionResponse)
def update_owner_access_status(
    owner_public_id: str,
    payload: AdminOwnerStatusUpdateRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> AdminOwnerStatusActionResponse:
    try:
        return set_owner_access_status(
            db,
            owner_public_id,
            payload.status,
            payload.reason,
        )
    except AdminOwnerFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/owners/{owner_public_id}/lock", response_model=AdminOwnerStatusActionResponse)
def lock_owner(
    owner_public_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> AdminOwnerStatusActionResponse:
    try:
        return lock_owner_access(db, owner_public_id)
    except AdminOwnerFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/owners/{owner_public_id}/unlock", response_model=AdminOwnerStatusActionResponse)
def unlock_owner(
    owner_public_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> AdminOwnerStatusActionResponse:
    try:
        return unlock_owner_access(db, owner_public_id)
    except AdminOwnerFailure as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
