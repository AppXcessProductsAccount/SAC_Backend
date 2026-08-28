from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.contact import ContactService
from app.schema.contact import ContactCreate, ContactSchema
from typing import List, Annotated
from app.core.deps import RoleChecker
from app.models.user import UserRole

router = APIRouter(prefix="/contacts", tags=["contacts"])
super_admin_only = RoleChecker([UserRole.SUPER_ADMIN])

@router.post("/", response_model=dict)
@router.post("", response_model=dict, include_in_schema=False)
async def create_contact(data: ContactCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    """Public route to submit a contact form."""
    contact = await ContactService.create_contact(db, data)
    return {
        "status": "success",
        "message": "Thank you for contacting us! We have received your message and will get back to you soon.",
        "data": ContactSchema.from_orm(contact)
    }

@router.get("/admin/list", response_model=List[ContactSchema], dependencies=[Depends(super_admin_only)])
async def list_contacts(db: Annotated[AsyncSession, Depends(get_db)]):
    """Admin route to list all contact submissions."""
    return await ContactService.get_all_contacts(db)
