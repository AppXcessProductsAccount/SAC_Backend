"""consolidate_landing_tables

Revision ID: 535d96e5f74f
Revises: d471331b2f3d
Create Date: 2026-04-22 12:54:24.083332

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '535d96e5f74f'
down_revision: Union[str, None] = 'd471331b2f3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import json

import json

def upgrade() -> None:
    # 1. Create sections table if it doesn't exist
    # Use bind to check if table exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    if 'sections' not in existing_tables:
        op.create_table(
            'sections',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('section_id', sa.String(length=100), nullable=False),
            sa.Column('template_id', sa.String(length=100), nullable=False, server_default='default'),
            sa.Column('content', sa.JSON(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_sections_section_id'), 'sections', ['section_id'], unique=True)

    # 2. Migrate data
    # Define a helper to migrate a single-row table
    def migrate_single_row(table_name, section_id):
        if table_name in existing_tables:
            result = connection.execute(sa.text(f"SELECT * FROM {table_name} LIMIT 1"))
            row = result.fetchone()
            if row:
                # Convert row to dict, excluding 'id'
                content = dict(row._mapping)
                if 'id' in content:
                    del content['id']
                # Check if already exists in sections to avoid unique constraint error
                check = connection.execute(sa.text("SELECT 1 FROM sections WHERE section_id = :section_id"), {"section_id": section_id})
                if not check.fetchone():
                    connection.execute(
                        sa.text("INSERT INTO sections (section_id, template_id, content) VALUES (:section_id, :template_id, :content)"),
                        {"section_id": section_id, "template_id": "default", "content": json.dumps(content)}
                    )

    # Define a helper to migrate a multi-row table (list)
    def migrate_multi_row(table_name, section_id):
        if table_name in existing_tables:
            result = connection.execute(sa.text(f"SELECT * FROM {table_name} ORDER BY id ASC"))
            rows = result.fetchall()
            if rows:
                items = []
                for row in rows:
                    content = dict(row._mapping)
                    if 'id' in content:
                        del content['id']
                    items.append(content)
                # Check if already exists in sections
                check = connection.execute(sa.text("SELECT 1 FROM sections WHERE section_id = :section_id"), {"section_id": section_id})
                if not check.fetchone():
                    connection.execute(
                        sa.text("INSERT INTO sections (section_id, template_id, content) VALUES (:section_id, :template_id, :content)"),
                        {"section_id": section_id, "template_id": "default", "content": json.dumps(items)}
                    )

    # Migrate each section
    migrate_single_row('navbar', 'navbar')
    migrate_single_row('hero', 'hero')
    migrate_single_row('program_section', 'programs')
    migrate_multi_row('event', 'events')
    migrate_single_row('enlightenment', 'enlightenment')
    migrate_multi_row('testimonial', 'testimonials')
    migrate_single_row('contact_info', 'contact')
    migrate_single_row('footer_info', 'footer')

    # 3. Drop old tables
    tables_to_drop = [
        'navbar', 'hero', 'program_section', 'event', 'enlightenment', 
        'testimonial', 'contact_info', 'footer_info', 'events_section', 'testimonial_section'
    ]
    for table in tables_to_drop:
        if table in existing_tables:
            op.drop_table(table)


def downgrade() -> None:
    # Downgrade is complex because we're merging many tables into one. 
    # For now, we'll just drop the sections table.
    op.drop_index(op.f('ix_sections_section_id'), table_name='sections')
    op.drop_table('sections')
