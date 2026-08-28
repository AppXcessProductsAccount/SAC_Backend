from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from datetime import datetime

class UnitBase(BaseModel):
    title: str
    type: str
    content_subtype: str
    content_data: Optional[Any] = None
    order: Optional[int] = 0
    is_header: Optional[bool] = False

class UnitCreate(UnitBase):
    pass

class UnitUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    content_subtype: Optional[str] = None
    content_data: Optional[Any] = None
    order: Optional[int] = None
    is_header: Optional[bool] = None

class UnitRead(UnitBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CourseBase(BaseModel):
    title: str
    code: str
    category: str
    description: Optional[str] = None
    is_active: Optional[bool] = True
    expires_at: Optional[datetime] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    code: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None

class CourseRead(CourseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    units: List[UnitRead] = []

    model_config = ConfigDict(from_attributes=True)

class UnitReorder(BaseModel):
    unit_ids: List[int]

class BulkDelete(BaseModel):
    ids: List[int]

class BulkStatusChange(BaseModel):
    ids: List[int]
    is_active: bool
