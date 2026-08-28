"""add_contact_table

Revision ID: 263cbcccf71a
Revises: 619ae68160fc
Create Date: 2026-04-30 13:12:35.728760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '263cbcccf71a'
down_revision: Union[str, None] = '619ae68160fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('contacts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('subject', sa.String(length=255), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contacts_id'), 'contacts', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_contacts_id'), table_name='contacts')
    op.drop_table('contacts')
