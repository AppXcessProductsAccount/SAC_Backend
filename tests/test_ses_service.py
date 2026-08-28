import pytest
from unittest.mock import MagicMock, patch
from app.services.email import EmailService


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_ses_client():

    with patch("boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        yield mock_client


@pytest.mark.anyio
async def test_send_otp_email_success(mock_ses_client):
    mock_ses_client.send_email.return_value = {"MessageId": "test-msg-id-12345"}

    with patch("app.services.email.settings") as mock_settings:
        mock_settings.aws_ses_region = "ap-southeast-1"
        mock_settings.aws_access_key_id = "testing"
        mock_settings.aws_secret_access_key = "testing"
        mock_settings.aws_ses_sender_email = "noreply@example.com"

        email_svc = EmailService()
        result = await email_svc.send_otp_email("user@example.com", "654321")

        assert result is True
        mock_ses_client.send_email.assert_called_once()


@pytest.mark.anyio
async def test_send_otp_email_failure(mock_ses_client):
    mock_ses_client.send_email.side_effect = Exception("AWS SES Error")

    email_svc = EmailService()
    result = await email_svc.send_otp_email("user@example.com", "123456")

    assert result is False

