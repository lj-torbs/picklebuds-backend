from pydantic import BaseModel, Field

from app.schemas.booking import OwnerBookingReviewItemResponse
from app.schemas.venue import VenueDetailResponse


class OwnerTransactionsResponse(BaseModel):
    items: list[OwnerBookingReviewItemResponse] = Field(default_factory=list)


class OwnerDashboardStatsResponse(BaseModel):
    total_revenue: float
    pending_count: int
    completed_count: int
    cancelled_count: int
    venue_count: int
    court_count: int


class OwnerDashboardResponse(BaseModel):
    stats: OwnerDashboardStatsResponse
    recent_transactions: list[OwnerBookingReviewItemResponse] = Field(default_factory=list)


class OwnerVenueListResponse(BaseModel):
    items: list[VenueDetailResponse] = Field(default_factory=list)
