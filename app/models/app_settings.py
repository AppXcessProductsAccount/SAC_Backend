from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models import Base


# The event kinds the notification bell can show. Kept here rather than in the
# router so the settings row and the feed cannot drift apart.
NOTIFICATION_TYPES = (
    "payment",
    "program_registration",
    "membership_application",
    "participant",
)

DEFAULT_CURRENCY = "MYR"
DEFAULT_CURRENCIES = ["MYR", "SGD", "USD"]


class AppSettings(Base):
    """
    Site-wide operational settings, held in exactly one row.

    Currency and location were previously hardcoded in three separate places —
    "MYR" in the dashboard, a free-text currency box on the programme form, and
    nothing at all for the centre's own address. Anything an operator should be
    able to change without a deploy belongs here.

    A singleton table rather than a key/value store: the fields are a fixed,
    known set, so typed columns get validation and defaults for free, and reading
    them is one row rather than a scan.
    """

    __tablename__ = "app_settings"

    # Always 1. The unique constraint is what stops a second row appearing.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # Localisation
    default_currency: Mapped[str] = mapped_column(String(10), default=DEFAULT_CURRENCY)
    enabled_currencies: Mapped[list | None] = mapped_column(sa.JSON, default=list)
    default_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    default_country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    default_address: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kuala_Lumpur")
    date_format: Mapped[str] = mapped_column(String(32), default="d MMM yyyy")

    # Organisation identity, used in the panel header and outgoing mail.
    organisation_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    support_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    support_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Notifications — which event kinds reach the bell, and how often it refreshes.
    notify_payment: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_program_registration: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_membership_application: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_participant: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_poll_seconds: Mapped[int] = mapped_column(Integer, default=60)

    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime, server_default=func.now(), onupdate=func.now()
    )

    def enabled_notification_types(self) -> set[str]:
        """The event kinds the feed is allowed to return."""
        flags = {
            "payment": self.notify_payment,
            "program_registration": self.notify_program_registration,
            "membership_application": self.notify_membership_application,
            "participant": self.notify_participant,
        }
        return {name for name, on in flags.items() if on}
