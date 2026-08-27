import secrets
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import Admin, Owner, Player
from app.schemas.common import CurrentUser, UserRole


@dataclass
class AuthFailure(Exception):
    message: str


@dataclass
class SignupFailure(Exception):
    message: str


def _build_current_user(user: Player | Owner | Admin, role: UserRole) -> CurrentUser:
    joined_at = None
    if isinstance(user, Player):
        joined_at = user.joined_at.isoformat() if isinstance(user.joined_at, datetime) else None
    return CurrentUser(
        id=user.id,
        public_id=user.public_id,
        full_name=user.full_name,
        email=user.email,
        role=role,
        joined_at=joined_at,
    )


def authenticate_user(
    db: Session,
    email: str,
    password: str,
    role: UserRole,
) -> CurrentUser:
    model_map = {
        "player": Player,
        "owner": Owner,
        "admin": Admin,
    }
    model = model_map[role]
    user = db.scalar(select(model).where(model.email == email))

    if user is None or not verify_password(password, user.password_hash):
        raise AuthFailure("Invalid email, password, or role.")

    if role == "player" and user.status != "active":
        raise AuthFailure("Player account is suspended.")

    if role == "owner":
        if user.status == "inactive":
            raise AuthFailure("Owner account is inactive.")
        if user.status == "suspended":
            if user.suspension_reason == "system_payment_due":
                raise AuthFailure("Owner account is locked until system payment is settled.")
            raise AuthFailure("Owner account is suspended.")

    if role == "admin" and user.status != "active":
        raise AuthFailure("Admin account is inactive.")

    return _build_current_user(user, role)


def _generate_player_public_id(db: Session) -> str:
    for _ in range(10):
        public_id = f"USR-{secrets.token_hex(4).upper()}"
        exists = db.scalar(select(Player.id).where(Player.public_id == public_id))
        if exists is None:
            return public_id
    raise SignupFailure("Unable to generate a unique player ID.")


def signup_player(
    db: Session,
    full_name: str,
    email: str,
    password: str,
) -> CurrentUser:
    existing_player = db.scalar(select(Player).where(Player.email == email))
    existing_owner = db.scalar(select(Owner.id).where(Owner.email == email))
    existing_admin = db.scalar(select(Admin.id).where(Admin.email == email))

    if existing_player:
        raise SignupFailure("A player account with this email already exists.")
    if existing_owner:
        raise SignupFailure("This email is already used by an owner account.")
    if existing_admin:
        raise SignupFailure("This email is already reserved by an admin account.")

    player = Player(
        public_id=_generate_player_public_id(db),
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        status="active",
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return _build_current_user(player, "player")


def get_user_by_public_id(
    db: Session,
    role: UserRole,
    public_id: str,
) -> CurrentUser | None:
    model_map = {
        "player": Player,
        "owner": Owner,
        "admin": Admin,
    }
    model = model_map[role]
    user = db.scalar(select(model).where(model.public_id == public_id))
    if user is None:
        return None
    return _build_current_user(user, role)
