from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.landing import Section, CMSPage
from app.schema.cms import SectionCreate, SectionUpdate, CMSPageCreate, CMSPageUpdate
from typing import Optional, List

class CMSService:
    # --- Page Methods ---
    @staticmethod
    async def get_all_pages(db: AsyncSession) -> List[CMSPage]:
        result = await db.execute(select(CMSPage).order_by(CMSPage.id.asc()))
        return list(result.scalars().all())

    @staticmethod
    async def create_page(db: AsyncSession, data: CMSPageCreate) -> CMSPage:
        page = CMSPage(name=data.name)
        db.add(page)
        await db.commit()
        await db.refresh(page)
        return page

    @staticmethod
    async def update_page(db: AsyncSession, page_id: int, data: CMSPageUpdate) -> Optional[CMSPage]:
        result = await db.execute(select(CMSPage).filter(CMSPage.id == page_id))
        page = result.scalars().first()
        if page:
            page.name = data.name
            await db.commit()
            await db.refresh(page)
        return page

    @staticmethod
    async def delete_page(db: AsyncSession, page_id: int) -> bool:
        result = await db.execute(select(CMSPage).filter(CMSPage.id == page_id))
        page = result.scalars().first()
        if page:
            await db.delete(page)
            await db.commit()
            return True
        return False

    # --- Section Methods ---
    @staticmethod
    async def get_all_sections(db: AsyncSession, page_id: Optional[int] = None) -> List[Section]:
        query = select(Section)
        if page_id:
            query = query.filter(Section.page_id == page_id)
        result = await db.execute(query.order_by(Section.id.asc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_section_list(db: AsyncSession, page_id: Optional[int] = None) -> List[Section]:
        query = select(Section)
        if page_id:
            query = query.filter(Section.page_id == page_id)
        result = await db.execute(query.order_by(Section.id.asc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_section_content(db: AsyncSession, section_id: str) -> Optional[Section]:
        result = await db.execute(select(Section).filter(Section.section_id == section_id))
        return result.scalars().first()

    @staticmethod
    async def upsert_section(db: AsyncSession, section_id: str, data: SectionUpdate) -> Section:
        result = await db.execute(select(Section).filter(Section.section_id == section_id))
        section = result.scalars().first()
        
        update_data = data.model_dump(exclude_unset=True)
        
        if not section:
            template_id = update_data.get("template_id", "default")
            content = update_data.get("content", {})
            page_id = update_data.get("page_id")
            section = Section(section_id=section_id, template_id=template_id, content=content, page_id=page_id)
            db.add(section)
        else:
            if "template_id" in update_data:
                section.template_id = update_data["template_id"]
            if "content" in update_data:
                section.content = update_data["content"]
            if "page_id" in update_data:
                section.page_id = update_data["page_id"]
        
        await db.commit()
        await db.refresh(section)
        return section

    @staticmethod
    async def create_section(db: AsyncSession, data: SectionCreate) -> Section:
        section = Section(
            section_id=data.section_id,
            template_id=data.template_id,
            content=data.content,
            page_id=data.page_id
        )
        db.add(section)
        await db.commit()
        await db.refresh(section)
        return section

    @staticmethod
    async def delete_section(db: AsyncSession, section_id: str) -> bool:
        result = await db.execute(select(Section).filter(Section.section_id == section_id))
        section = result.scalars().first()
        if section:
            await db.delete(section)
            await db.commit()
            return True
        return False
