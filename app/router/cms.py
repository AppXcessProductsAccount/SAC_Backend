from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.cms import CMSService
from app.schema.cms import (
    SectionSchema, SectionCreate, SectionUpdate, SectionListSchema,
    CMSPageSchema, CMSPageCreate, CMSPageUpdate
)
from typing import Annotated, List, Optional, Union

from app.core.deps import RoleChecker
from app.models.user import UserRole

router = APIRouter(prefix="/cms", tags=["cms"])
super_admin_only = RoleChecker([UserRole.SUPER_ADMIN])

# --- Public/Website Routes ---

@router.get("/website", response_model=Union[List[CMSPageSchema], List[SectionListSchema]])
async def get_website_data(
    db: Annotated[AsyncSession, Depends(get_db)],
    page_id: Optional[int] = None
):
    """
    If page_id is None: Returns all available pages.
    If page_id is provided: Returns all sections for that specific page.
    """
    if page_id is None:
        return await CMSService.get_all_pages(db)
    return await CMSService.get_all_sections(db, page_id)

@router.get("/website/{page_id}/{section_id}/content", response_model=SectionSchema)
async def get_section_content(
    page_id: int,
    section_id: str, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Returns the content for a specific section on a specific page."""
    section = await CMSService.get_section_content(db, section_id)
    if not section or section.page_id != page_id:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found on page {page_id}")
    return section

# --- Admin Routes (Pages) ---

@router.get("/admin/pages", response_model=List[CMSPageSchema], dependencies=[Depends(super_admin_only)])
async def list_pages(db: Annotated[AsyncSession, Depends(get_db)]):
    """List all CMS pages."""
    return await CMSService.get_all_pages(db)

@router.post("/admin/pages", response_model=CMSPageSchema, dependencies=[Depends(super_admin_only)])
async def create_page(data: CMSPageCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    """Create a new CMS page."""
    return await CMSService.create_page(db, data)

@router.put("/admin/pages/{page_id}", response_model=CMSPageSchema, dependencies=[Depends(super_admin_only)])
async def update_page(page_id: int, data: CMSPageUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    """Update a CMS page name."""
    page = await CMSService.update_page(db, page_id, data)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@router.delete("/admin/pages/{page_id}", dependencies=[Depends(super_admin_only)])
async def delete_page(page_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    """Delete a CMS page."""
    success = await CMSService.delete_page(db, page_id)
    if not success:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"message": "Page deleted"}

# --- Admin Routes (Website Flow) ---

@router.get("/admin/website", response_model=Union[List[CMSPageSchema], List[SectionListSchema]], dependencies=[Depends(super_admin_only)])
async def get_admin_website_data(
    db: Annotated[AsyncSession, Depends(get_db)],
    page_id: Optional[int] = None
):
    """
    Same flow as public website but for admin use.
    If page_id is None: Returns all available pages.
    If page_id is provided: Returns all sections for that specific page (metadata only).
    """
    if page_id is None:
        return await CMSService.get_all_pages(db)
    return await CMSService.get_all_sections(db, page_id)

@router.get("/admin/website/{page_id}/{section_id}/content", response_model=SectionSchema, dependencies=[Depends(super_admin_only)])
async def get_admin_section_content(
    page_id: int,
    section_id: str, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Returns the full content for a specific section on a specific page (Admin)."""
    section = await CMSService.get_section_content(db, section_id)
    if not section or section.page_id != page_id:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found on page {page_id}")
    return section

# --- Admin Routes (Section CRUD) ---

@router.get("/admin/sections", response_model=List[SectionSchema], dependencies=[Depends(super_admin_only)])
async def list_all_sections_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
    page_id: Optional[int] = None
):
    """List all sections with full content, optionally filtered by page_id."""
    return await CMSService.get_all_sections(db, page_id)

@router.post("/admin/sections", response_model=SectionSchema, dependencies=[Depends(super_admin_only)])
async def create_section(data: SectionCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    """Create a new section."""
    return await CMSService.create_section(db, data)

@router.put("/admin/sections/{section_id}", response_model=SectionSchema, dependencies=[Depends(super_admin_only)])
async def update_section(section_id: str, data: SectionUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    """Update an existing section's content or template."""
    return await CMSService.upsert_section(db, section_id, data)

@router.delete("/admin/sections/{section_id}", dependencies=[Depends(super_admin_only)])
async def delete_section(section_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    """Delete a section."""
    success = await CMSService.delete_section(db, section_id)
    if not success:
        raise HTTPException(status_code=404, detail="Section not found")
    return {"message": "Section deleted"}
