from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


VenueStatus = Literal["active", "inactive"]
CourtStatus = Literal["available", "maintenance"]
BookingMode = Literal["private", "open_play"]
PaymentProvider = Literal["GCash", "Bank Transfer", "Maya", "Other"]
RentalCategory = Literal["paddle", "ball", "shoes", "net", "other"]
RentalItemStatus = Literal["available", "unavailable"]
AvailabilityState = Literal["available", "booked", "closed"]


class VenueListItemResponse(BaseModel):
    public_id: str
    name: str
    address: str
    phone: str | None = None
    status: VenueStatus
    image_url: str | None = None
    court_count: int = 0
    has_open_play: bool = False
    whole_gym_enabled: bool = False


class VenueListResponse(BaseModel):
    items: list[VenueListItemResponse]


class VenuePaymentMethodResponse(BaseModel):
    id: int
    provider: PaymentProvider
    display_name: str
    account_name: str
    account_number: str
    instructions: str | None = None
    qr_code_image_url: str
    qr_code_file_name: str
    is_active: bool


class VenueRentalItemResponse(BaseModel):
    public_id: str
    name: str
    category: RentalCategory
    price_per_session: float
    quantity_available: int
    status: RentalItemStatus
    description: str | None = None


class VenueCourtResponse(BaseModel):
    public_id: str
    name: str
    surface: str
    capacity_label: str
    price_per_hour: float
    status: CourtStatus
    booking_mode: BookingMode
    open_play_capacity: int | None = None
    available_slots: list[str] = Field(default_factory=list)
    image_url: str | None = None


class VenueWholeGymBookingResponse(BaseModel):
    enabled: bool
    price_per_hour: float | None = None
    available_slots: list[str] = Field(default_factory=list)
    notes: str | None = None


class VenueDetailResponse(BaseModel):
    public_id: str
    owner_public_id: str
    name: str
    address: str
    phone: str | None = None
    status: VenueStatus
    image_url: str | None = None
    payment_methods: list[VenuePaymentMethodResponse] = Field(default_factory=list)
    whole_gym_booking: VenueWholeGymBookingResponse | None = None
    rental_items: list[VenueRentalItemResponse] = Field(default_factory=list)
    courts: list[VenueCourtResponse] = Field(default_factory=list)


class VenueAvailabilityItemResponse(BaseModel):
    date: date
    slot_label: str
    state: AvailabilityState
    booking_public_id: str | None = None
    booking_type: Literal["private", "open_play", "whole_gym"] | None = None
    seats_taken: int | None = None
    seats_capacity: int | None = None


class VenueCourtAvailabilityResponse(BaseModel):
    court_public_id: str
    court_name: str
    booking_mode: BookingMode
    items: list[VenueAvailabilityItemResponse] = Field(default_factory=list)


class VenueWholeGymAvailabilityResponse(BaseModel):
    items: list[VenueAvailabilityItemResponse] = Field(default_factory=list)


class VenueAvailabilityResponse(BaseModel):
    venue_public_id: str
    date_from: date
    days: int
    courts: list[VenueCourtAvailabilityResponse] = Field(default_factory=list)
    whole_gym: VenueWholeGymAvailabilityResponse | None = None
