import hmac
import hashlib
import httpx
from typing import Optional, Dict, Any
from app.core.settings import settings

class HitPayService:
    def __init__(self):
        self.api_key = settings.hitpay_api_key
        self.salt = settings.hitpay_salt
        self.base_url = "https://api.sandbox.hit-pay.com/v1" if settings.hitpay_is_test else "https://api.hit-pay.com/v1"
        self.headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-BUSINESS-NAME": settings.hitpay_x_business_name,
            "X-BUSINESS-API-KEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }

    async def create_payment_request(
        self, 
        amount: float, 
        currency: str, 
        email: str, 
        webhook_url: str,
        redirect_url: str,
        reference_number: str,
        name: str = "",
        phone: str = "",
        address: str = "",
        city: str = "",
        state: str = "",
        country: str = "",
        postal_code: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Creates a payment request and returns the HitPay response including payment_url.
        """
        # Fetch latest settings
        api_key = settings.hitpay_api_key
        
        # HitPay expects amount as a number with 2 decimal places usually
        data = {
            "amount": round(amount, 2),
            "currency": currency,
            "email": email,
            "name": name,
            "phone": phone,
            "webhook": webhook_url,
            "redirect_url": redirect_url,
            "reference_number": reference_number
        }
        
        # Address fields must be sent in a specific format and require line1, city, country
        if address and city and country:
            data["address[line1]"] = address
            data["address[city]"] = city
            if state:
                data["address[state]"] = state
            data["address[country]"] = country
            if postal_code:
                data["address[postal_code]"] = postal_code
        elif address:
            # If only a general address string is provided, we might try to put it in line1
            # but HitPay requires city and country too. To avoid 422 error, we skip it
            # unless we have the required components.
            pass
        
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-BUSINESS-NAME": settings.hitpay_x_business_name,
            "X-BUSINESS-API-KEY": api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        print(f"DEBUG: Sending to HitPay: {data}")
        print(f"DEBUG: URL: {self.base_url}/payment-requests")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/payment-requests",
                    data=data,
                    headers=headers
                )
                if response.status_code != 201 and response.status_code != 200:
                    print(f"HitPay Error Status: {response.status_code}")
                    print(f"HitPay Error Response: {response.text}")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"HitPay Exception: {str(e)}")
                return None

    def generate_signature(self, payment_request_id: str) -> str:
        """
        Generates a signature for the payment request ID using the salt.
        This is used by the frontend JS SDK to authorize the Payment Element.
        """
        if not self.salt:
            return ""
            
        return hmac.new(
            self.salt.encode('utf-8'),
            payment_request_id.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def verify_webhook_signature(self, raw_payload: bytes, signature: str) -> bool:
        """
        Verifies the HitPay webhook signature using HMAC-SHA256 and salt.
        """
        if not self.salt:
            return False
            
        computed_signature = hmac.new(
            self.salt.encode('utf-8'),
            raw_payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)

    async def get_payment_request(self, payment_request_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the details of a payment request from HitPay.
        """
        api_key = settings.hitpay_api_key
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "X-BUSINESS-API-KEY": api_key,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/payment-requests/{payment_request_id}",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"HitPay Get Error: {str(e)}")
                return None

hitpay_service = HitPayService()
