import asyncio
import os
import sys

# Add the current directory to sys.path to import app
sys.path.append(os.getcwd())

from app.services.hitpay import hitpay_service
from app.core.settings import settings

async def test_hitpay():
    print(f"API Key: {settings.hitpay_api_key}")
    print(f"Salt: {settings.hitpay_salt}")
    print(f"Is Test: {settings.hitpay_is_test}")
    print(f"Base URL: {hitpay_service.base_url}")
    
    # Try to create a payment request
    resp = await hitpay_service.create_payment_request(
        amount=10.0,
        currency="MYR",
        email="test@example.com",
        webhook_url="https://example.com/webhook",
        redirect_url="https://example.com/redirect",
        reference_number="TEST-SIG-123",
        name="Test User"
    )
    
    if resp:
        print("\n--- HitPay Success ---")
        payment_request_id = resp.get("id")
        payment_url = resp.get("url")
        print(f"Payment ID: {payment_request_id}")
        print(f"Payment URL: {payment_url}")
        
        # Generate signature
        signature = hitpay_service.generate_signature(payment_request_id)
        print(f"Generated Signature: {signature}")
    else:
        print("\n--- HitPay Failed ---")

if __name__ == "__main__":
    asyncio.run(test_hitpay())
