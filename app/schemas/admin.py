from pydantic import BaseModel


OwnerStatus = str
SystemPaymentStatus = str
OwnerSuspensionReason = str | None


class AdminOwnerTransactionSummary(BaseModel):
    id: str
    booking_id: str
    customer_name: str
    gym_name: str
    court_name: str
    booking_type: str
    booking_date: str
    amount: float
    payment_status: str
    status: str
    created_at: str


class AdminOwnerCourtSummary(BaseModel):
    id: str
    name: str
    surface: str
    capacity: str
    price_per_hour: float
    status: str
    booking_mode: str
    open_play_capacity: int | None = None


class AdminOwnerVenueSummary(BaseModel):
    id: str
    name: str
    address: str
    phone: str | None = None
    status: str
    courts: list[AdminOwnerCourtSummary]


class AdminOwnerSummary(BaseModel):
    id: str
    name: str
    email: str
    phone: str | None = None
    joined_at: str | None = None
    status: OwnerStatus
    system_payment_status: SystemPaymentStatus
    suspension_reason: OwnerSuspensionReason = None
    total_gyms: int
    total_courts: int
    gross_revenue: float
    system_fee_per_transaction: float
    system_fee_billable_count: int
    system_share: float
    owner_total_profit: float


class AdminOwnerListResponse(BaseModel):
    items: list[AdminOwnerSummary]


class AdminOwnerDetailResponse(BaseModel):
    owner: AdminOwnerSummary
    venues: list[AdminOwnerVenueSummary]
    transactions: list[AdminOwnerTransactionSummary]


class AdminOwnerPaymentStatusUpdateRequest(BaseModel):
    status: SystemPaymentStatus


class AdminOwnerStatusUpdateRequest(BaseModel):
    status: OwnerStatus
    reason: OwnerSuspensionReason = None


class AdminOwnerSystemFeeUpdateRequest(BaseModel):
    fee_per_transaction: float


class AdminOwnerStatusActionResponse(BaseModel):
    owner_public_id: str
    status: OwnerStatus
    system_payment_status: SystemPaymentStatus
    suspension_reason: OwnerSuspensionReason = None


class AdminOwnerSystemFeeUpdateResponse(BaseModel):
    owner_public_id: str
    fee_per_transaction: float
    system_share: float
    owner_total_profit: float
