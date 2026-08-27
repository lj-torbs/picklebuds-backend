from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse, SignupRequest
from app.schemas.common import CurrentUser
from app.services.auth_service import (
    AuthFailure,
    SignupFailure,
    authenticate_user,
    signup_player,
)


router = APIRouter()
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW = timedelta(minutes=5)
_login_attempts: dict[str, deque[datetime]] = defaultdict(deque)


@dataclass
class LoginRateLimitState:
    blocked: bool
    retry_after_seconds: int = 0


def _login_rate_limit_key(request: Request, email: str, role: str) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else None
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"
    return f"{client_ip}:{role}:{email.lower()}"


def _check_login_rate_limit(key: str) -> LoginRateLimitState:
    now = datetime.now(UTC)
    attempts = _login_attempts[key]
    cutoff = now - LOGIN_WINDOW

    while attempts and attempts[0] < cutoff:
        attempts.popleft()

    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        retry_at = attempts[0] + LOGIN_WINDOW
        retry_after = max(1, int((retry_at - now).total_seconds()))
        return LoginRateLimitState(blocked=True, retry_after_seconds=retry_after)

    return LoginRateLimitState(blocked=False)


def _record_failed_login(key: str) -> None:
    now = datetime.now(UTC)
    attempts = _login_attempts[key]
    cutoff = now - LOGIN_WINDOW

    while attempts and attempts[0] < cutoff:
        attempts.popleft()

    attempts.append(now)


def _clear_failed_logins(key: str) -> None:
    _login_attempts.pop(key, None)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> LoginResponse:
    rate_limit_key = _login_rate_limit_key(request, payload.email, payload.role)
    limit_state = _check_login_rate_limit(rate_limit_key)
    if limit_state.blocked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many login attempts. "
                f"Try again in {limit_state.retry_after_seconds} seconds."
            ),
            headers={"Retry-After": str(limit_state.retry_after_seconds)},
        )

    try:
        user = authenticate_user(db, payload.email, payload.password, payload.role)
    except AuthFailure as exc:
        _record_failed_login(rate_limit_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
        ) from exc

    _clear_failed_logins(rate_limit_key)
    access_token = create_access_token({"sub": user.public_id, "role": user.role})
    return LoginResponse(
        access_token=access_token,
        role=user.role,
        user=user,
    )


@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> LoginResponse:
    try:
        user = signup_player(db, payload.full_name, payload.email, payload.password)
    except SignupFailure as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc

    access_token = create_access_token({"sub": user.public_id, "role": user.role})
    return LoginResponse(
        access_token=access_token,
        role=user.role,
        user=user,
    )


@router.get("/me", response_model=CurrentUser)
def me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user
