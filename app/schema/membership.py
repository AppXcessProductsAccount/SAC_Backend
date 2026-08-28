from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any, Dict

# Membership Schemas

class MembershipType(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    allow_donation: bool = False

class CustomQuestion(BaseModel):
    question: str
    type: str # text, select, etc.
    options: Optional[List[str]] = None

class MembershipBase(BaseModel):
    name: str
    is_active: bool = True
    attended_programs_options: List[str] = []
    membership_types: List[MembershipType] = []
    custom_questions: List[CustomQuestion] = []
    interest_options: List[str] = []
    terms_and_conditions: Optional[str] = None

class MembershipCreate(MembershipBase):
    pass

class MembershipUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    attended_programs_options: Optional[List[str]] = None
    membership_types: Optional[List[MembershipType]] = None
    custom_questions: Optional[List[CustomQuestion]] = None
    interest_options: Optional[List[str]] = None
    terms_and_conditions: Optional[str] = None

class MembershipResponse(MembershipBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Registration Schemas

class MembershipRegistrationCreate(BaseModel):
    attended_programs: List[str]
    membership_type: str
    monthly_contribution: float
    custom_answers: Dict[str, Any] = {}
    interests: List[str]
    agreed_to_terms: bool

class MembershipRegistrationResponse(BaseModel):
    id: UUID
    user_id: UUID
    membership_id: UUID
    attended_programs: List[str]
    membership_type: str
    monthly_contribution: float
    custom_answers: Dict[str, Any]
    interests: List[str]
    agreed_to_terms: bool
    status: str
    created_at: datetime
    payment_url: Optional[str] = None
    
    # Optional nested membership for context
    membership: Optional[MembershipResponse] = None

    class Config:
        from_attributes = True
