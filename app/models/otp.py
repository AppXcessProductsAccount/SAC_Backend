import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, Boolean, Enum as SQLAlchemyEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from . import Base


class OTPPurpose(str, Enum):
    LOGIN = "LOGIN"
    SIGNUP = "SIGNUP"
    # Password resets go through the same table as login codes, but must be
    # scoped: a code mailed for a reset must not also unlock a login, and a
    # login code must not be redeemable as proof for setting a new password.
    PASSWORD_RESET = "PASSWORD_RESET"


class OTPCode(Base):
    __tablename__ = "otp_codes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    otp_code: Mapped[str] = mapped_column(String(255))  # Hashed OTP preferred, but for now simple
    purpose: Mapped[OTPPurpose] = mapped_column(SQLAlchemyEnum(OTPPurpose))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
