from pydantic import BaseModel, Field

from app.schemas.booking import OwnerBookingReviewItemResponse
from app.schemas.venue import VenueDetailResponse


class OwnerTransactionsResponse(BaseModel):
    system_fee_per_transaction: float
    items: list[OwnerBookingReviewItemResponse] = Field(default_factory=list)


class OwnerDashboardStatsResponse(BaseModel):
    total_revenue: float
    pending_count: int
    completed_count: int
    cancelled_count: int
    system_fee_per_transaction: float
    system_fee_billable_count: int
    system_fee_owed: float
    venue_count: int
    court_count: int


class OwnerDashboardResponse(BaseModel):
    stats: OwnerDashboardStatsResponse
    recent_transactions: list[OwnerBookingReviewItemResponse] = Field(default_factory=list)


class OwnerVenueListResponse(BaseModel):
    items: list[VenueDetailResponse] = Field(default_factory=list)
