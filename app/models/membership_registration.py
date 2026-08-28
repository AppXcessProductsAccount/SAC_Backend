import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import sqlalchemy as sa
from app.models import Base

class MembershipRegistration(Base):
    __tablename__ = "membership_registrations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    membership_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("memberships.id", ondelete="CASCADE"), index=True)
    
    # Selected options
    attended_programs: Mapped[list | None] = mapped_column(sa.JSON, default=list) # List of selected program names
    membership_type: Mapped[str] = mapped_column(String(255))
    monthly_contribution: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Dynamic answers to custom questions
    # Example: {"How much would you like to contribute?": "I will donate 50"}
    custom_answers: Mapped[dict | None] = mapped_column(sa.JSON, default=dict)
    
    # Interests
    interests: Mapped[list | None] = mapped_column(sa.JSON, default=list)
    
    # Terms Agreement
    agreed_to_terms: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="Pending") # Pending, Approved, Rejected
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="membership_registrations")
    membership = relationship("Membership", backref="registrations")
