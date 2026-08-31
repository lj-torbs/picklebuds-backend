from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.settlement import OwnerSettlement
from app.models.transaction import Transaction
from app.models.user import Owner
from app.models.venue import Court, Venue
from app.schemas.admin import (
    AdminOwnerDetailResponse,
    AdminOwnerListResponse,
    AdminOwnerStatusActionResponse,
    AdminOwnerSummary,
    AdminOwnerTransactionSummary,
)


SYSTEM_SHARE_RATE = Decimal("0.12")


@dataclass
class AdminOwnerFailure(Exception):
    message: str
    status_code: int = 400


def _parse_date_range(date_from: str | None, date_to: str | None) -> tuple[date | None, date | None]:
    parsed_from = date.fromisoformat(date_from) if date_from else None
    parsed_to = date.fromisoformat(date_to) if date_to else None
    return parsed_from, parsed_to


def _apply_owner_filters(
    statement: Select,
    *,
    q: str | None,
    payment_status: str | None,
    access_status: str | None,
) -> Select:
    filters = []
    if q:
        normalized = f"%{q.strip()}%"
        filters.append(
            or_(
                Owner.full_name.ilike(normalized),
                Owner.email.ilike(normalized),
                Owner.business_name.ilike(normalized),
            )
        )
    if payment_status in {"paid", "unpaid"}:
        filters.append(Owner.system_payment_status == payment_status)
    if access_status == "suspended":
        filters.append(Owner.status == "suspended")
    elif access_status in {"active", "inactive"}:
        filters.append(Owner.status == access_status)
    if filters:
        statement = statement.where(and_(*filters))
    return statement


def _build_revenue_map(
    db: Session,
    *,
    date_from: date | None,
    date_to: date | None,
) -> dict[int, dict[str, float]]:
    statement = (
        select(
            Venue.owner_id,
            func.coalesce(func.sum(Transaction.amount), 0),
        )
        .select_from(Transaction)
        .join(Booking, Booking.id == Transaction.booking_id)
        .join(Venue, Venue.id == Transaction.venue_id)
        .where(Transaction.payment_status == "paid")
    )

    if date_from is not None:
        statement = statement.where(Booking.booking_date >= date_from)
    if date_to is not None:
        statement = statement.where(Booking.booking_date <= date_to)

    statement = statement.group_by(Venue.owner_id)
    rows = db.execute(statement).all()

    revenue_map: dict[int, dict[str, float]] = {}
    for owner_id, gross_amount in rows:
        gross = float(gross_amount or 0)
        system_share = float((Decimal(str(gross)) * SYSTEM_SHARE_RATE).quantize(Decimal("0.01")))
        revenue_map[owner_id] = {
            "gross_revenue": gross,
            "system_share": system_share,
            "owner_total_profit": round(gross - system_share, 2),
        }
    return revenue_map


def _build_venue_counts(
    db: Session,
    owner_ids: list[int],
) -> tuple[dict[int, int], dict[int, int]]:
    if not owner_ids:
        return {}, {}

    gym_rows = db.execute(
        select(Venue.owner_id, func.count(Venue.id)).where(Venue.owner_id.in_(owner_ids)).group_by(Venue.owner_id)
    ).all()
    court_rows = db.execute(
        select(Venue.owner_id, func.count(Court.id))
        .select_from(Court)
        .join(Venue, Venue.id == Court.venue_id)
        .where(Venue.owner_id.in_(owner_ids))
        .group_by(Venue.owner_id)
    ).all()

    return dict(gym_rows), dict(court_rows)


def _owner_summary_from_model(
    owner: Owner,
    *,
    total_gyms: int,
    total_courts: int,
    gross_revenue: float,
    system_share: float,
    owner_total_profit: float,
) -> AdminOwnerSummary:
    return AdminOwnerSummary(
        id=owner.public_id,
        name=owner.full_name,
        email=owner.email,
        phone=owner.phone,
        joined_at=owner.created_at.isoformat() if owner.created_at else None,
        status=owner.status,
        system_payment_status=owner.system_payment_status,
        suspension_reason=owner.suspension_reason,
        total_gyms=total_gyms,
        total_courts=total_courts,
        gross_revenue=round(gross_revenue, 2),
        system_share=round(system_share, 2),
        owner_total_profit=round(owner_total_profit, 2),
    )


