from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


BookingType = Literal["private", "open_play", "whole_gym"]
BookingStatus = Literal["pending", "confirmed", "completed", "cancelled"]
PaymentStatus = Literal["unpaid", "paid", "refunded"]
RentalCategory = Literal["paddle", "ball", "shoes", "net", "other"]
PaymentReviewStatus = Literal["pending", "approved", "rejected"]


class BookingRentalItemInput(BaseModel):
    rental_item_public_id: str
    quantity: int = Field(ge=1)


class BookingPaymentInput(BaseModel):
    venue_payment_method_id: int | None = None
    provider: str | None = None
    account_number: str | None = None
    reference_number: str = Field(min_length=6, max_length=120)
    sender_account_name: str = Field(min_length=1, max_length=160)
    receipt_file_name: str = Field(min_length=1, max_length=255)
    receipt_image_url: str = Field(min_length=1, max_length=2000000)


class BookingCreateRequest(BaseModel):
    venue_public_id: str
    court_public_id: str | None = None
    booking_type: BookingType
    booking_date: date
    slot_labels: list[str] = Field(min_length=1)
    participant_count: int = Field(default=1, ge=1)
    total_amount: float = Field(ge=0)
    rentals: list[BookingRentalItemInput] = Field(default_factory=list)
    payment: BookingPaymentInput


class BookingResponse(BaseModel):
    public_id: str
    venue_public_id: str
    court_public_id: str | None = None
    booking_type: BookingType
    booking_date: date
    slot_labels: list[str]
    participant_count: int
    status: BookingStatus
    payment_status: PaymentStatus
    total_amount: float


class BookingRentalSnapshotResponse(BaseModel):
    rental_item_public_id: str
    item_name: str
    category: RentalCategory
    price_per_session: float
    quantity: int


class BookingListItemResponse(BookingResponse):
    venue_name: str
    venue_address: str
    court_name: str | None = None
    booked_by_name: str
    booked_by_email: str
    rentals: list[BookingRentalSnapshotResponse] = Field(default_factory=list)


class BookingListResponse(BaseModel):
    items: list[BookingListItemResponse]


class OwnerBookingReviewItemResponse(BaseModel):
    public_id: str
    venue_public_id: str
    venue_name: str
    court_public_id: str | None = None
    court_name: str | None = None
    booking_type: BookingType
    booking_date: date
    slot_labels: list[str]
    participant_count: int
    amount: float
    status: BookingStatus
    payment_status: PaymentStatus
    payment_review_status: PaymentReviewStatus
    payment_method_label: str | None = None
    reference_number: str | None = None
    sender_account_name: str | None = None
    receipt_file_name: str | None = None
    receipt_image_url: str | None = None
    receipt_uploaded_at: datetime | None = None
    customer_name: str
    customer_email: str
    created_at: datetime
    rentals: list[BookingRentalSnapshotResponse] = Field(default_factory=list)


class OwnerBookingReviewListResponse(BaseModel):
    items: list[OwnerBookingReviewItemResponse]


class BookingActionResponse(BaseModel):
    public_id: str
    status: BookingStatus
    payment_status: PaymentStatus
    payment_review_status: PaymentReviewStatus | None = None
