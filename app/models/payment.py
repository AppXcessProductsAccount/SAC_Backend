import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models import Base

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    registration_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("program_registrations.id", ondelete="CASCADE"), index=True)
    
    # HitPay specific fields
    hitpay_payment_id: Mapped[str | None] = mapped_column(String(255), index=True)
    payment_url: Mapped[str | None] = mapped_column(String(500))
    
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="MYR")
    status: Mapped[str] = mapped_column(String(50), default="pending") # pending, completed, failed, refunded
    
    payment_method: Mapped[str | None] = mapped_column(String(100))
    external_reference: Mapped[str | None] = mapped_column(String(255)) # Store custom order ID or other ref
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    registration = relationship("ProgramRegistration", backref="payments")
