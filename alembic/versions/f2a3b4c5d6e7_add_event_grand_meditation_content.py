"""add event_grand_meditation_content JSON to app_settings

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-09-12

Editable names and images for the Grand Group Meditation page (the Guru and the
three remembered masters), managed from the admin Events feature. Null means the
page uses its built-in defaults.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column("event_grand_meditation_content", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "event_grand_meditation_content")
