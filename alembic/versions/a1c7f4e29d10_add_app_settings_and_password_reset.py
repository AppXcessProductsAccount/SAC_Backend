"""Add app_settings table and PASSWORD_RESET otp purpose

Revision ID: a1c7f4e29d10
Revises: 0bc11b95296c
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c7f4e29d10'
down_revision: Union[str, None] = '0bc11b95296c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'app_settings',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('default_currency', sa.String(length=10), nullable=False, server_default='MYR'),
        sa.Column('enabled_currencies', sa.JSON(), nullable=True),
        sa.Column('default_city', sa.String(length=120), nullable=True),
        sa.Column('default_country', sa.String(length=120), nullable=True),
        sa.Column('default_address', sa.Text(), nullable=True),
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='Asia/Kuala_Lumpur'),
        sa.Column('date_format', sa.String(length=32), nullable=False, server_default='d MMM yyyy'),
        sa.Column('organisation_name', sa.String(length=200), nullable=True),
        sa.Column('support_email', sa.String(length=255), nullable=True),
        sa.Column('support_phone', sa.String(length=40), nullable=True),
        sa.Column('notify_payment', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('notify_program_registration', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('notify_membership_application', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('notify_participant', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('notification_poll_seconds', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Seed the single row so a fresh install has the defaults the panel expects.
    # The service also creates it on demand, which covers databases restored from
    # a dump taken before this migration ran.
    op.execute(
        """
        INSERT INTO app_settings (id, default_currency, enabled_currencies)
        VALUES (1, 'MYR', '["MYR", "SGD", "USD"]')
        ON CONFLICT (id) DO NOTHING
        """
    )

    # Postgres enum values cannot be added inside a transaction on older servers,
    # and IF NOT EXISTS keeps a re-run from failing on an already-patched database.
    op.execute("ALTER TYPE otppurpose ADD VALUE IF NOT EXISTS 'PASSWORD_RESET'")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('app_settings')
    # Postgres has no ALTER TYPE ... DROP VALUE. The extra enum label is left in
    # place; nothing reads it once the reset endpoints are gone.
