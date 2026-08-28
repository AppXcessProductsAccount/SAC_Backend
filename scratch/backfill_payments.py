import asyncio
from sqlalchemy import select
from app.core.database import DBSessionManager
from app.models.registration import ProgramRegistration
from app.models.payment import Payment

async def backfill_payment_metadata():
    async with DBSessionManager.session() as db:
        try:
            # Get all registrations
            result = await db.execute(select(ProgramRegistration))
            registrations = result.scalars().all()
            
            print(f"Found {len(registrations)} registrations to check.")
            
            updated_count = 0
            for reg in registrations:
                # Find the latest payment for this registration
                payment_result = await db.execute(
                    select(Payment)
                    .where(Payment.registration_id == reg.id)
                    .order_by(Payment.created_at.desc())
                )
                latest_payment = payment_result.scalars().first()
                
                if latest_payment:
                    # Update registration metadata if null
                    if not reg.hitpay_payment_id:
                        reg.hitpay_payment_id = latest_payment.hitpay_payment_id
                    if not reg.payment_url:
                        reg.payment_url = latest_payment.payment_url
                    if not reg.payment_request_id and latest_payment.hitpay_payment_id:
                        reg.payment_request_id = latest_payment.hitpay_payment_id
                    
                    updated_count += 1
            
            await db.commit()
            print(f"Successfully backfilled metadata for {updated_count} registrations.")
            
        except Exception as e:
            print(f"Error during backfill: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(backfill_payment_metadata())
