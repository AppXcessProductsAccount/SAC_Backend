from typing import List, Optional
from sqlalchemy import String, Text, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

class CMSPage(Base):
    __tablename__ = "cms_pages"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    # Relationship
    sections: Mapped[List["Section"]] = relationship(back_populates="page", cascade="all, delete-orphan")

class Section(Base):
    __tablename__ = "sections"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    page_id: Mapped[int | None] = mapped_column(ForeignKey("cms_pages.id", ondelete="CASCADE"), index=True)
    section_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    template_id: Mapped[str] = mapped_column(String(100), default="default")
    content: Mapped[dict] = mapped_column(JSON)

    # Relationship
    page: Mapped[Optional["CMSPage"]] = relationship(back_populates="sections")
