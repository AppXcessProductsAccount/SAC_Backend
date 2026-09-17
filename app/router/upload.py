import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid

from app.services.s3 import s3_service
from app.core.settings import settings

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = "uploads"

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("")
async def upload_file(file: UploadFile = File(...)):
    # Check if S3 is configured
    if settings.s3_access_key and settings.s3_secret_key:
        try:
            url = await s3_service.upload_file(file)
            return {"url": url}
        except Exception as e:
            # In development, don't fail, just fallback to local
            if settings.app_env == "development":
                print(f"DEBUG: S3 upload failed, falling back to local: {str(e)}")
            else:
                raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")
    
    # Fallback to local storage
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # The multipart parser leaves the spooled file's cursor at the end, so
        # rewind before copying — otherwise a 0-byte file is written.
        file.file.seek(0)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file locally: {str(e)}")

    return {"url": f"/uploads/{unique_filename}"}

@router.post("/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    urls = []
    for file in files:
        if settings.s3_access_key and settings.s3_secret_key:
            try:
                url = await s3_service.upload_file(file)
                urls.append(url)
                continue
            except Exception as e:
                if settings.app_env == "development":
                    print(f"DEBUG: S3 upload failed for {file.filename}, falling back to local: {str(e)}")
                pass # Try local fallback
                
        # Local fallback
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        try:
            file.file.seek(0)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            urls.append(f"/uploads/{unique_filename}")
        except Exception:
            continue
            
    return {"urls": urls}
