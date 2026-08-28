"""seed privacy policy and terms of service pages

Adds the two legal pages as ordinary CMS content: one `cms_pages` row each, with
a single `sections` row holding the document. That is what makes them editable
from the admin's Sections editor like every other page — clause by clause, with
"+ Add Item" for a new one — rather than being text baked into the frontend.

The public site carries the same wording as a fallback in
`frontend/lib/legal-defaults.ts`, so /privacy-policy and /terms-of-service render
a complete document even before this migration has been run, or if the API is
unreachable.

Written to be safely re-runnable: both inserts are `ON CONFLICT DO NOTHING`, so
running it against a database where the pages already exist — or where someone
created them by hand — changes nothing and, crucially, does not overwrite
wording an admin has since edited. `backend/alembic/seeds/seed_legal_pages.sql` is the
same content as a plain script, for a production database that is migrated by
hand rather than by alembic.

Revision ID: f7c2a1d94e08
Revises: a1c7f4e29d10
Create Date: 2026-08-25
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f7c2a1d94e08"
down_revision: Union[str, None] = "a1c7f4e29d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ORG = "Self Awareness Society"
CONTACT_EMAIL = "enquiry@selfawareness.com.sg"
CONTACT_PHONE = "+65 6222 5115"
CONTACT_ADDRESS = "Self Awareness Centre HQ, 10 Anson Road, Singapore"

CONTACT_BLOCK = (
    f"Email: {CONTACT_EMAIL}\nPhone: {CONTACT_PHONE}\nAddress: {CONTACT_ADDRESS}"
)

PRIVACY_CONTENT = {
    "title": "Privacy Policy",
    "last_updated": "25 August 2026",
    "intro": (
        f"{ORG} runs meditation and self-awareness programmes in Singapore and Malaysia. "
        "This policy explains what personal information we collect when you use this website, "
        "why we collect it, who we share it with, and the choices you have. It covers this website "
        "and the enquiries, member accounts and programme registrations made through it."
    ),
    "clauses": [
        {
            "heading": "Who we are",
            "body": (
                f"{ORG} is the organisation responsible for the personal information described here.\n\n"
                f"Address: {CONTACT_ADDRESS}\nEmail: {CONTACT_EMAIL}\nPhone: {CONTACT_PHONE}"
            ),
        },
        {
            "heading": "Information we collect",
            "body": (
                "We collect only what a given action needs.\n\n"
                "Enquiries: your name, email address, phone number, and the subject and message you send us.\n\n"
                "Accounts: your name, preferred name, email address and phone number, and — if you choose to add "
                "them — your date of birth, gender, occupation, address and profile photo.\n\n"
                "Programme registrations: the last four digits of your NRIC or passport number, your preferred "
                "language, meal preference, any health conditions you tell us about, the name and phone number of "
                "an emergency contact, how you heard about us, and the name and number of anyone who introduced you.\n\n"
                "Payments: the amount, status and reference of your payment. Card and bank details are entered on "
                "our payment provider's page and are never seen or stored by us.\n\n"
                "Technical information: your device's IP address and basic request logs, kept so the service stays "
                "secure and available."
            ),
        },
        {
            "heading": "Why we collect it",
            "body": (
                "To answer your enquiries; to create and secure your account and send the one-time codes you sign "
                "in with; to register you for a programme and prepare for it, including catering and accessibility; "
                "to reach your emergency contact if something happens during a programme; to take and reconcile "
                "payment; to send you information about a programme you have registered for; and to keep the records "
                "we are required by law to keep.\n\n"
                "We send newsletters and programme announcements only to people who asked for them, and every one of "
                "those messages can be stopped at any time."
            ),
        },
        {
            "heading": "Health information",
            "body": (
                "The health conditions you disclose during registration are used only to keep you safe during a "
                "programme, and are seen only by the staff running it. You do not have to give them, but withholding "
                "something relevant may mean we cannot accept your registration for certain programmes."
            ),
        },
        {
            "heading": "Who we share it with",
            "body": (
                "We do not sell your personal information.\n\n"
                "We share it with our payment provider so a payment can be taken; with the service providers who "
                "host this website, store its files and deliver its email and messages, all of whom act on our "
                "instructions; with the facilitators of a programme you have registered for, limited to what running "
                "it requires; and with the authorities where the law requires it."
            ),
        },
        {
            "heading": "Where your information is held",
            "body": (
                "Our systems are hosted in Singapore. Where a service provider processes information outside "
                "Singapore or Malaysia, we require them to protect it to a standard comparable to the one described "
                "here."
            ),
        },
        {
            "heading": "How long we keep it",
            "body": (
                "Enquiries are kept for up to two years after we have answered them. Account and registration "
                "records are kept while your account is active and for up to seven years afterwards, because payment "
                "and attendance records must be retained for tax and accounting purposes. Anything we no longer need "
                "is deleted or anonymised."
            ),
        },
        {
            "heading": "Keeping it secure",
            "body": (
                "Data travels over encrypted connections, access to it is limited to the staff whose role requires "
                "it, and signing in uses a one-time code rather than a shared password. No system is perfectly "
                "secure, so please do not send us sensitive information by email or public message."
            ),
        },
        {
            "heading": "Cookies and similar technologies",
            "body": (
                "This site stores a small amount of data in your browser to keep you signed in and to remember your "
                "preferences. These are necessary for the site to work and are cleared when you sign out. We do not "
                "use advertising cookies."
            ),
        },
        {
            "heading": "Your rights",
            "body": (
                "You may ask us for a copy of the information we hold about you, ask us to correct it, ask us to "
                f"delete your account, or withdraw a consent you have given. Write to {CONTACT_EMAIL} and we "
                "will respond within 30 days. If our response does not satisfy you, you may complain to the Personal "
                "Data Protection Commission in Singapore, or to the equivalent authority where you live."
            ),
        },
        {
            "heading": "Children",
            "body": (
                "This website is not intended for children under 13, and we do not knowingly collect their "
                "information. A young person attending a programme is registered by a parent or guardian, who "
                "provides the details and consents on their behalf. If you believe we hold a child's information "
                "without that consent, contact us and we will remove it."
            ),
        },
        {
            "heading": "Changes to this policy",
            "body": (
                "We update this policy when our practices change. The date at the top shows when it was last "
                "revised, and material changes are announced on this page before they take effect."
            ),
        },
        {
            "heading": "Contact us",
            "body": (
                "Questions about this policy, or about the information we hold on you:\n\n" + CONTACT_BLOCK
            ),
        },
    ],
}

TERMS_CONTENT = {
    "title": "Terms of Service",
    "last_updated": "25 August 2026",
    "intro": (
        f"These terms govern your use of this website and your registration for programmes run by {ORG}. "
        "By creating an account, submitting an enquiry or registering for a programme, you agree to them. "
        "Please read them together with our Privacy Policy, which explains how we handle your personal information."
    ),
    "clauses": [
        {
            "heading": "Who may use this site",
            "body": (
                "You may use this site if you are 18 or older and able to enter into a binding agreement. A "
                "registration for someone under 18 must be made by their parent or guardian, who accepts these terms "
                "on their behalf."
            ),
        },
        {
            "heading": "Your account",
            "body": (
                "You sign in with a one-time code sent to your email address or phone number, so keeping those "
                "contact details accurate and under your control is what keeps your account secure. Tell us promptly "
                "if you think someone else has access to it. Anything done through your account is treated as done "
                "by you.\n\n"
                "The details you give us — including your phone number and your emergency contact — must be true and "
                "current. We may suspend or close an account used to give false information or to disrupt a "
                "programme."
            ),
        },
        {
            "heading": "Registering for a programme",
            "body": (
                "A registration is a request for a place, not yet a confirmed one. Your place is confirmed once we "
                "accept it and the required payment has been received. Programmes have limited capacity and places "
                "are taken in the order they are paid for.\n\n"
                "Some programmes carry prerequisites, a minimum age, or health requirements. We may decline or "
                "cancel a registration that does not meet them."
            ),
        },
        {
            "heading": "Fees and payment",
            "body": (
                "Programme fees are shown on the programme's page in the currency stated there. Where a programme "
                "allows it, you may pay a deposit to hold your place and settle the balance by the due date shown on "
                "your registration. A place whose balance is unpaid after that date may be released to someone "
                "else.\n\n"
                "Payments are taken by our payment provider. We do not receive or store your card details."
            ),
        },
        {
            "heading": "Cancellations, transfers and refunds",
            "body": (
                "If you cancel, tell us in writing as early as you can. A deposit reserves a place that we then hold "
                "for you and is generally not refundable; whether the balance is refundable depends on how close to "
                "the start date you cancel, and the terms published with each programme apply.\n\n"
                "If we cancel or reschedule a programme, you may transfer to another date or have what you paid for "
                "it refunded in full. We are not responsible for travel or accommodation you booked separately."
            ),
        },
        {
            "heading": "During a programme",
            "body": (
                "Our programmes involve meditation, reflection and physical stillness for extended periods. They are "
                "not medical treatment and are not a substitute for it. Take medical advice before attending if you "
                "have a physical or mental health condition, and tell us about anything relevant when you "
                "register.\n\n"
                "You remain responsible for your own wellbeing during a programme, and should stop and speak to a "
                "facilitator if you feel unwell."
            ),
        },
        {
            "heading": "Conduct",
            "body": (
                "Our centres are shared spaces. Please follow the facilitators' instructions, respect the silence "
                "and privacy of other participants, and do not record or photograph anyone without their agreement. "
                "We may ask someone whose behaviour endangers or seriously disturbs others to leave, without a "
                "refund."
            ),
        },
        {
            "heading": "Our content",
            "body": (
                f"The text, images, recordings and teaching materials on this site belong to {ORG} or to those who "
                "licensed them to us. You may read, download and print them for your own personal, non-commercial "
                "use. Republishing them, selling them or teaching from them requires our written permission."
            ),
        },
        {
            "heading": "Content you submit",
            "body": (
                "You keep ownership of what you send us — enquiries, testimonials, photographs. By sending it you "
                "allow us to use it for the purpose you sent it for, and to publish a testimonial under the name you "
                "gave unless you tell us otherwise. Please do not send anything unlawful, or anything you do not "
                "have the right to share."
            ),
        },
        {
            "heading": "Availability of the site",
            "body": (
                "We aim to keep this site available and its information accurate, but we cannot guarantee it will be "
                "uninterrupted or free of errors. Programme dates, venues, fees and facilitators may change, and the "
                "details confirmed to you when you registered are the ones that apply."
            ),
        },
        {
            "heading": "Limitation of liability",
            "body": (
                "So far as the law allows, our liability arising from your use of this site or from a programme is "
                "limited to the amount you paid for the programme concerned. Nothing in these terms limits liability "
                "for death or personal injury caused by our negligence, for fraud, or for anything else that cannot "
                "lawfully be limited."
            ),
        },
        {
            "heading": "Governing law",
            "body": (
                "These terms are governed by the laws of Singapore, and the courts of Singapore have jurisdiction "
                "over any dispute arising from them."
            ),
        },
        {
            "heading": "Changes to these terms",
            "body": (
                "We may update these terms. The date at the top shows when they were last revised, and the version "
                "in force when you registered is the one that applies to that registration. Continuing to use the "
                "site after a change means you accept the updated terms."
            ),
        },
        {
            "heading": "Contact us",
            "body": "Questions about these terms:\n\n" + CONTACT_BLOCK,
        },
    ],
}

# (page name, section_id, content). The page name is what the frontend matches on
# — `lib/cms-pages.ts` normalises case, spaces and underscores away — so renaming
# a page in the admin moves it to a new URL without detaching it.
LEGAL_PAGES = [
    ("Privacy Policy", "privacy_policy", PRIVACY_CONTENT),
    ("Terms of Service", "terms_of_service", TERMS_CONTENT),
]

# The footer's copyright line, rewritten to the `{year}` token the site expands to
# the current year. Applied only to a line that still carries a hard-coded year,
# so a footer someone has already fixed by hand is left alone.
FOOTER_SECTION_ID = "footer"


def upgrade() -> None:
    conn = op.get_bind()

    for name, section_id, content in LEGAL_PAGES:
        # ON CONFLICT DO NOTHING on both statements: this migration must be safe to
        # re-run against a production database that already has these pages, and it
        # must never overwrite wording an admin has edited since.
        conn.execute(
            sa.text("INSERT INTO cms_pages (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"),
            {"name": name},
        )
        conn.execute(
            sa.text(
                """
                INSERT INTO sections (page_id, section_id, template_id, content)
                SELECT p.id, :section_id, 'default', CAST(:content AS JSON)
                FROM cms_pages p
                WHERE p.name = :name
                ON CONFLICT (section_id) DO NOTHING
                """
            ),
            {"name": name, "section_id": section_id, "content": json.dumps(content)},
        )

    # The stored footer says "© 2024 …", which is why the live site still shows 2024.
    # Swapping the year for the {year} token makes it self-updating from here on.
    conn.execute(
        sa.text(
            """
            UPDATE sections
            SET content = jsonb_set(
                    content::jsonb,
                    '{copyright_text}',
                    to_jsonb(regexp_replace(content->>'copyright_text', '\\d{4}', '{year}'))
                )::json
            WHERE section_id = :section_id
              AND content->>'copyright_text' ~ '\\d{4}'
            """
        ),
        {"section_id": FOOTER_SECTION_ID},
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Sections first: they hold the foreign key onto the pages.
    for name, section_id, _ in LEGAL_PAGES:
        conn.execute(
            sa.text("DELETE FROM sections WHERE section_id = :section_id"),
            {"section_id": section_id},
        )
        conn.execute(
            sa.text("DELETE FROM cms_pages WHERE name = :name"),
            {"name": name},
        )

    # The footer's year token is deliberately NOT reverted: putting a hard-coded
    # year back would be restoring a bug, and the site renders the token correctly
    # either way.