def list_admin_owners(
    db: Session,
    *,
    q: str | None = None,
    payment_status: str | None = None,
    access_status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> AdminOwnerListResponse:
    parsed_from, parsed_to = _parse_date_range(date_from, date_to)
    statement = select(Owner).order_by(Owner.created_at.desc(), Owner.id.desc())
    statement = _apply_owner_filters(
        statement,
        q=q,
        payment_status=payment_status,
        access_status=access_status,
    )
    owners = list(db.scalars(statement))
    owner_ids = [owner.id for owner in owners]
    gym_counts, court_counts = _build_venue_counts(db, owner_ids)
    revenue_map = _build_revenue_map(db, date_from=parsed_from, date_to=parsed_to)

    items = []
    for owner in owners:
        revenue = revenue_map.get(
            owner.id,
            {"gross_revenue": 0.0, "system_share": 0.0, "owner_total_profit": 0.0},
        )
        items.append(
            _owner_summary_from_model(
                owner,
                total_gyms=int(gym_counts.get(owner.id, 0) or 0),
                total_courts=int(court_counts.get(owner.id, 0) or 0),
                gross_revenue=revenue["gross_revenue"],
                system_share=revenue["system_share"],
                owner_total_profit=revenue["owner_total_profit"],
            )
        )
    return AdminOwnerListResponse(items=items)


def _get_owner_or_fail(db: Session, owner_public_id: str) -> Owner:
    owner = db.scalar(select(Owner).where(Owner.public_id == owner_public_id))
    if owner is None:
        raise AdminOwnerFailure("Owner was not found.", status_code=404)
    return owner


def get_admin_owner_detail(
    db: Session,
    owner_public_id: str,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
) -> AdminOwnerDetailResponse:
    parsed_from, parsed_to = _parse_date_range(date_from, date_to)
    owner = _get_owner_or_fail(db, owner_public_id)
    summary = list_admin_owners(
        db,
        q=None,
        payment_status=None,
        access_status=None,
        date_from=date_from,
        date_to=date_to,
    )
    owner_summary = next((item for item in summary.items if item.id == owner_public_id), None)
    if owner_summary is None:
        owner_summary = _owner_summary_from_model(
            owner,
            total_gyms=0,
            total_courts=0,
            gross_revenue=0,
            system_share=0,
            owner_total_profit=0,
        )

    statement = (
        select(
            Transaction.public_id,
            Booking.public_id,
            Booking.booked_by_name_snapshot,
            Venue.name,
            Court.name,
            Booking.booking_type,
            Booking.booking_date,
            Transaction.amount,
            Transaction.payment_status,
            Transaction.status,
            Transaction.created_at,
        )
        .select_from(Transaction)
        .join(Booking, Booking.id == Transaction.booking_id)
        .join(Venue, Venue.id == Transaction.venue_id)
        .outerjoin(Court, Court.id == Transaction.court_id)
        .where(Venue.owner_id == owner.id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
    )
    if parsed_from is not None:
        statement = statement.where(Booking.booking_date >= parsed_from)
    if parsed_to is not None:
        statement = statement.where(Booking.booking_date <= parsed_to)

    transactions = [
        AdminOwnerTransactionSummary(
            id=row[0],
            booking_id=row[1],
            customer_name=row[2],
            gym_name=row[3],
            court_name=row[4] or "Whole gym",
            booking_type=row[5],
            booking_date=row[6].isoformat(),
            amount=float(row[7] or 0),
            payment_status=row[8],
            status=row[9],
            created_at=row[10].isoformat() if row[10] else "",
        )
        for row in db.execute(statement).all()
    ]
    return AdminOwnerDetailResponse(owner=owner_summary, transactions=transactions)


def _get_latest_owner_settlement(db: Session, owner_id: int) -> OwnerSettlement | None:
    return db.scalar(
        select(OwnerSettlement)
        .where(OwnerSettlement.owner_id == owner_id)
        .order_by(OwnerSettlement.period_end.desc(), OwnerSettlement.id.desc())
    )


def set_owner_system_payment_status(
    db: Session,
    owner_public_id: str,
    status: str,
) -> AdminOwnerStatusActionResponse:
    if status not in {"paid", "unpaid"}:
        raise AdminOwnerFailure("Invalid owner payment status.", status_code=422)

    owner = _get_owner_or_fail(db, owner_public_id)
    owner.system_payment_status = status

    if status == "paid" and owner.suspension_reason == "system_payment_due":
        owner.status = "active"
        owner.suspension_reason = None

    latest_settlement = _get_latest_owner_settlement(db, owner.id)
    if latest_settlement is not None:
        latest_settlement.payment_status = status
        latest_settlement.paid_at = datetime.now(UTC).replace(tzinfo=None) if status == "paid" else None
        if status == "paid":
            latest_settlement.locked_at = None

    db.commit()
    db.refresh(owner)
    return AdminOwnerStatusActionResponse(
        owner_public_id=owner.public_id,
        status=owner.status,
        system_payment_status=owner.system_payment_status,
        suspension_reason=owner.suspension_reason,
    )


def lock_owner_access(
    db: Session,
    owner_public_id: str,
) -> AdminOwnerStatusActionResponse:
    owner = _get_owner_or_fail(db, owner_public_id)
    owner.status = "suspended"
    owner.suspension_reason = "system_payment_due"
    owner.system_payment_status = "unpaid"

    latest_settlement = _get_latest_owner_settlement(db, owner.id)
    if latest_settlement is not None:
        latest_settlement.payment_status = "unpaid"
        latest_settlement.locked_at = datetime.now(UTC).replace(tzinfo=None)
        latest_settlement.note = "Owner access locked until settlement is paid."

    db.commit()
    db.refresh(owner)
    return AdminOwnerStatusActionResponse(
        owner_public_id=owner.public_id,
        status=owner.status,
        system_payment_status=owner.system_payment_status,
        suspension_reason=owner.suspension_reason,
    )


def unlock_owner_access(
    db: Session,
    owner_public_id: str,
) -> AdminOwnerStatusActionResponse:
    owner = _get_owner_or_fail(db, owner_public_id)
    if owner.system_payment_status != "paid":
        raise AdminOwnerFailure(
            "Owner must settle the system payment before access can be restored.",
            status_code=400,
        )

    if owner.suspension_reason == "system_payment_due":
        owner.status = "active"
        owner.suspension_reason = None

    latest_settlement = _get_latest_owner_settlement(db, owner.id)
    if latest_settlement is not None and latest_settlement.payment_status == "paid":
        latest_settlement.locked_at = None

    db.commit()
    db.refresh(owner)
    return AdminOwnerStatusActionResponse(
        owner_public_id=owner.public_id,
        status=owner.status,
        system_payment_status=owner.system_payment_status,
        suspension_reason=owner.suspension_reason,
    )


def set_owner_access_status(
    db: Session,
    owner_public_id: str,
    status: str,
    reason: str | None = None,
) -> AdminOwnerStatusActionResponse:
    if status not in {"active", "suspended"}:
        raise AdminOwnerFailure("Invalid owner access status.", status_code=422)
    if status == "suspended" and reason not in {"manual_review", "system_payment_due"}:
        raise AdminOwnerFailure("A valid suspension reason is required.", status_code=422)

    owner = _get_owner_or_fail(db, owner_public_id)
    owner.status = status
    owner.suspension_reason = reason if status == "suspended" else None

    latest_settlement = _get_latest_owner_settlement(db, owner.id)
    if latest_settlement is not None:
        if status == "suspended" and reason == "system_payment_due":
            latest_settlement.locked_at = datetime.now(UTC).replace(tzinfo=None)
            latest_settlement.payment_status = "unpaid"
            latest_settlement.note = "Owner access locked until settlement is paid."
            owner.system_payment_status = "unpaid"
        elif status == "active" and latest_settlement.payment_status == "paid":
            latest_settlement.locked_at = None

    db.commit()
    db.refresh(owner)
    return AdminOwnerStatusActionResponse(
        owner_public_id=owner.public_id,
        status=owner.status,
        system_payment_status=owner.system_payment_status,
        suspension_reason=owner.suspension_reason,
    )
