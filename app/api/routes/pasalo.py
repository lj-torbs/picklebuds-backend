from fastapi import APIRouter

from app.schemas.pasalo import PasaloClaimRequest, PasaloOfferRequest


router = APIRouter()


@router.post("/offers")
def create_offer(payload: PasaloOfferRequest) -> dict[str, str]:
    return {"booking_public_id": payload.booking_public_id, "status": "open"}


@router.post("/offers/{offer_id}/claim")
def claim_offer(offer_id: str, payload: PasaloClaimRequest) -> dict[str, str]:
    return {
        "offer_id": offer_id,
        "claimant_email": payload.claimant_email,
        "status": "pending",
    }


@router.post("/claims/{claim_id}/approve")
def approve_claim(claim_id: str) -> dict[str, str]:
    return {"claim_id": claim_id, "status": "approved"}


@router.post("/claims/{claim_id}/reject")
def reject_claim(claim_id: str) -> dict[str, str]:
    return {"claim_id": claim_id, "status": "rejected"}
