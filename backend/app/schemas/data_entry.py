from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DataEntryBase(BaseModel):
    title: str
    content: str


class DataEntryCreate(DataEntryBase):
    pass


class DataEntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class DataEntryResponse(DataEntryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_id: int

    class Config:
        from_attributes = True
