from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DataEntryBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class DataEntryCreate(DataEntryBase):
    tag_ids: Optional[List[int]] = Field(
        default=[], description="List of tag IDs to associate"
    )


class DataEntryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    tag_ids: Optional[List[int]] = Field(
        default=None, description="List of tag IDs to associate"
    )


class DataEntryResponse(DataEntryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_id: int
    tags: List[dict] = Field(default=[], description="Associated tags")

    class Config:
        from_attributes = True


class DataEntrySearchParams(BaseModel):
    """Search and filter parameters for data entries"""

    search: Optional[str] = Field(None, description="Search term for title and content")
    tag_ids: Optional[List[int]] = Field(None, description="Filter by tag IDs")
    date_from: Optional[datetime] = Field(
        None, description="Filter entries created after this date"
    )
    date_to: Optional[datetime] = Field(
        None, description="Filter entries created before this date"
    )
    sort_by: Optional[str] = Field(
        "created_at", description="Sort field (created_at, updated_at, title)"
    )
    sort_order: Optional[str] = Field("desc", description="Sort order (asc, desc)")
    limit: Optional[int] = Field(
        100, ge=1, le=1000, description="Number of results to return"
    )
    offset: Optional[int] = Field(0, ge=0, description="Number of results to skip")
