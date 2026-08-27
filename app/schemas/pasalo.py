from pydantic import BaseModel, EmailStr, Field


class PasaloOfferRequest(BaseModel):
    booking_public_id: str
    asking_price: float = Field(ge=0)
    note: str | None = None


class PasaloClaimRequest(BaseModel):
    claimant_name: str
    claimant_email: EmailStr
    reference_number: str
