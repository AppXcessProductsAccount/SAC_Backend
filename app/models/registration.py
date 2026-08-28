import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models import Base

class MealPreference(str, Enum):
    VEGETARIAN = "Vegetarian"
    NON_VEGETARIAN = "Non-Vegetarian"

class RegistrationStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"

class PaymentStatus(str, Enum):
    PENDING = "Pending"
    PARTIAL = "Partial"
    COMPLETED = "Completed"
    FAILED = "Failed"
    REFUNDED = "Refunded"

class ProgramRegistration(Base):
    __tablename__ = "program_registrations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"), index=True)
    
    # Custom fields
    nric_last_4: Mapped[str] = mapped_column(String(4))
    preferred_language: Mapped[str] = mapped_column(String(50))
    meal_preference: Mapped[MealPreference] = mapped_column(SQLAlchemyEnum(MealPreference))
    health_issues: Mapped[str] = mapped_column(Text, default="NA")
    referred_by: Mapped[str | None] = mapped_column(String(255), nullable=True) # General referral info
    introducer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    introducer_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Emergency Contact
    emergency_contact_name: Mapped[str] = mapped_column(String(255))
    emergency_contact_phone: Mapped[str] = mapped_column(String(20))
    emergency_contact_relation: Mapped[str] = mapped_column(String(100))
    
    discovery_source: Mapped[str] = mapped_column(String(255)) # How you know about us
    status: Mapped[RegistrationStatus] = mapped_column(SQLAlchemyEnum(RegistrationStatus), default=RegistrationStatus.PENDING)
    
    # Payment Tracking
    amount_paid: Mapped[float] = mapped_column(default=0.0)
    balance_amount: Mapped[float] = mapped_column(default=0.0)
    payment_status: Mapped[PaymentStatus] = mapped_column(SQLAlchemyEnum(PaymentStatus), default=PaymentStatus.PENDING)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # HitPay Metadata
    payment_request_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hitpay_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="registrations")
    program = relationship("Program", backref="registrations")
