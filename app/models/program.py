import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import String, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models import Base

class Program(Base):
    __tablename__ = "programs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    program_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    address: Mapped[str] = mapped_column(Text)
    class_id: Mapped[str] = mapped_column(String(50), index=True) # e.g., C1006
    date_range: Mapped[str] = mapped_column(String(100)) # e.g., 20 – 26 April 2026
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    order_id: Mapped[int] = mapped_column(default=0)
    
    # Dynamic options for registration
    languages: Mapped[list | None] = mapped_column(sa.JSON, default=list) # e.g., ["English", "Tamil"]
    discovery_sources: Mapped[list | None] = mapped_column(sa.JSON, default=list) # e.g., ["TikTok", "Instagram"]
    
    # Pricing and Payment Policy
    price: Mapped[float] = mapped_column(default=0.0) # Total cost in RM
    is_refundable: Mapped[bool] = mapped_column(Boolean, default=True)
    refund_percentage: Mapped[float] = mapped_column(default=100.0)
    allow_partial_payment: Mapped[bool] = mapped_column(Boolean, default=False)
    minimum_deposit: Mapped[float] = mapped_column(default=0.0)
    balance_due_days: Mapped[int] = mapped_column(default=7) # Days to pay the rest
    currency: Mapped[str] = mapped_column(String(10), default="MYR") # e.g., MYR, SGD
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
