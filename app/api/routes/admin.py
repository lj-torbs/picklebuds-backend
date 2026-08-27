from fastapi import APIRouter, Depends

from app.api.deps import require_role
from app.schemas.common import CurrentUser

router = APIRouter()


@router.get("/owners")
def list_admin_owners(
    current_user: CurrentUser = Depends(require_role("admin")),
) -> dict[str, list[dict[str, str]]]:
    return {"items": []}


@router.post("/owners/{owner_public_id}/lock")
def lock_owner(
    owner_public_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
) -> dict[str, str]:
    return {"owner_public_id": owner_public_id, "status": "locked"}


@router.post("/owners/{owner_public_id}/unlock")
def unlock_owner(
    owner_public_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
) -> dict[str, str]:
    return {"owner_public_id": owner_public_id, "status": "unlocked"}
