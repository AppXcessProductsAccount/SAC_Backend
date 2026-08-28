from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Annotated, List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.deps import RoleChecker
from app.models.user import UserRole
from app.models.membership import Membership
from app.models.membership_registration import MembershipRegistration
from app.schema.membership import (
    MembershipCreate, 
    MembershipUpdate, 
    MembershipResponse,
    MembershipRegistrationResponse
)

router = APIRouter(prefix="/admin/memberships", tags=["admin-memberships"])

# Only Admins and Super Admins can manage memberships
admin_only = Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPER_ADMIN]))

@router.post("/", response_model=MembershipResponse, dependencies=[admin_only])
async def create_membership(
    data: MembershipCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Create a new membership template."""
    new_membership = Membership(**data.model_dump())
    db.add(new_membership)
    await db.commit()
    await db.refresh(new_membership)
    return new_membership

@router.put("/{membership_id}", response_model=MembershipResponse, dependencies=[admin_only])
async def update_membership(
    membership_id: UUID,
    data: MembershipUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update details of an existing membership."""
    membership = await db.get(Membership, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(membership, field, value)
    
    await db.commit()
    await db.refresh(membership)
    return membership

@router.get("/", response_model=List[MembershipResponse], dependencies=[admin_only])
async def list_all_memberships(db: Annotated[AsyncSession, Depends(get_db)]):
    """List all memberships."""
    result = await db.execute(select(Membership).order_by(Membership.created_at.desc()))
    return result.scalars().all()

@router.get("/applications", response_model=List[MembershipRegistrationResponse], dependencies=[admin_only])
async def list_membership_applications(
    db: Annotated[AsyncSession, Depends(get_db)],
    membership_id: Optional[UUID] = None
):
    """List all membership applications."""
    query = select(MembershipRegistration).options(selectinload(MembershipRegistration.membership))
    if membership_id:
        query = query.where(MembershipRegistration.membership_id == membership_id)
    
    query = query.order_by(MembershipRegistration.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.patch("/applications/{application_id}/status", response_model=MembershipRegistrationResponse, dependencies=[admin_only])
async def update_application_status(
    application_id: UUID,
    status: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update status of a membership application."""
    query = (
        select(MembershipRegistration)
        .where(MembershipRegistration.id == application_id)
        .options(selectinload(MembershipRegistration.membership))
    )
    result = await db.execute(query)
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = status
    await db.commit()
    await db.refresh(application)
    return application

@router.delete("/{membership_id}", dependencies=[admin_only])
async def delete_membership(
    membership_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Delete a membership."""
    membership = await db.get(Membership, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    await db.delete(membership)
    await db.commit()
    return {"message": "Membership deleted successfully"}
