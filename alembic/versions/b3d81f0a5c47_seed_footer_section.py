"""seed the site footer as an editable CMS section

The footer was the only part of the site with no row in `sections`, so it never
appeared in the admin's Sections editor and there was nothing to edit. Every
value came from a literal in `frontend/components/Footer.tsx`, which meant the
newsletter wording, the social links and the copyright line could only be
changed by a developer and a deploy.

This seeds that same wording as the section's starting content, so the admin
opens on exactly what the site already shows and an editor changes only what
they mean to. The frontend still carries these defaults, so the footer renders
unchanged if the row is ever missing.

Attached to Home: the footer renders site-wide, but a section row needs a page,
and Home is where an editor looks for it. The site resolves a section's page by
id at runtime, so this choice does not affect what renders.

Revision ID: b3d81f0a5c47
Revises: f7c2a1d94e08
Create Date: 2026-08-28
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b3d81f0a5c47"
down_revision: Union[str, None] = "f7c2a1d94e08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SECTION_ID = "footer"
PAGE_NAME = "Home"

# Mirrors the `displayData` fallback in frontend/components/Footer.tsx. Keep the
# two in step: the frontend one is what renders if this row is ever absent.
FOOTER_CONTENT = {
    "newsletter_title": "Subscribe to Our Newsletter",
    "newsletter_description": (
        "Stay updated with our latest workshops, meditation sessions, and "
        "spiritual insights."
    ),
    "facebook_url": "#",
    "instagram_url": "#",
    "twitter_url": "#",
    "mail_url": "#",
    "logo_url": "/logo.png",
    # {year} is expanded to the current year when rendered, so the line does not
    # go stale the way a hard-coded "2024" did.
    "copyright_text": "© {year} SelfAwareness Inc. All rights reserved.",
    "background_image_url": "/testimonial.png",
}


def upgrade() -> None:
    conn = op.get_bind()

    # Rows seeded with an explicit id leave the sequence behind, so the insert
    # below would draw an id that is already taken and die on sections_pkey -
    # which ON CONFLICT (section_id) does not arbitrate. Same guard as the
    # legal-pages migration.
    conn.execute(
        sa.text(
            """
            SELECT setval(
                pg_get_serial_sequence('sections', 'id'),
                COALESCE((SELECT MAX(id) FROM sections), 0) + 1,
                false
            )
            """
        )
    )

    # ON CONFLICT DO NOTHING: this must be safe to re-run against a database
    # where the footer already exists, and must never overwrite wording an
    # admin has since edited.
    conn.execute(
        sa.text(
            """
            INSERT INTO sections (page_id, section_id, template_id, content)
            SELECT p.id, :section_id, 'default', CAST(:content AS JSON)
            FROM cms_pages p
            WHERE p.name = :page_name
            ON CONFLICT (section_id) DO NOTHING
            """
        ),
        {
            "section_id": SECTION_ID,
            "page_name": PAGE_NAME,
            "content": json.dumps(FOOTER_CONTENT),
        },
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("DELETE FROM sections WHERE section_id = :section_id"),
        {"section_id": SECTION_ID},
    )
