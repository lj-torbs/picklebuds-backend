from fastapi import APIRouter, Depends

from app.api.deps import require_role
from app.schemas.common import CurrentUser

router = APIRouter()


@router.get("/me")
def owner_me(
    current_user: CurrentUser = Depends(require_role("owner")),
) -> CurrentUser:
    return current_user


@router.get("/transactions")
def owner_transactions(
    current_user: CurrentUser = Depends(require_role("owner")),
) -> dict[str, list[dict[str, str]]]:
    return {"items": []}
