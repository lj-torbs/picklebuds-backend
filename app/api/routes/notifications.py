from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.common import CurrentUser
from app.schemas.notification import NotificationItemResponse, NotificationListResponse
from app.services.notification_service import list_notifications, mark_notification_read

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
def get_notifications(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    return list_notifications(db, current_user)


@router.post("/{notification_id}/read", response_model=NotificationItemResponse)
def read_notification(
    notification_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationItemResponse:
    try:
        return mark_notification_read(db, current_user, notification_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
