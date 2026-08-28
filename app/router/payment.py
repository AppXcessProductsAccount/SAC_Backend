from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.program import Program
from app.models.payment import Payment
from app.models.registration import ProgramRegistration, PaymentStatus
from app.services.hitpay import hitpay_service
from app.core.settings import settings

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/pay-balance/{registration_id}")
async def pay_balance(
    registration_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Initiate a payment for the remaining balance of a registration.
    """
    # Find the registration and ensure it belongs to the current user
    result = await db.execute(
        select(ProgramRegistration)
        .where(ProgramRegistration.id == registration_id)
        .where(ProgramRegistration.user_id == current_user.id)
    )
    registration = result.scalars().first()
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    if registration.balance_amount <= 0:
        raise HTTPException(status_code=400, detail="No balance amount remaining to pay")
    
    # Get program details for the name
    program = await db.get(Program, registration.program_id)
    program_name = program.program_name if program else "Meditation Program"

    # Initiate HitPay for the balance
    ref_no = f"BAL-{str(registration.id)[:8]}-{int(datetime.now().timestamp())}"
    
    hitpay_resp = await hitpay_service.create_payment_request(
        amount=registration.balance_amount,
        currency=program.currency if program else "MYR",
        email=current_user.email,
        name=current_user.full_name or current_user.nickname,
        phone=current_user.phone_number or "",
        address=current_user.address or "",
        webhook_url=f"{settings.app_url}/api/payments/webhook",
        redirect_url=f"{settings.frontend_url}/payment/success?reg_id={registration.id}",
        reference_number=ref_no
    )
    
    if not hitpay_resp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to initiate payment with HitPay. Please check if HitPay API keys are configured correctly in the .env file."
        )
        
    payment_url = hitpay_resp.get("url")
    payment_request_id = hitpay_resp.get("id")
    payment_signature = hitpay_service.generate_signature(payment_request_id)
    
    # Create Payment record
    new_payment = Payment(
        registration_id=registration.id,
        hitpay_payment_id=payment_request_id,
        payment_url=payment_url,
        amount=registration.balance_amount,
        currency=program.currency if program else "MYR",
        external_reference=ref_no,
        status="pending"
    )
    db.add(new_payment)
    await db.commit()
    
    return {
        "payment_url": payment_url,
        "payment_request_id": payment_request_id,
        "payment_signature": payment_signature
    }

@router.post("/webhook")
async def hitpay_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    hitpay_signature: Annotated[str | None, Header()] = None
):
    """
    Handle HitPay webhook callbacks to update payment and registration status.
    """
    if not hitpay_signature:
        raise HTTPException(status_code=400, detail="Missing HitPay signature")

    # Verify signature using raw body
    raw_body = await request.body()
    if not hitpay_service.verify_webhook_signature(raw_body, hitpay_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse payload
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        data = await request.json()
    else:
        form_data = await request.form()
        data = dict(form_data)
        
    print(f"DEBUG: Webhook Data: {data}")
    
    payment_request_id = data.get("payment_request_id")
    payment_id = data.get("payment_id") or data.get("id")
    status = data.get("status") # completed, succeeded, failed, etc.
    amount = float(data.get("amount", 0))
    payment_method = data.get("payment_method")
    currency = data.get("currency")
    
    # Fallback: if payment_method is null, fetch details from HitPay API
    # We should use payment_request_id to fetch details from HitPay
    hitpay_details = None
    if not payment_method and payment_request_id:
        hitpay_details = await hitpay_service.get_payment_request(payment_request_id)
        if hitpay_details:
            # Check for payment method in details
            # HitPay sometimes nests this in a 'payments' list
            payments = hitpay_details.get("payments", [])
            if payments and isinstance(payments, list) and len(payments) > 0:
                payment_method = (
                    payments[0].get("payment_type") or 
                    payments[0].get("method") or
                    payments[0].get("payment_method")
                )
                # Check for nested charge object
                if not payment_method and "payment_provider" in payments[0]:
                    provider = payments[0].get("payment_provider", {})
                    charge = provider.get("charge", {})
                    payment_method = charge.get("method")
            else:
                payment_method = hitpay_details.get("payment_type") or hitpay_details.get("method")
                # Check top level payment_provider (from user's JSON)
                if not payment_method and "payment_provider" in hitpay_details:
                    provider = hitpay_details.get("payment_provider", {})
                    charge = provider.get("charge", {})
                    payment_method = charge.get("method")

    # If still not found, check the webhook payload 'data' itself for nested structure
    # (Sometimes webhooks send the full object)
    if not payment_method:
        if "payment_provider" in data:
            provider = data.get("payment_provider", {})
            charge = provider.get("charge", {})
            payment_method = charge.get("method")
        elif "payments" in data and isinstance(data["payments"], list) and len(data["payments"]) > 0:
            p0 = data["payments"][0]
            payment_method = p0.get("payment_type") or p0.get("method")
            if not payment_method and "payment_provider" in p0:
                payment_method = p0.get("payment_provider", {}).get("charge", {}).get("method")

    # Find the payment record
    # Primary lookup using payment_request_id (as we store the request ID in hitpay_payment_id)
    payment = None
    if payment_request_id:
        result = await db.execute(select(Payment).where(Payment.hitpay_payment_id == payment_request_id))
        payment = result.scalars().first()
    
    if not payment and payment_id:
        # Fallback to finding by payment_id
        result = await db.execute(select(Payment).where(Payment.hitpay_payment_id == payment_id))
        payment = result.scalars().first()
        
    if not payment:
        # Final fallback: try finding by external reference
        ref = data.get("reference_number")
        if ref:
            result = await db.execute(select(Payment).where(Payment.external_reference == ref))
            payment = result.scalars().first()

    if not payment:
        return {"message": "Payment record not found"}

    if payment.status == "completed" or payment.status == "succeeded":
        return {"message": "Already processed"}

    # Update payment status and method
    payment.status = status
    if payment_method:
        payment.payment_method = str(payment_method)
    if currency:
        payment.currency = currency
    
    if status == "completed" or status == "succeeded":
        # Ensure status is normalized to 'completed' for our internal tracking if needed,
        # or just keep what HitPay sent.
        payment.status = "completed"
        
        # Update registration status
        result = await db.execute(select(ProgramRegistration).where(ProgramRegistration.id == payment.registration_id))
        registration = result.scalars().first()
        
        if registration:
            registration.amount_paid += amount
            registration.balance_amount -= amount
            registration.hitpay_payment_id = payment_id # Store the specific transaction ID
            
            if registration.balance_amount <= 0:
                registration.payment_status = PaymentStatus.COMPLETED
                from app.models.registration import RegistrationStatus # Ensure imported
                registration.status = RegistrationStatus.CONFIRMED # Sync status
                registration.balance_amount = 0 # Ensure no negative balance
            else:
                registration.payment_status = PaymentStatus.PARTIAL
    elif status == "failed":
        payment.status = "failed"
    
    await db.commit()
    return {"message": "Webhook processed successfully"}
