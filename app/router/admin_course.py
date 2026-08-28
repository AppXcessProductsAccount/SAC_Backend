from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Annotated, List, Optional
import sqlalchemy as sa

from app.core.database import get_db
from app.core.deps import RoleChecker
from app.models.user import User, UserRole
from app.models.course import Course, Unit
from app.schema.course import (
    CourseCreate, CourseUpdate, CourseRead,
    UnitCreate, UnitUpdate, UnitRead, UnitReorder,
    BulkDelete, BulkStatusChange
)
from app.services.s3 import s3_service

router = APIRouter(prefix="/admin/courses", tags=["admin-courses"])

# Admins and Super Admins only
admin_access = RoleChecker([UserRole.ADMIN, UserRole.SUPER_ADMIN])

async def get_presigned_units(units: List[Unit]) -> List[dict]:
    """Helper to inject presigned URLs into unit data."""
    processed_units = []
    for unit in units:
        unit_dict = {
            "id": unit.id,
            "course_id": unit.course_id,
            "title": unit.title,
            "type": unit.type,
            "content_subtype": unit.content_subtype,
            "content_data": unit.content_data,
            "order": unit.order,
            "is_header": unit.is_header,
            "created_at": unit.created_at,
            "updated_at": unit.updated_at
        }
        
        # Check if content needs presigning
        if unit.content_subtype in ["video_url", "audio_url", "document_url", "image_url"]:
            if isinstance(unit.content_data, str) and (unit.content_data.startswith("http")):
                # Generate presigned URL if it's S3
                presigned_url = await s3_service.get_presigned_url(unit.content_data)
                if presigned_url:
                    unit_dict["content_data"] = presigned_url
        
        processed_units.append(unit_dict)
    return processed_units

@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_in: CourseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Create a new course."""
    new_course = Course(**course_in.model_dump())
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    
    # Load units (empty for new course)
    new_course.units = []
    return new_course

@router.get("/{id}", response_model=CourseRead)
async def get_course(
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Get full course details including units with presigned URLs."""
    result = await db.execute(
        select(Course).where(Course.id == id)
    )
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Load units ordered by 'order'
    unit_result = await db.execute(
        select(Unit).where(Unit.course_id == id).order_by(Unit.order)
    )
    units = unit_result.scalars().all()
    
    # Process units for presigned URLs
    processed_units = await get_presigned_units(units)
    
    # Construct response
    course_data = CourseRead.model_validate(course).model_dump()
    course_data["units"] = processed_units
    return course_data

@router.put("/{id}", response_model=CourseRead)
async def update_course(
    id: int,
    course_in: CourseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Update course basic details."""
    result = await db.execute(select(Course).where(Course.id == id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    update_data = course_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    await db.commit()
    await db.refresh(course)
    
    # Load units for response
    unit_result = await db.execute(
        select(Unit).where(Unit.course_id == id).order_by(Unit.order)
    )
    units = unit_result.scalars().all()
    processed_units = await get_presigned_units(units)
    
    course_data = CourseRead.model_validate(course).model_dump()
    course_data["units"] = processed_units
    return course_data

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Delete a course."""
    result = await db.execute(select(Course).where(Course.id == id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    await db.delete(course)
    await db.commit()
    return None

@router.post("/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_courses(
    bulk_in: BulkDelete,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Delete multiple courses."""
    await db.execute(
        sa.delete(Course).where(Course.id.in_(bulk_in.ids))
    )
    await db.commit()
    return None

@router.post("/bulk-status", status_code=status.HTTP_200_OK)
async def bulk_status_change(
    bulk_in: BulkStatusChange,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Change status for multiple courses."""
    await db.execute(
        update(Course)
        .where(Course.id.in_(bulk_in.ids))
        .values(is_active=bulk_in.is_active)
    )
    await db.commit()
    return {"message": f"Status updated for {len(bulk_in.ids)} courses"}

@router.post("/{id}/units", response_model=UnitRead, status_code=status.HTTP_201_CREATED)
async def add_unit(
    id: int,
    unit_in: UnitCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Add a unit to a course."""
    # Check if course exists
    course_res = await db.execute(select(Course).where(Course.id == id))
    if not course_res.scalars().first():
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get max order to append at the end if order not provided
    if unit_in.order == 0 or unit_in.order is None:
        order_res = await db.execute(select(sa.func.max(Unit.order)).where(Unit.course_id == id))
        max_order = order_res.scalar() or 0
        unit_in.order = max_order + 1

    new_unit = Unit(**unit_in.model_dump(), course_id=id)
    db.add(new_unit)
    await db.commit()
    await db.refresh(new_unit)
    return new_unit

@router.put("/{id}/units/{unit_id}", response_model=UnitRead)
async def update_unit(
    id: int,
    unit_id: int,
    unit_in: UnitUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Update a specific unit."""
    result = await db.execute(
        select(Unit).where(Unit.id == unit_id, Unit.course_id == id)
    )
    unit = result.scalars().first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    update_data = unit_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(unit, field, value)
    
    await db.commit()
    await db.refresh(unit)
    return unit

@router.delete("/{id}/units/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit(
    id: int,
    unit_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Delete a unit from a course."""
    result = await db.execute(
        select(Unit).where(Unit.id == unit_id, Unit.course_id == id)
    )
    unit = result.scalars().first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    await db.delete(unit)
    await db.commit()
    return None

@router.put("/{id}/units/reorder")
async def reorder_units(
    id: int,
    reorder_in: UnitReorder,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """Update units order."""
    # We use a bulk update approach or individual updates
    for index, unit_id in enumerate(reorder_in.unit_ids):
        await db.execute(
            update(Unit)
            .where(Unit.id == unit_id, Unit.course_id == id)
            .values(order=index + 1)
        )
    
    await db.commit()
    return {"message": "Units reordered successfully"}

@router.get("", response_model=List[CourseRead])
async def list_courses(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(admin_access)]
):
    """List all courses."""
    result = await db.execute(select(Course).order_by(Course.created_at.desc()))
    courses = result.scalars().all()
    return courses
