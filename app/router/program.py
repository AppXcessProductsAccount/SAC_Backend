from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated, List
from uuid import UUID
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.program import Program
from app.models.registration import ProgramRegistration, RegistrationStatus, PaymentStatus
from app.models.payment import Payment
from app.services.hitpay import hitpay_service
from app.core.settings import settings
from app.schema.program import ProgramResponse, RegistrationCreate, RegistrationResponse

router = APIRouter(prefix="/programs", tags=["programs"])

@router.get("/", response_model=List[ProgramResponse])
async def list_active_programs(db: Annotated[AsyncSession, Depends(get_db)]):
    """List all active programs available for registration."""
    result = await db.execute(
        select(Program)
        .where(Program.is_active == True)
        .order_by(Program.order_id.asc())
    )
    return result.scalars().all()

@router.post("/{program_id}/register", response_model=RegistrationResponse)
async def register_for_program(
    program_id: UUID,
    data: RegistrationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Register the current user for a specific program and initiate payment."""
    # ... (Profile validation same as before) ...
    required_fields = [
        current_user.full_name, current_user.nickname, current_user.gender,
        current_user.dob, current_user.occupation, current_user.address, current_user.phone_number
    ]
    if any(field in [None, ""] for field in required_fields):
        raise HTTPException(status_code=400, detail={"message": "Complete profile first", "profile_setup": False})

    if data.discovery_source == "Introducer" and (not data.introducer_name or not data.introducer_phone):
        raise HTTPException(status_code=400, detail="Introducer details required")

    program = await db.get(Program, program_id)
    if not program or not program.is_active:
        raise HTTPException(status_code=404, detail="Program not found or inactive")
    
    # Temporarily disabled duplicate check to allow multiple registrations per user
    # existing = await db.execute(select(ProgramRegistration).where(
    #     ProgramRegistration.user_id == current_user.id, ProgramRegistration.program_id == program_id
    # ))
    # if existing.scalars().first():
    #     raise HTTPException(status_code=400, detail="Already registered")
    
    # Calculate Payment Logic
    total_price = program.price
    amount_to_pay = total_price
    is_partial = False
    
    if not data.pay_full and program.allow_partial_payment:
        amount_to_pay = program.minimum_deposit
        is_partial = True
    
    balance = total_price - amount_to_pay
    due_date = None
    if balance > 0:
        due_date = datetime.now() + timedelta(days=program.balance_due_days)

    # Remove pay_full from data before passing to model
    reg_data = data.model_dump()
    pay_full = reg_data.pop("pay_full", True)

    new_reg = ProgramRegistration(
        user_id=current_user.id,
        program_id=program_id,
        balance_amount=total_price,
        due_date=due_date,
        **reg_data
    )
    db.add(new_reg)
    await db.flush() # Get the new_reg.id

    payment_url = None
    if amount_to_pay > 0:
        # Initiate HitPay
        # Reference number: REG-{reg_id_short}-{timestamp}
        ref_no = f"REG-{str(new_reg.id)[:8]}-{int(datetime.now().timestamp())}"
        
        hitpay_resp = await hitpay_service.create_payment_request(
            amount=amount_to_pay,
            currency=program.currency,
            email=current_user.email,
            name=current_user.full_name or current_user.nickname,
            phone=current_user.phone_number or "",
            address=current_user.address or "",
            webhook_url=f"{settings.app_url}/api/payments/webhook",
            redirect_url=f"{settings.frontend_url}/payment/success?reg_id={new_reg.id}",
            reference_number=ref_no
        )
        
        if not hitpay_resp:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate payment with HitPay. Please check your configuration."
            )
            
        payment_url = hitpay_resp.get("url")
        # Create Payment record
        new_payment = Payment(
            registration_id=new_reg.id,
            hitpay_payment_id=hitpay_resp.get("id"),
            payment_url=payment_url,
            amount=amount_to_pay,
            currency=program.currency,
            external_reference=ref_no,
            status="pending"
        )
        db.add(new_payment)

    await db.commit()
    await db.refresh(new_reg)
    
    if hitpay_resp:
        new_reg.payment_request_id = hitpay_resp.get("id")
        new_reg.payment_url = payment_url
        
    await db.commit()
    await db.refresh(new_reg)
    
    return new_reg

@router.get("/my-registrations", response_model=List[RegistrationResponse])
async def get_my_registrations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get all programs the current user has registered for."""
    result = await db.execute(
        select(ProgramRegistration).where(ProgramRegistration.user_id == current_user.id)
    )
    registrations = result.scalars().all()
    
    # Attach any needed calculated fields for listing
    for reg in registrations:
        if reg.payment_status == PaymentStatus.COMPLETED:
            # Clean up fields for completed payments if you want, 
            # though they are now persisted in DB
            pass
            
    return registrations
