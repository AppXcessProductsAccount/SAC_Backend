import asyncio
from app.core.database import DBSessionManager
from app.models.user import User, UserRole
from app.services.auth_service import auth_service
from sqlalchemy import select

async def seed_admin():
    email = "admin@gmail.com"
    password = "admin@123"
    
    async with DBSessionManager.session() as db:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        hashed_password = auth_service.get_password_hash(password)
        
        if user:
            print(f"User {email} already exists. Updating role and password...")
            user.role = UserRole.SUPER_ADMIN
            user.password_hash = hashed_password
            user.is_verified = True
        else:
            print(f"Creating new Super Admin: {email}")
            user = User(
                full_name="Super Admin",
                email=email,
                password_hash=hashed_password,
                role=UserRole.SUPER_ADMIN,
                is_active=True,
                is_verified=True
            )
            db.add(user)
        
        await db.commit()
        print("Admin user seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_admin())
