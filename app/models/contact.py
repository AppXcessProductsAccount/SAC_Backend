from sqlalchemy import Column, Integer, String, Text, DateTime
from . import Base
from datetime import datetime

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
