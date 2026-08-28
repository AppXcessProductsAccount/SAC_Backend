from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
import os

from app import logger
from app.core.config import setup_logger
from app.core.manager import lifespan
from app.core.redis import RedisHelper
from app.core.settings import Settings
from app.router.base import router as base_router
from app.router.cms import router as cms_router
from app.router.upload import router as upload_router
from app.router.auth import router as auth_router
from app.router.admin import router as admin_router
from app.router.user import router as user_router
from app.router.program import router as program_router
from app.router.admin_program import router as admin_program_router
from app.router.payment import router as payment_router
from app.router.contact import router as contact_router
from app.router.membership import router as membership_router
from app.router.admin_membership import router as admin_membership_router
from app.router.admin_course import router as admin_course_router
from app.router.settings import router as settings_router

_settings = Settings()

app = FastAPI(lifespan=lifespan, debug=_settings.debug, docs_url="/api/docs")

# Create uploads directory if not exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_logger(_settings.debug)

app.include_router(base_router)
app.include_router(cms_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(program_router, prefix="/api")
app.include_router(admin_program_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(contact_router, prefix="/api")
app.include_router(membership_router, prefix="/api")
app.include_router(admin_membership_router, prefix="/api")
app.include_router(admin_course_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

client = TestClient(app)


def add_cache_layer(app: FastAPI) -> None:
    try:
        app.state.cache = RedisHelper()
    except Exception as e:
        logger.error(e)
