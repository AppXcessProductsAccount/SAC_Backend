from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Annotated, List
from uuid import UUID

from app.core.database import get_db
from app.core.deps import RoleChecker
from app.models.user import UserRole
from app.models.program import Program
from app.models.registration import ProgramRegistration
from app.schema.program import ProgramCreate, ProgramUpdate, ProgramResponse, ProgramWithRegistrations, RegistrationResponse

router = APIRouter(prefix="/admin/programs", tags=["admin-programs"])

# Only Admins and Super Admins can manage programs
admin_only = Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPER_ADMIN]))

@router.post("/", response_model=ProgramResponse, dependencies=[admin_only])
async def create_program(
    data: ProgramCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Create a new program location/class."""
    new_program = Program(**data.model_dump())
    db.add(new_program)
    await db.commit()
    await db.refresh(new_program)
    return new_program

@router.put("/{program_id}", response_model=ProgramResponse, dependencies=[admin_only])
async def update_program(
    program_id: UUID,
    data: ProgramUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update details of an existing program."""
    program = await db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(program, field, value)
    
    await db.commit()
    await db.refresh(program)
    return program

@router.get("/", response_model=List[ProgramResponse], dependencies=[admin_only])
async def list_all_programs(db: Annotated[AsyncSession, Depends(get_db)]):
    """List all programs including inactive ones."""
    result = await db.execute(select(Program).order_by(Program.order_id.asc()))
    return result.scalars().all()

@router.get("/{program_id}", response_model=ProgramWithRegistrations, dependencies=[admin_only])
async def get_program_details(
    program_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get details of a specific program along with its list of registrants."""
    result = await db.execute(
        select(Program)
        .where(Program.id == program_id)
        .options(selectinload(Program.registrations))
    )
    program = result.scalars().first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
        
    # For older registrations that might have null metadata in the registration table,
    # we can optionally fetch from the Payment table, but since we've added these fields
    # to the model, we should ensure new ones are correct.
    # For now, we return as is, but we'll ensure the register logic is solid.
    
    return program

@router.patch("/{program_id}/toggle-status", response_model=ProgramResponse, dependencies=[admin_only])
async def toggle_program_status(
    program_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Enable or disable a program for registration."""
    program = await db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    program.is_active = not program.is_active
    await db.commit()
    await db.refresh(program)
    return program

@router.delete("/{program_id}", dependencies=[admin_only])
async def delete_program(
    program_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Delete a program and all its registrations."""
    program = await db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    await db.delete(program)
    await db.commit()
    return {"message": "Program deleted successfully"}
