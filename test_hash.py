from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    hashed = pwd_context.hash("admin@123")
    print(f"Hashed: {hashed}")
except Exception as e:
    print(f"Error: {e}")
