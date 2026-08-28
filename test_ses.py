import asyncio
import sys
import os

# Add the current directory to sys.path to import the app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.email import email_service
from app.core.settings import settings

async def test_ses_connectivity():
    print("--- AWS SES Connectivity Test ---")
    print(f"Region: {settings.aws_ses_region}")
    print(f"Sender: {settings.aws_ses_sender_email}")
    
    if not settings.aws_access_key_id or not settings.aws_secret_access_key:
        print("WARNING: AWS credentials are not set in .env")
    
    # Use command line argument if provided, else use ADMIN_EMAIL from settings
    test_receiver = sys.argv[1] if len(sys.argv) > 1 else settings.admin_email
    
    if not test_receiver:
        print("No recipient provided and ADMIN_EMAIL is not set. Usage: python test_ses.py <email>")
        return

    print(f"Attempting to send test OTP to {test_receiver}...")
    
    try:
        # We use a dummy OTP for testing
        success = await email_service.send_otp_email(test_receiver, "123456")
        
        if success:
            print("\nSUCCESS: Email sent successfully via SES!")
            print("Please check your inbox (and spam folder).")
        else:
            print("\nFAILURE: Failed to send email. Check the logs for details.")
            
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_ses_connectivity())
