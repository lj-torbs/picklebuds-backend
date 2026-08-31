from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import CurrentUser, UserRole


class LoginRequest(BaseModel):
    email: str
    password: str
    role: UserRole

    @field_validator("email")
    @classmethod
    def validate_login_email(cls, value: str) -> str:
        normalized = value.strip()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("A valid email address is required.")
        return normalized.lower()


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=60)
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Full name is required.")
        if not all(char.isalpha() or char in {" ", "'", "-"} for char in normalized):
            raise ValueError(
                "Full name can only contain letters, spaces, apostrophes, and hyphens."
            )
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(char.isalpha() for char in value) or not any(char.isdigit() for char in value):
            raise ValueError("Password must include at least one letter and one number.")
        return value


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user: CurrentUser
