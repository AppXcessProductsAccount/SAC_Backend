from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
    
    debug: bool = False
    app_env: str = "development"
    cors_origins: list[str] = ["*"]
    
    # Admin settings
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"
    
    # Base URLs
    app_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    
    # S3 settings
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = ""
    s3_region: str = "us-east-1"
    s3_endpoint_url: str = "https://s3.amazonaws.com"

    # JWT settings
    secret_key: str = "your-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # AWS SES settings
    aws_ses_region: str = "us-east-1"
    aws_ses_sender_email: str = "noreply@example.com"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # HitPay Settings
    hitpay_api_key: str = ""
    hitpay_salt: str = ""
    hitpay_x_business_name: str = "Self Awareness Meditation"
    hitpay_is_test: bool = True

settings = Settings()
