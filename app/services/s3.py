import aioboto3
from app.core.settings import settings
from fastapi import UploadFile
import uuid
import os

class S3Service:
    def __init__(self):
        self.session = aioboto3.Session()
        self.bucket_name = settings.s3_bucket_name
        self.region = settings.s3_region
        self.access_key = settings.s3_access_key
        self.secret_key = settings.s3_secret_key
        self.endpoint_url = settings.s3_endpoint_url

    async def upload_file(self, file: UploadFile) -> str:
        """Uploads a file to S3 and returns the URL."""
        # If in development and S3 not fully configured, skip and let the router handle local fallback
        if settings.app_env == "development" and not (self.access_key and self.secret_key and self.bucket_name):
            print(f"DEBUG: S3 not configured, skipping S3 upload for {file.filename}")
            raise Exception("S3 not configured")

        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        try:
            async with self.session.client(
                "s3",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url
            ) as s3:
                await s3.upload_fileobj(
                    file.file,
                    self.bucket_name,
                    unique_filename,
                    ExtraArgs={"ContentType": file.content_type}
                )
                
            # Return the public URL
            if "amazonaws.com" in self.endpoint_url:
                return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{unique_filename}"
            else:
                return f"{self.endpoint_url}/{self.bucket_name}/{unique_filename}"
        except Exception as e:
            if settings.app_env == "development":
                print(f"DEBUG: S3 upload failed: {str(e)}")
            raise e

    async def get_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Generates a pre-signed URL for a file in S3."""
        if not file_key:
            return ""
        
        # If the file_key is already a full URL, we might need to extract the key
        # But for now, assume file_key is the object key
        if file_key.startswith("http"):
            # Extract key from URL if it's our bucket URL
            if f"{self.bucket_name}.s3" in file_key:
                file_key = file_key.split("/")[-1]
            elif self.endpoint_url in file_key:
                file_key = file_key.split("/")[-1]

        try:
            async with self.session.client(
                "s3",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url
            ) as s3:
                url = await s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": file_key
                    },
                    ExpiresIn=expires_in
                )
                return url
        except Exception as e:
            if settings.app_env == "development":
                print(f"DEBUG: Failed to generate presigned URL: {str(e)}")
            return ""

s3_service = S3Service()
