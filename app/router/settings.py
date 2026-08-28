from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import RoleChecker
from app.models.user import User, UserRole
from app.schema.settings import (
    AppSettingsResponse,
    AppSettingsUpdate,
    PublicSettings,
)
from app.services.settings_service import settings_service

router = APIRouter(tags=["settings"])

admin_access = RoleChecker([UserRole.ADMIN, UserRole.SUPER_ADMIN])


@router.get("/admin/settings", response_model=AppSettingsResponse)
async def get_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)],
):
    """Site-wide settings as shown on the admin Settings page."""
    return await settings_service.get(db)


@router.put("/admin/settings", response_model=AppSettingsResponse)
async def update_settings(
    payload: AppSettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)],
):
    """
    Save changed settings.

    `exclude_unset` rather than `exclude_none`: the panel saves one card at a
    time, and a field the operator deliberately cleared must be storable as null.
    """
    changes = payload.model_dump(exclude_unset=True)
    return await settings_service.update(db, changes)


@router.get("/settings/public", response_model=PublicSettings)
async def public_settings(db: Annotated[AsyncSession, Depends(get_db)]):
    """
    The currency and location the public website needs to render prices and
    contact details. No authentication: none of it is private, and the site
    renders before anyone signs in.
    """
    return await settings_service.get(db)
