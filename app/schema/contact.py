from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

from app.schema.phone import OptionalPhoneNumber

class ContactBase(BaseModel):
    full_name: str
    phone: Optional[str] = None
    email: EmailStr
    address: Optional[str] = None
    subject: str
    message: str

class ContactCreate(ContactBase):
    """
    An enquiry submitted from the site's contact form.

    The number is checked here and not on `ContactBase`, because `ContactSchema`
    inherits from that same base to serialise rows back out: validating there
    would re-run the check on every stored enquiry, and one row saved before this
    validation existed would then break the whole admin list.
    """
    phone: OptionalPhoneNumber = None

class ContactSchema(ContactBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
