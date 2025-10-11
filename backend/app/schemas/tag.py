"""
Pydantic schemas for Tag model
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: str = Field(default="#007bff", pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")
    description: Optional[str] = Field(None, max_length=200, description="Tag description")


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, max_length=200)


class TagResponse(TagBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TagWithCount(TagResponse):
    data_entry_count: int = Field(description="Number of data entries with this tag")


class DataEntryWithTags(BaseModel):
    """Schema for data entry with tags"""
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True
