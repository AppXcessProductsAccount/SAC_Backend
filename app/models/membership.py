import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import String, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models import Base

class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Dynamic options for the application form
    
    # Field 2: Programs you have attended under SAC (Dynamic Options)
    # Example: ["7DTJ", "Enhance Prosperity and Abundance", "Other"]
    attended_programs_options: Mapped[list | None] = mapped_column(sa.JSON, default=list)
    
    # Field 3: Membership type (Dynamic Options with Prices)
    # Example: [{"name": "Principle", "price": 25, "allow_donation": true}, {"name": "Student", "price": 15}]
    membership_types: Mapped[list | None] = mapped_column(sa.JSON, default=list)
    
    # Field 5: Custom Questions (Dynamic)
    # Example: [{"question": "How much would you like to contribute?", "type": "text"}]
    custom_questions: Mapped[list | None] = mapped_column(sa.JSON, default=list)
    
    # Field 6: Your Interests Matter (Dynamic Options)
    # Example: ["Movies", "Dance & Music", "Other"]
    interest_options: Mapped[list | None] = mapped_column(sa.JSON, default=list)
    
    # Field 7: Terms and Conditions
    terms_and_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
