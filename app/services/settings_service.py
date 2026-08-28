from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_settings import (
    DEFAULT_CURRENCIES,
    DEFAULT_CURRENCY,
    AppSettings,
)

SETTINGS_ID = 1


class SettingsService:
    """
    Reads and writes the single site-settings row.

    The row is created on first read rather than seeded by the migration, so a
    database restored from an older dump still answers instead of 500ing on a
    missing row.
    """

    @staticmethod
    async def get(db: AsyncSession) -> AppSettings:
        result = await db.execute(select(AppSettings).where(AppSettings.id == SETTINGS_ID))
        row = result.scalars().first()
        if row:
            # Older rows can predate a column's default; never hand back an empty list.
            if not row.enabled_currencies:
                row.enabled_currencies = list(DEFAULT_CURRENCIES)
            return row

        row = AppSettings(
            id=SETTINGS_ID,
            default_currency=DEFAULT_CURRENCY,
            enabled_currencies=list(DEFAULT_CURRENCIES),
        )
        db.add(row)
        try:
            await db.commit()
        except IntegrityError:
            # Two first requests raced; the other one won and the row now exists.
            await db.rollback()
            result = await db.execute(select(AppSettings).where(AppSettings.id == SETTINGS_ID))
            row = result.scalars().first()
            if row is None:
                raise
            return row
        await db.refresh(row)
        return row

    @staticmethod
    async def update(db: AsyncSession, changes: dict) -> AppSettings:
        row = await SettingsService.get(db)

        for field, value in changes.items():
            setattr(row, field, value)

        # The default must be one of the enabled codes, whichever of the two the
        # operator just changed — otherwise the programme form offers a list that
        # cannot produce the default it preselects.
        if row.default_currency not in (row.enabled_currencies or []):
            row.enabled_currencies = [row.default_currency, *(row.enabled_currencies or [])]

        await db.commit()
        await db.refresh(row)
        return row


settings_service = SettingsService()
