import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, Boolean, Enum as SQLAlchemyEnum, Date, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

from . import Base


class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    USER = "USER"


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True, unique=True, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), index=True, unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(SQLAlchemyEnum(UserRole), default=UserRole.USER)
    gender: Mapped[Gender | None] = mapped_column(SQLAlchemyEnum(Gender), nullable=True)
    dob: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    @hybrid_property
    def age(self) -> int | None:
        if self.dob:
            today = datetime.now().date()
            return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return None
