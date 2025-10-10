"""
Tag model for organizing data entries
"""
from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

# Association table for many-to-many relationship between DataEntry and Tag
data_entry_tags = Table(
    'data_entry_tags',
    Base.metadata,
    Column('data_entry_id', Integer, ForeignKey('data_entries.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    color = Column(String, default="#007bff")  # Hex color for UI
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to data entries
    data_entries = relationship("DataEntry", secondary=data_entry_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag(name='{self.name}', color='{self.color}')>"
