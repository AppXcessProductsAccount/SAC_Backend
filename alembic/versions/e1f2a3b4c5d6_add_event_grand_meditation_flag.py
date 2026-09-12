"""add event_grand_meditation_enabled feature flag to app_settings

Revision ID: e1f2a3b4c5d6
Revises: b3d81f0a5c47
Create Date: 2026-09-12

The Grand Group Meditation event page is publishable/retractable from the admin
without a deploy. Existing rows default to enabled so the page is live once built.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "b3d81f0a5c47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column(
            "event_grand_meditation_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "event_grand_meditation_enabled")
