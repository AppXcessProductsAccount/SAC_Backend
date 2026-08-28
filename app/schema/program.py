from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.models.registration import MealPreference, RegistrationStatus, PaymentStatus
from app.schema.phone import OptionalPhoneNumber, PhoneNumber

class ProgramBase(BaseModel):
    program_name: Optional[str] = None
    city: str
    address: str
    class_id: str
    date_range: str
    is_active: bool = True
    order_id: int = 0
    languages: Optional[List[str]] = []
    discovery_sources: Optional[List[str]] = []

    # Pricing and Payment Policy
    price: float = 0.0
    is_refundable: bool = True
    refund_percentage: float = 100.0
    allow_partial_payment: bool = False
    minimum_deposit: float = 0.0
    balance_due_days: int = 7
    currency: str = "MYR"

    @field_validator("languages", "discovery_sources", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        return v

class ProgramCreate(ProgramBase):
    pass

class ProgramUpdate(BaseModel):
    program_name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    class_id: Optional[str] = None
    date_range: Optional[str] = None
    is_active: Optional[bool] = None
    order_id: Optional[int] = None
    languages: Optional[List[str]] = None
    discovery_sources: Optional[List[str]] = None
    price: Optional[float] = None
    is_refundable: Optional[bool] = None
    refund_percentage: Optional[float] = None
    allow_partial_payment: Optional[bool] = None
    minimum_deposit: Optional[float] = None
    balance_due_days: Optional[int] = None
    currency: Optional[str] = None

class ProgramResponse(ProgramBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class RegistrationCreate(BaseModel):
    nric_last_4: str = Field(..., min_length=4, max_length=4)
    preferred_language: str
    meal_preference: MealPreference
    health_issues: str = "NA"
    referred_by: Optional[str] = None
    introducer_name: Optional[str] = None
    # Checked against the number's own country's rules and stored as E.164.
    # `RegistrationResponse` below is deliberately left as plain `str`: it
    # serialises existing rows, some of which predate this validation.
    introducer_phone: OptionalPhoneNumber = None
    emergency_contact_name: str
    emergency_contact_phone: PhoneNumber
    emergency_contact_relation: str
    discovery_source: str
    pay_full: bool = True # User choice: full or deposit

class RegistrationResponse(BaseModel):
    id: UUID
    user_id: UUID
    program_id: UUID
    nric_last_4: str
    preferred_language: str
    meal_preference: MealPreference
    health_issues: str
    referred_by: Optional[str] = None
    introducer_name: Optional[str] = None
    introducer_phone: Optional[str] = None
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relation: str
    discovery_source: str
    status: RegistrationStatus
    amount_paid: float
    balance_amount: float
    payment_status: PaymentStatus
    due_date: Optional[datetime] = None
    payment_url: Optional[str] = None
    payment_request_id: Optional[str] = None
    hitpay_payment_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ProgramWithRegistrations(ProgramResponse):
    registrations: List[RegistrationResponse] = []
