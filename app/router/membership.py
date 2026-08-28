from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Annotated, List
from uuid import UUID

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.membership import Membership
from app.models.membership_registration import MembershipRegistration
from app.schema.membership import (
    MembershipResponse,
    MembershipRegistrationCreate,
    MembershipRegistrationResponse
)
from app.services.hitpay import hitpay_service
from app.core.settings import settings

router = APIRouter(prefix="/memberships", tags=["memberships"])

@router.get("/", response_model=List[MembershipResponse])
async def list_active_memberships(db: Annotated[AsyncSession, Depends(get_db)]):
    """List all active memberships."""
    result = await db.execute(
        select(Membership)
        .where(Membership.is_active == True)
        .order_by(Membership.created_at.desc())
    )
    return result.scalars().all()

@router.get("/{membership_id}", response_model=MembershipResponse)
async def get_membership_details(
    membership_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get details of a specific membership."""
    membership = await db.get(Membership, membership_id)
    if not membership or not membership.is_active:
        raise HTTPException(status_code=404, detail="Membership not found")
    return membership

@router.post("/{membership_id}/apply", response_model=MembershipRegistrationResponse)
async def apply_for_membership(
    membership_id: UUID,
    data: MembershipRegistrationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Submit an application for membership."""
    # Check if membership exists and is active
    membership = await db.get(Membership, membership_id)
    if not membership or not membership.is_active:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    
    # Create new registration
    new_reg = MembershipRegistration(
        user_id=current_user.id,
        membership_id=membership_id,
        **data.model_dump()
    )
    
    # Capture user details before commit to avoid lazy loading issues
    user_email = current_user.email
    user_full_name = current_user.full_name

    db.add(new_reg)
    await db.commit()
    await db.refresh(new_reg)
    await db.refresh(membership)
    
    # Create HitPay payment request
    payment_url = None
    if new_reg.monthly_contribution > 0:
        hitpay_resp = await hitpay_service.create_payment_request(
            amount=new_reg.monthly_contribution,
            currency="SGD", # Assuming SGD based on previous Singapore context
            email=user_email,
            webhook_url=f"{settings.app_url}/api/payments/webhook", # Adjust if you have a specific webhook
            redirect_url=f"{settings.frontend_url}/payment-success?type=membership&id={new_reg.id}",
            reference_number=str(new_reg.id),
            name=f"{user_full_name}" if user_full_name else user_email
        )
        if hitpay_resp:
            payment_url = hitpay_resp.get("url")
    
    # Attach membership object to avoid lazy loading error in response model
    new_reg.membership = membership
    
    # We don't store payment_url in DB usually, just return it
    response_data = MembershipRegistrationResponse.model_validate(new_reg)
    response_data.payment_url = payment_url
    
    return response_data

@router.get("/my-applications", response_model=List[MembershipRegistrationResponse])
async def get_my_applications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """List all membership applications for the current user."""
    result = await db.execute(
        select(MembershipRegistration)
        .where(MembershipRegistration.user_id == current_user.id)
        .options(selectinload(MembershipRegistration.membership))
        .order_by(MembershipRegistration.created_at.desc())
    )
    return result.scalars().all()
