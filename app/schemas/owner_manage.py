from pydantic import BaseModel, Field

from app.schemas.venue import (
    CourtStatus,
    PaymentProvider,
    RentalCategory,
    RentalItemStatus,
    VenueStatus,
)


class OwnerVenuePaymentMethodInput(BaseModel):
    provider: PaymentProvider
    account_name: str = Field(min_length=1, max_length=160)
    account_number: str = Field(min_length=1, max_length=120)
    instructions: str | None = None
    qr_code_image_url: str = Field(min_length=1, max_length=500)
    qr_code_file_name: str = Field(min_length=1, max_length=255)
    is_active: bool = True


class OwnerVenueWholeGymInput(BaseModel):
    enabled: bool
    price_per_hour: float | None = Field(default=None, ge=0)
    available_slots: list[str] = Field(default_factory=list)
    notes: str | None = None


class OwnerVenueRentalItemInput(BaseModel):
    public_id: str | None = None
    name: str = Field(min_length=1, max_length=120)
    category: RentalCategory
    price_per_session: float = Field(ge=0)
    quantity_available: int = Field(ge=0)
    status: RentalItemStatus
    description: str | None = None


class OwnerVenueUpsertRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    address: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    status: VenueStatus
    image_url: str | None = Field(default=None, max_length=500)
    payment_methods: list[OwnerVenuePaymentMethodInput] = Field(default_factory=list)
    whole_gym_booking: OwnerVenueWholeGymInput | None = None
    rental_items: list[OwnerVenueRentalItemInput] = Field(default_factory=list)


class OwnerCourtUpsertRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    surface: str = Field(min_length=1, max_length=120)
    capacity_label: str = Field(min_length=1, max_length=120)
    price_per_hour: float = Field(ge=0)
    status: CourtStatus
    booking_mode: str
    open_play_capacity: int | None = Field(default=None, ge=2)
    available_slots: list[str] = Field(default_factory=list)
    image_url: str | None = Field(default=None, max_length=500)


class OwnerStatusUpdateRequest(BaseModel):
    status: str
