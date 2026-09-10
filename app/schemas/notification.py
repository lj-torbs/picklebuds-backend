from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class NotificationItemResponse(BaseModel):
    id: int
    recipient_type: Literal["player", "owner"]
    title: str
    message: str
    action_url: str | None
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationItemResponse]
