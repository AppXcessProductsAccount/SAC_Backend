from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schema.auth import (
    LoginRequest, LoginResponse, OTPRequest, OTPVerify, RefreshRequest, Token, UserResponse
)
from app.schema.settings import (
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest
)
from app.services.auth_service import auth_service
from app.core.deps import get_current_user
from app.models.otp import OTPPurpose
from app.models.user import User
from typing import Annotated

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/send-otp")
async def send_otp(data: OTPRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    success = await auth_service.send_otp(db, data.email, OTPPurpose.LOGIN)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )
    return {"message": "OTP sent successfully"}

@router.post("/verify-otp", response_model=LoginResponse)
async def verify_otp(data: OTPVerify, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await auth_service.verify_otp(db, data.email, data.otp, OTPPurpose.LOGIN)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP"
        )
    
    access_token, refresh_token = await auth_service.create_session(db, user.id)
    await db.refresh(user)
    
    return {
        "message": "Login successful",
        "user": user,
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(data: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """Issue a new access token from a still-valid refresh token."""
    access_token = await auth_service.refresh_access_token(db, data.refresh_token)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # The refresh token is not rotated: two tabs refreshing at once must both keep working.
    return {"access_token": access_token, "refresh_token": data.refresh_token}

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await auth_service.login_admin(db, data.email, data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token, refresh_token = await auth_service.create_session(db, user.id)
    await db.refresh(user)
    
    return {
        "message": "Login successful",
        "user": user,
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    }


@router.post("/change-password", response_model=Token)
async def change_password(
    data: ChangePasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Change the signed-in admin's password.

    Changing a password revokes every session it authorised, so the caller is
    handed a fresh token pair — otherwise the admin would be signed out by their
    own successful password change, which reads as a failure.
    """
    ok, message = await auth_service.change_password(
        db, user, data.current_password, data.new_password
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    access_token, refresh_token = await auth_service.create_session(db, user.id)
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Start a password reset.

    The answer is the same whether or not the address belongs to an admin
    account. Saying "no such account" here would let anyone use this form to
    enumerate who has access to the panel.
    """
    await auth_service.send_password_reset_otp(db, data.email)
    return {
        "message": "If that email belongs to an admin account, a reset code is on its way."
    }


@router.post("/reset-password", response_model=LoginResponse)
async def reset_password(
    data: ResetPasswordRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Redeem a reset code, set the new password, and sign the admin straight in."""
    user = await auth_service.reset_password(db, data.email, data.otp, data.new_password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That code is invalid or has expired. Request a new one.",
        )

    access_token, refresh_token = await auth_service.create_session(db, user.id)
    await db.refresh(user)

    return {
        "message": "Password updated",
        "user": user,
        "tokens": {"access_token": access_token, "refresh_token": refresh_token},
    }
