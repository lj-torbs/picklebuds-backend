from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.common import CurrentUser
from app.schemas.notification import NotificationItemResponse, NotificationListResponse


def create_player_notification(
    db: Session,
    *,
    player_id: int,
    booking_id: int | None,
    title: str,
    message: str,
    action_url: str | None = None,
    created_at: datetime | None = None,
) -> Notification:
    notification = Notification(
        recipient_type="player",
        player_id=player_id,
        owner_id=None,
        booking_id=booking_id,
        title=title,
        message=message,
        action_url=action_url,
        is_read=False,
        created_at=created_at or datetime.utcnow(),
    )
    db.add(notification)
    return notification


def create_owner_notification(
    db: Session,
    *,
    owner_id: int,
    booking_id: int | None,
    title: str,
    message: str,
    action_url: str | None = None,
    created_at: datetime | None = None,
) -> Notification:
    notification = Notification(
        recipient_type="owner",
        player_id=None,
        owner_id=owner_id,
        booking_id=booking_id,
        title=title,
        message=message,
        action_url=action_url,
        is_read=False,
        created_at=created_at or datetime.utcnow(),
    )
    db.add(notification)
    return notification


def list_notifications(db: Session, current_user: CurrentUser) -> NotificationListResponse:
    statement = select(Notification).order_by(
        Notification.created_at.desc(),
        Notification.id.desc(),
    )

    if current_user.role == "player":
        statement = statement.where(
            Notification.recipient_type == "player",
            Notification.player_id == current_user.id,
        )
    elif current_user.role == "owner":
        statement = statement.where(
            Notification.recipient_type == "owner",
            Notification.owner_id == current_user.id,
        )
    else:
        return NotificationListResponse(items=[])

    notifications = db.scalars(statement).all()
    return NotificationListResponse(
        items=[
            NotificationItemResponse(
                id=notification.id,
                recipient_type=notification.recipient_type,
                title=notification.title,
                message=notification.message,
                action_url=notification.action_url,
                is_read=notification.is_read,
                created_at=notification.created_at,
            )
            for notification in notifications
        ]
    )


def mark_notification_read(
    db: Session,
    current_user: CurrentUser,
    notification_id: int,
) -> NotificationItemResponse:
    statement = select(Notification).where(Notification.id == notification_id)
    if current_user.role == "player":
        statement = statement.where(
            Notification.recipient_type == "player",
            Notification.player_id == current_user.id,
        )
    elif current_user.role == "owner":
        statement = statement.where(
            Notification.recipient_type == "owner",
            Notification.owner_id == current_user.id,
        )
    else:
        raise ValueError("Unsupported notification recipient.")

    notification = db.scalar(statement)
    if notification is None:
        raise LookupError("Notification not found.")

    notification.is_read = True
    db.commit()
    db.refresh(notification)

    return NotificationItemResponse(
        id=notification.id,
        recipient_type=notification.recipient_type,
        title=notification.title,
        message=notification.message,
        action_url=notification.action_url,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )
