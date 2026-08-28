import random
import string
from datetime import datetime, timedelta
import uuid
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import delete as sa_delete, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.user import User, UserRole
from app.models.otp import OTPCode, OTPPurpose
from app.models.token import AccessToken, RefreshToken
from app.services.email import email_service

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        # `exp` has one-second resolution, so two tokens minted for the same user
        # inside the same second used to encode identically and collide on the
        # unique index over access_tokens.token. A per-token id keeps them distinct.
        to_encode.update({"exp": expire, "jti": uuid.uuid4().hex})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt, expire

    @staticmethod
    def create_refresh_token(data: dict):
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode = data.copy()
        to_encode.update({"exp": expire, "type": "refresh", "jti": uuid.uuid4().hex})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt, expire

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        return ''.join(random.choices(string.digits, k=length))

    async def send_otp(self, db: AsyncSession, email: str, purpose: OTPPurpose, create_missing: bool = True):
        # Find or create user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if not user:
            # A password reset must never bring an account into existence: that
            # would turn the reset form into an open sign-up and tell the sender
            # which addresses are not registered.
            if not create_missing:
                return False
            user = User(
                full_name=email.split('@')[0],
                email=email,
                role=UserRole.USER,
                is_active=True,
                is_verified=False
            )
            db.add(user)
            await db.flush()

        otp = self.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        otp_record = OTPCode(
            user_id=user.id,
            otp_code=otp, # Should ideally be hashed
            purpose=purpose,
            expires_at=expires_at
        )
        db.add(otp_record)
        await db.commit()

        # Send email
        if purpose == OTPPurpose.PASSWORD_RESET:
            await email_service.send_password_reset_email(email, otp)
        else:
            await email_service.send_otp_email(email, otp)
        return True

    async def verify_otp(self, db: AsyncSession, email: str, otp: str, purpose: OTPPurpose):
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalars().first()
        if not user:
            return None

        result = await db.execute(
            select(OTPCode).where(
                OTPCode.user_id == user.id,
                OTPCode.otp_code == otp,
                OTPCode.purpose == purpose,
                OTPCode.is_used == False,
                OTPCode.expires_at > datetime.utcnow()
            )
        )
        otp_record = result.scalars().first()
        
        if not otp_record:
            return None

        otp_record.is_used = True
        user.is_verified = True
        await db.commit()
        await db.refresh(user)
        return user

    async def login_admin(self, db: AsyncSession, email: str, password: str):
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user or not user.password_hash:
            return None
            
        if not self.verify_password(password, user.password_hash):
            return None
            
        return user

    async def create_session(self, db: AsyncSession, user_id: uuid.UUID):
        access_token_str, access_expire = self.create_access_token({"sub": str(user_id)})
        refresh_token_str, refresh_expire = self.create_refresh_token({"sub": str(user_id)})
        
        access_token = AccessToken(
            user_id=user_id,
            token=access_token_str,
            expires_at=access_expire
        )
        refresh_token = RefreshToken(
            user_id=user_id,
            token=refresh_token_str,
            expires_at=refresh_expire
        )
        
        db.add(access_token)
        db.add(refresh_token)
        await db.commit()

        return access_token_str, refresh_token_str

    async def refresh_access_token(self, db: AsyncSession, refresh_token_str: str) -> Optional[str]:
        """
        Exchange a refresh token for a new access token.

        Access tokens live 30 minutes, so a session that is still well within its
        7-day refresh window would otherwise start failing mid-edit. Returns None
        whenever the refresh token cannot be trusted; the caller answers 401 and the
        client sends the user back to the login screen.
        """
        try:
            payload = jwt.decode(
                refresh_token_str, settings.secret_key, algorithms=[settings.algorithm]
            )
        except JWTError:
            return None

        # An access token must never be usable as a refresh token.
        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            user_uuid = uuid.UUID(user_id)
        except (ValueError, AttributeError, TypeError):
            return None

        # The signature can be valid while the session has been revoked server-side.
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token_str)
        )
        stored = result.scalars().first()
        if not stored or stored.is_revoked or stored.expires_at <= datetime.utcnow():
            return None

        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalars().first()
        if not user or not user.is_active:
            return None

        access_token_str, access_expire = self.create_access_token({"sub": str(user.id)})
        db.add(
            AccessToken(user_id=user.id, token=access_token_str, expires_at=access_expire)
        )
        await db.commit()

        return access_token_str

    async def change_password(
        self, db: AsyncSession, user: User, current_password: str, new_password: str
    ) -> tuple[bool, str]:
        """
        Change the password of a signed-in admin.

        Returns (ok, message) rather than raising: the router turns the message
        into the 400 the form shows, and every failure here is a form error the
        operator can correct, not an exception.
        """
        if not user.password_hash:
            return False, "This account has no password set. Use 'Forgot password' instead."

        if not self.verify_password(current_password, user.password_hash):
            return False, "Your current password is incorrect."

        if current_password == new_password:
            return False, "The new password must be different from the current one."

        # Read the id before the commit expires the instance: touching an expired
        # attribute afterwards triggers a lazy refresh outside the async context,
        # which fails with MissingGreenlet rather than reloading.
        user_id = user.id

        user.password_hash = self.get_password_hash(new_password)
        await db.commit()

        # Every other session was authorised by the old password. Revoke them so a
        # password change actually locks out whoever prompted it.
        await self.revoke_sessions(db, user_id)

        # The caller needs a usable instance to mint the replacement session from.
        await db.refresh(user)
        return True, "Password updated."

    async def send_password_reset_otp(self, db: AsyncSession, email: str) -> bool:
        """
        Mail a reset code, but only to an account that can actually sign in with
        a password. The caller answers the same way either way — see the router.
        """
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if not user or not user.is_active:
            return False

        # Only staff sign in with a password; participants use login OTPs, and
        # issuing them a reset code would set a credential they never use.
        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            return False

        return await self.send_otp(db, email, OTPPurpose.PASSWORD_RESET, create_missing=False)

    async def reset_password(
        self, db: AsyncSession, email: str, otp: str, new_password: str
    ) -> Optional[User]:
        """
        Redeem a reset code and set the new password.

        The code is checked against PASSWORD_RESET specifically, so a login code
        that happens to be in flight cannot be used to take over the account.
        """
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user or not user.is_active:
            return None

        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            return None

        result = await db.execute(
            select(OTPCode).where(
                OTPCode.user_id == user.id,
                OTPCode.otp_code == otp,
                OTPCode.purpose == OTPPurpose.PASSWORD_RESET,
                OTPCode.is_used == False,  # noqa: E712 - SQL expression, not a bool test
                OTPCode.expires_at > datetime.utcnow(),
            )
        )
        otp_record = result.scalars().first()
        if not otp_record:
            return None

        user_id = user.id
        otp_record.is_used = True
        user.password_hash = self.get_password_hash(new_password)
        await db.commit()

        # Whoever locked the owner out may be holding a live session.
        await self.revoke_sessions(db, user_id)
        await db.refresh(user)
        return user

    async def revoke_sessions(self, db: AsyncSession, user_id: uuid.UUID) -> None:
        """
        Revoke every refresh token for a user and drop their access tokens.

        Access tokens are stateless JWTs, so deleting the rows does not stop one
        already in a browser tab; it expires within 30 minutes on its own. Killing
        the refresh tokens is what ends those sessions for good.
        """
        await db.execute(
            sa_update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)  # noqa: E712
            .values(is_revoked=True)
        )
        await db.execute(sa_delete(AccessToken).where(AccessToken.user_id == user_id))
        await db.commit()


auth_service = AuthService()
