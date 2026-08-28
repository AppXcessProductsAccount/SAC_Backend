from pydantic import BaseModel, EmailStr, Field, model_validator
from uuid import UUID
from datetime import datetime, date
from app.models.user import UserRole, Gender
from app.schema.phone import OptionalPhoneNumber


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    full_name: str
    nickname: str | None = None
    email: EmailStr | None
    phone_number: str | None
    role: UserRole
    gender: Gender | None = None
    dob: date | None = None
    age: int | None = None
    occupation: str | None = None
    address: str | None = None
    is_active: bool
    is_verified: bool
    profile_image_url: str | None
    created_at: datetime


class AdminUserCreate(BaseModel):
    """
    A participant added from the admin panel.

    Self-service signup creates the row during send-otp and leaves it unverified
    until the code is checked. An admin adding someone has already vouched for
    them, so no OTP is issued and the account is created verified; the person can
    sign in through the normal flow whenever they like.
    """
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone_number: OptionalPhoneNumber = None
    nickname: str | None = Field(default=None, max_length=100)
    gender: Gender | None = None
    dob: date | None = None
    occupation: str | None = Field(default=None, max_length=255)
    address: str | None = None

    @model_validator(mode="after")
    def require_a_contact_method(self):
        # Both columns are nullable, but a participant with neither can never be
        # found, contacted, or signed in as.
        if not self.email and not self.phone_number:
            raise ValueError("Provide an email address or a phone number.")
        return self


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone_number: OptionalPhoneNumber = None
    profile_image_url: str | None = None


class LoginResponse(BaseModel):
    message: str
    user: UserResponse
    tokens: Token | None = None
