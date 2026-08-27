from typing import Literal

from pydantic import BaseModel


UserRole = Literal["player", "owner", "admin"]


class CurrentUser(BaseModel):
    id: int
    public_id: str
    full_name: str
    email: str
    role: UserRole
    joined_at: str | None = None
