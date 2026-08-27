from typing import Literal

from pydantic import BaseModel


class PaymentProofResponse(BaseModel):
    booking_public_id: str
    review_status: Literal["pending", "approved", "rejected"]
    payment_status: Literal["unpaid", "paid", "refunded"]
