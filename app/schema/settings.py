from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.app_settings import DEFAULT_CURRENCIES, DEFAULT_CURRENCY

# ISO 4217 codes are three letters. Anything else is a typo, and a typo here
# silently mislabels every price in the panel.
_CURRENCY_LEN = 3


def _clean_code(value: str) -> str:
    code = (value or "").strip().upper()
    if len(code) != _CURRENCY_LEN or not code.isalpha():
        raise ValueError(f"'{value}' is not a 3-letter currency code.")
    return code


class AppSettingsResponse(BaseModel):
    default_currency: str
    enabled_currencies: list[str]
    default_city: str | None = None
    default_country: str | None = None
    default_address: str | None = None
    timezone: str
    date_format: str
    organisation_name: str | None = None
    support_email: str | None = None
    support_phone: str | None = None
    notify_payment: bool
    notify_program_registration: bool
    notify_membership_application: bool
    notify_participant: bool
    notification_poll_seconds: int
    event_grand_meditation_enabled: bool
    event_announcement_enabled: bool
    event_grand_meditation_content: dict | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class PublicSettings(BaseModel):
    """The subset the public website may read without authenticating."""

    default_currency: str
    enabled_currencies: list[str]
    default_city: str | None = None
    default_country: str | None = None
    timezone: str
    date_format: str
    organisation_name: str | None = None
    support_email: str | None = None
    support_phone: str | None = None
    event_grand_meditation_enabled: bool
    event_announcement_enabled: bool
    event_grand_meditation_content: dict | None = None


class AppSettingsUpdate(BaseModel):
    """
    Every field optional: the panel saves one card at a time, and a partial save
    must not blank the fields the operator did not touch.
    """

    default_currency: str | None = None
    enabled_currencies: list[str] | None = None
    default_city: str | None = Field(default=None, max_length=120)
    default_country: str | None = Field(default=None, max_length=120)
    default_address: str | None = None
    timezone: str | None = Field(default=None, max_length=64)
    date_format: str | None = Field(default=None, max_length=32)
    organisation_name: str | None = Field(default=None, max_length=200)
    support_email: EmailStr | None = None
    support_phone: str | None = Field(default=None, max_length=40)
    notify_payment: bool | None = None
    notify_program_registration: bool | None = None
    notify_membership_application: bool | None = None
    notify_participant: bool | None = None
    notification_poll_seconds: int | None = Field(default=None, ge=15, le=3600)
    event_grand_meditation_enabled: bool | None = None
    event_announcement_enabled: bool | None = None
    event_grand_meditation_content: dict | None = None

    @field_validator("default_currency")
    @classmethod
    def valid_default_currency(cls, v: str | None) -> str | None:
        return _clean_code(v) if v is not None else None

    @field_validator("enabled_currencies")
    @classmethod
    def valid_currency_list(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        # Deduplicate while keeping the operator's ordering — the first entry is
        # what the programme form preselects.
        seen: list[str] = []
        for raw in v:
            code = _clean_code(raw)
            if code not in seen:
                seen.append(code)
        if not seen:
            raise ValueError("Enable at least one currency.")
        return seen

    @field_validator(
        "default_city",
        "default_country",
        "default_address",
        "organisation_name",
        "support_phone",
    )
    @classmethod
    def blank_to_none(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        return stripped or None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=10)
    new_password: str = Field(min_length=8, max_length=128)


__all__ = [
    "AppSettingsResponse",
    "AppSettingsUpdate",
    "PublicSettings",
    "ChangePasswordRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "DEFAULT_CURRENCY",
    "DEFAULT_CURRENCIES",
]
