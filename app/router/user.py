from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional

from datetime import date
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, Gender
from app.schema.auth import UserResponse
from app.schema.email import validate_email_address
from app.schema.phone import validate_phone
from app.services.s3 import s3_service

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user's profile details."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    full_name: Annotated[Optional[str], Form()] = None,
    nickname: Annotated[Optional[str], Form()] = None,
    email: Annotated[Optional[str], Form()] = None,
    phone_number: Annotated[Optional[str], Form()] = None,
    gender: Annotated[Optional[Gender], Form()] = None,
    dob: Annotated[Optional[date], Form()] = None,
    occupation: Annotated[Optional[str], Form()] = None,
    address: Annotated[Optional[str], Form()] = None,
    avatar: Annotated[Optional[UploadFile], File()] = None
):
    """Update current user's profile and optionally upload a new avatar."""
    if full_name is not None:
        current_user.full_name = full_name
    if nickname is not None:
        current_user.nickname = nickname
    if email is not None:
        # Same gap as the phone number: these arrive as multipart Form() values,
        # so no schema has judged them. Without this the profile page was the one
        # way into the database that accepted "abc@abc".
        try:
            current_user.email = validate_email_address(email)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from None
    if phone_number is not None:
        # This route takes its fields as multipart Form() values rather than
        # through a schema, so the shared check runs by hand here; otherwise the
        # profile page would be the one way into the database that skips it.
        try:
            current_user.phone_number = validate_phone(phone_number)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from None
    if gender is not None:
        current_user.gender = gender
    if dob is not None:
        current_user.dob = dob
    if occupation is not None:
        current_user.occupation = occupation
    if address is not None:
        current_user.address = address
    
    if avatar:
        url = await s3_service.upload_file(avatar)
        current_user.profile_image_url = url

    # Both columns are nullable, and both are a way of signing in. Clearing the
    # last one leaves an account nobody can get back into, so it is refused here
    # rather than discovered at the next login.
    if not current_user.email and not current_user.phone_number:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Keep either an email address or a phone number on your account — it is how you sign in.",
        )

    await db.commit()
    await db.refresh(current_user)
    return current_user
