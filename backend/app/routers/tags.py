"""
Tag management endpoints
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..core.audit import AuditService
from ..core.database import get_db
from ..core.logging import get_logger
from ..models.tag import Tag
from ..models.user import User
from ..schemas.tag import TagCreate, TagResponse, TagUpdate, TagWithCount
from .auth import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.get("/", response_model=List[TagWithCount])
@limiter.limit("100/hour")
def get_tags(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all tags with usage count"""
    tags = db.query(Tag).all()

    # Add count of data entries for each tag
    tags_with_count = []
    for tag in tags:
        count = len(tag.data_entries)
        tag_dict = {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "description": tag.description,
            "created_at": tag.created_at,
            "updated_at": tag.updated_at,
            "data_entry_count": count,
        }
        tags_with_count.append(tag_dict)

    # Log tag access
    AuditService.log_user_action(
        db=db,
        action="list_tags",
        user_id=current_user.id,
        details={"count": len(tags)},
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    return tags_with_count


@router.post("/", response_model=TagResponse)
@limiter.limit("20/hour")
def create_tag(
    request: Request,
    tag: TagCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new tag"""
    # Check if tag already exists
    existing_tag = db.query(Tag).filter(Tag.name == tag.name).first()
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists",
        )

    # Create new tag
    db_tag = Tag(name=tag.name, color=tag.color, description=tag.description)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)

    # Log tag creation
    AuditService.log_user_action(
        db=db,
        action="create_tag",
        user_id=current_user.id,
        details={"tag_name": tag.name, "tag_id": db_tag.id},
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    logger.info(
        "Tag created", user_id=current_user.id, tag_id=db_tag.id, tag_name=tag.name
    )

    return db_tag


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(
    request: Request,
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific tag by ID"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )

    # Log tag access
    AuditService.log_user_action(
        db=db,
        action="view_tag",
        user_id=current_user.id,
        details={"tag_id": tag_id, "tag_name": tag.name},
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    return tag


@router.put("/{tag_id}", response_model=TagResponse)
@limiter.limit("20/hour")
def update_tag(
    request: Request,
    tag_id: int,
    tag_update: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a tag"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )

    # Check if new name conflicts with existing tag
    if tag_update.name and tag_update.name != tag.name:
        existing_tag = db.query(Tag).filter(Tag.name == tag_update.name).first()
        if existing_tag:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this name already exists",
            )

    # Store old values for audit log
    old_name = tag.name
    old_color = tag.color
    old_description = tag.description

    # Update tag
    if tag_update.name is not None:
        tag.name = tag_update.name
    if tag_update.color is not None:
        tag.color = tag_update.color
    if tag_update.description is not None:
        tag.description = tag_update.description

    db.commit()
    db.refresh(tag)

    # Log tag update
    AuditService.log_user_action(
        db=db,
        action="update_tag",
        user_id=current_user.id,
        details={
            "tag_id": tag_id,
            "old_name": old_name,
            "new_name": tag.name,
            "old_color": old_color,
            "new_color": tag.color,
            "description_changed": old_description != tag.description,
        },
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    logger.info(
        "Tag updated", user_id=current_user.id, tag_id=tag_id, tag_name=tag.name
    )

    return tag


@router.delete("/{tag_id}")
@limiter.limit("10/hour")
def delete_tag(
    request: Request,
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a tag"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )

    # Store tag details for audit log
    tag_name = tag.name
    data_entry_count = len(tag.data_entries)

    # Remove tag from all data entries first
    for data_entry in tag.data_entries:
        data_entry.tags.remove(tag)

    # Delete the tag
    db.delete(tag)
    db.commit()

    # Log tag deletion
    AuditService.log_user_action(
        db=db,
        action="delete_tag",
        user_id=current_user.id,
        details={
            "tag_id": tag_id,
            "tag_name": tag_name,
            "affected_data_entries": data_entry_count,
        },
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    logger.info(
        "Tag deleted", user_id=current_user.id, tag_id=tag_id, tag_name=tag_name
    )

    return {"message": "Tag deleted successfully"}
