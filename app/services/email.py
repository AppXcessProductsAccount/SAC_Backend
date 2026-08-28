import boto3
from botocore.exceptions import ClientError
from app.core.settings import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.ses_client = boto3.client(
            'ses',
            region_name=settings.aws_ses_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        self.sender = settings.aws_ses_sender_email

    def _send(self, email: str, subject: str, body_text: str, body_html: str) -> bool:
        """One place that talks to SES, so every template gets the same charset
        handling and the same 'log it, do not raise' failure behaviour."""
        try:
            response = self.ses_client.send_email(
                Destination={'ToAddresses': [email]},
                Message={
                    'Body': {
                        'Html': {'Charset': 'UTF-8', 'Data': body_html},
                        'Text': {'Charset': 'UTF-8', 'Data': body_text},
                    },
                    'Subject': {'Charset': 'UTF-8', 'Data': subject},
                },
                Source=self.sender,
            )
            logger.info(f"Email sent! Message ID: {response['MessageId']}")
            return True
        except Exception as e:
            logger.error(f"Error sending email via SES: {str(e)}")
            return False

    async def send_otp_email(self, email: str, otp: str):
        subject = "Your Verification Code"
        body_text = f"Your verification code is: {otp}. It will expire in 10 minutes."
        body_html = f"""
        <html>
        <head></head>
        <body>
          <h1>Verification Code</h1>
          <p>Your verification code is: <strong>{otp}</strong></p>
          <p>It will expire in 10 minutes.</p>
        </body>
        </html>
        """

        try:
            response = self.ses_client.send_email(
                Destination={
                    'ToAddresses': [email],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': 'UTF-8',
                            'Data': body_html,
                        },
                        'Text': {
                            'Charset': 'UTF-8',
                            'Data': body_text,
                        },
                    },
                    'Subject': {
                        'Charset': 'UTF-8',
                        'Data': subject,
                    },
                },
                Source=self.sender,
            )
            logger.info(f"Email sent! Message ID: {response['MessageId']}")
            return True
        except Exception as e:
            logger.error(f"Error sending email via SES: {str(e)}")
            return False

    async def send_password_reset_email(self, email: str, otp: str) -> bool:
        """
        A reset code, worded so it cannot be mistaken for a login code — the two
        arrive from the same address and look alike otherwise.
        """
        subject = "Reset your admin password"
        body_text = (
            f"Your password reset code is: {otp}\n\n"
            "It expires in 10 minutes and can be used once.\n\n"
            "If you did not ask to reset your password, ignore this email — "
            "your password has not been changed."
        )
        body_html = f"""
        <html>
        <head></head>
        <body style="font-family: -apple-system, Segoe UI, Roboto, sans-serif; color: #101848;">
          <h1 style="font-size: 20px;">Reset your admin password</h1>
          <p>Use this code to set a new password:</p>
          <p style="font-size: 32px; font-weight: bold; letter-spacing: 6px;">{otp}</p>
          <p>It expires in 10 minutes and can be used once.</p>
          <hr style="border: none; border-top: 1px solid #eee;" />
          <p style="color: #666; font-size: 13px;">
            If you did not ask to reset your password, ignore this email &mdash;
            your password has not been changed.
          </p>
        </body>
        </html>
        """
        return self._send(email, subject, body_text, body_html)


email_service = EmailService()
