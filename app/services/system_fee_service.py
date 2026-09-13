from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.system_fee import OwnerSystemFeeSetting


DEFAULT_SYSTEM_FEE_PER_TRANSACTION = 10.0


def get_owner_system_fee(db: Session, owner_id: int) -> float:
    fee = db.scalar(
        select(OwnerSystemFeeSetting.fee_per_transaction).where(
            OwnerSystemFeeSetting.owner_id == owner_id
        )
    )
    return float(fee if fee is not None else DEFAULT_SYSTEM_FEE_PER_TRANSACTION)


def get_owner_system_fee_map(
    db: Session,
    owner_ids: list[int],
) -> dict[int, float]:
    if not owner_ids:
        return {}

    fee_map = {owner_id: DEFAULT_SYSTEM_FEE_PER_TRANSACTION for owner_id in owner_ids}
    rows = db.execute(
        select(
            OwnerSystemFeeSetting.owner_id,
            OwnerSystemFeeSetting.fee_per_transaction,
        ).where(OwnerSystemFeeSetting.owner_id.in_(owner_ids))
    ).all()

    for owner_id, fee in rows:
        fee_map[owner_id] = float(fee)

    return fee_map


def set_owner_system_fee(
    db: Session,
    owner_id: int,
    fee_per_transaction: float,
) -> OwnerSystemFeeSetting:
    setting = db.scalar(
        select(OwnerSystemFeeSetting).where(OwnerSystemFeeSetting.owner_id == owner_id)
    )
    if setting is None:
        setting = OwnerSystemFeeSetting(owner_id=owner_id)
        db.add(setting)

    setting.fee_per_transaction = fee_per_transaction
    return setting
