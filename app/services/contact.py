from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.contact import Contact
from app.schema.contact import ContactCreate
from typing import List

class ContactService:
    @staticmethod
    async def create_contact(db: AsyncSession, data: ContactCreate) -> Contact:
        contact = Contact(
            full_name=data.full_name,
            phone=data.phone,
            email=data.email,
            address=data.address,
            subject=data.subject,
            message=data.message
        )
        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        return contact

    @staticmethod
    async def get_all_contacts(db: AsyncSession) -> List[Contact]:
        result = await db.execute(select(Contact).order_by(Contact.created_at.desc()))
        return list(result.scalars().all())
