from fastapi import APIRouter


router = APIRouter()


@router.get("")
def list_venues() -> dict[str, list[dict[str, str]]]:
    return {"items": []}


@router.get("/{venue_public_id}")
def get_venue(venue_public_id: str) -> dict[str, str]:
    return {"venue_public_id": venue_public_id}
