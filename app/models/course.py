from typing import List, Optional
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from . import Base

class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    units: Mapped[List["Unit"]] = relationship(back_populates="course", cascade="all, delete-orphan", order_by="Unit.order")

class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50)) # standard_content, learning_activity, header
    content_subtype: Mapped[str] = mapped_column(String(50)) # text, web_url, video_url, etc.
    content_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_header: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    course: Mapped["Course"] = relationship(back_populates="units")
