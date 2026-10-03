from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from ..core.audit import AuditService
from ..core.database import get_db
from ..core.logging import get_logger
from ..models.data_entry import DataEntry
from ..models.tag import Tag
from ..models.user import User
from ..schemas.data_entry import (
    DataEntryCreate,
    DataEntryResponse,
    DataEntrySearchParams,
    DataEntryUpdate,
)
from .auth import get_current_user

router = APIRouter(prefix="/data-entries", tags=["data entries"])
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.get("/", response_model=List[DataEntryResponse])
@limiter.limit("100/hour")
def get_data_entries(
    request: Request,
    search: Optional[str] = Query(
        None, description="Search term for title and content"
    ),
    tag_ids: Optional[str] = Query(None, description="Comma-separated tag IDs"),
    date_from: Optional[datetime] = Query(
        None, description="Filter entries created after this date"
    ),
    date_to: Optional[datetime] = Query(
        None, description="Filter entries created before this date"
    ),
    sort_by: str = Query(
        "created_at", description="Sort field (created_at, updated_at, title)"
    ),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get data entries with search, filtering, and pagination"""

    # Build base query
    query = (
        db.query(DataEntry)
        .options(joinedload(DataEntry.tags))
        .filter(DataEntry.owner_id == current_user.id)
    )

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                DataEntry.title.ilike(search_term), DataEntry.content.ilike(search_term)
            )
        )

    # Apply tag filter
    if tag_ids:
        try:
            tag_id_list = [
                int(tid.strip()) for tid in tag_ids.split(",") if tid.strip()
            ]
            if tag_id_list:
                query = query.join(DataEntry.tags).filter(Tag.id.in_(tag_id_list))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tag_ids format. Use comma-separated integers.",
            )

    # Apply date filters
    if date_from:
        query = query.filter(DataEntry.created_at >= date_from)
    if date_to:
        query = query.filter(DataEntry.created_at <= date_to)

    # Apply sorting
    if sort_by == "title":
        sort_column = DataEntry.title
    elif sort_by == "updated_at":
        sort_column = DataEntry.updated_at
    else:  # default to created_at
        sort_column = DataEntry.created_at

    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Apply pagination
    data_entries = query.offset(offset).limit(limit).all()

    # Convert to response format with tags
    result = []
    for entry in data_entries:
        entry_dict = {
            "id": entry.id,
            "title": entry.title,
            "content": entry.content,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
            "owner_id": entry.owner_id,
            "tags": [
                {"id": tag.id, "name": tag.name, "color": tag.color}
                for tag in entry.tags
            ],
        }
        result.append(entry_dict)

    # Log data access
    AuditService.log_data_entry_action(
        db=db,
        action="list_entries",
        user_id=current_user.id,
        entry_id=0,  # No specific entry for list operation
        details={
            "count": len(result),
            "search": search,
            "tag_ids": tag_ids,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "offset": offset,
            "limit": limit,
        },
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    return result


@router.post("/", response_model=DataEntryResponse)
@limiter.limit("50/hour")
def create_data_entry(
    request: Request,
    data_entry: DataEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Create the data entry
    db_data_entry = DataEntry(
        title=data_entry.title, content=data_entry.content, owner_id=current_user.id
    )
    db.add(db_data_entry)
    db.flush()  # Flush to get the ID

    # Add tags if provided
    if data_entry.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(data_entry.tag_ids)).all()
        db_data_entry.tags.extend(tags)

    db.commit()
    db.refresh(db_data_entry)

    # Load tags for response
    db_data_entry = (
        db.query(DataEntry)
        .options(joinedload(DataEntry.tags))
        .filter(DataEntry.id == db_data_entry.id)
        .first()
    )

    # Log data entry creation
    AuditService.log_data_entry_action(
        db=db,
        action="create_entry",
        user_id=current_user.id,
        entry_id=db_data_entry.id,
        details={
            "title": data_entry.title,
            "content_length": len(data_entry.content),
            "tag_ids": data_entry.tag_ids,
        },
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    logger.info(
        "Data entry created", user_id=current_user.id, entry_id=db_data_entry.id
    )

    # Convert to response format
    return {
        "id": db_data_entry.id,
        "title": db_data_entry.title,
        "content": db_data_entry.content,
        "created_at": db_data_entry.created_at,
        "updated_at": db_data_entry.updated_at,
        "owner_id": db_data_entry.owner_id,
        "tags": [
            {"id": tag.id, "name": tag.name, "color": tag.color}
            for tag in db_data_entry.tags
        ],
    }


@router.get("/{data_entry_id}", response_model=DataEntryResponse)
def get_data_entry(
    request: Request,
    data_entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data_entry = (
        db.query(DataEntry)
        .options(joinedload(DataEntry.tags))
        .filter(DataEntry.id == data_entry_id, DataEntry.owner_id == current_user.id)
        .first()
    )

    if not data_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data entry not found"
        )

    # Log data entry access
    AuditService.log_data_entry_action(
        db=db,
        action="view_entry",
        user_id=current_user.id,
        entry_id=data_entry_id,
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    # Convert to response format
    return {
        "id": data_entry.id,
        "title": data_entry.title,
        "content": data_entry.content,
        "created_at": data_entry.created_at,
        "updated_at": data_entry.updated_at,
        "owner_id": data_entry.owner_id,
        "tags": [
            {"id": tag.id, "name": tag.name, "color": tag.color}
            for tag in data_entry.tags
        ],
    }


@router.put("/{data_entry_id}", response_model=DataEntryResponse)
@limiter.limit("50/hour")
def update_data_entry(
    request: Request,
    data_entry_id: int,
    data_entry_update: DataEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data_entry = (
        db.query(DataEntry)
        .filter(DataEntry.id == data_entry_id, DataEntry.owner_id == current_user.id)
        .first()
    )

    if not data_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data entry not found"
        )

    # Store old values for audit log
    old_title = data_entry.title
    old_content = data_entry.content
    old_tag_ids = [tag.id for tag in data_entry.tags]

    if data_entry_update.title is not None:
        data_entry.title = data_entry_update.title
    if data_entry_update.content is not None:
        data_entry.content = data_entry_update.content

    # Update tags if provided
    if data_entry_update.tag_ids is not None:
        # Clear existing tags
        data_entry.tags.clear()
        # Add new tags
        if data_entry_update.tag_ids:
            tags = db.query(Tag).filter(Tag.id.in_(data_entry_update.tag_ids)).all()
            data_entry.tags.extend(tags)

    db.commit()
    db.refresh(data_entry)

    # Load tags for response
    data_entry = (
        db.query(DataEntry)
        .options(joinedload(DataEntry.tags))
        .filter(DataEntry.id == data_entry_id)
        .first()
    )

    # Log data entry update
    AuditService.log_data_entry_action(
        db=db,
        action="update_entry",
        user_id=current_user.id,
        entry_id=data_entry_id,
        details={
            "old_title": old_title,
            "new_title": data_entry.title,
            "content_changed": old_content != data_entry.content,
            "content_length": len(data_entry.content),
            "old_tag_ids": old_tag_ids,
            "new_tag_ids": [tag.id for tag in data_entry.tags],
        },
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    logger.info("Data entry updated", user_id=current_user.id, entry_id=data_entry_id)

    # Convert to response format
    return {
        "id": data_entry.id,
        "title": data_entry.title,
        "content": data_entry.content,
        "created_at": data_entry.created_at,
        "updated_at": data_entry.updated_at,
        "owner_id": data_entry.owner_id,
        "tags": [
            {"id": tag.id, "name": tag.name, "color": tag.color}
            for tag in data_entry.tags
        ],
    }


@router.delete("/{data_entry_id}")
@limiter.limit("20/hour")
def delete_data_entry(
    request: Request,
    data_entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data_entry = (
        db.query(DataEntry)
        .filter(DataEntry.id == data_entry_id, DataEntry.owner_id == current_user.id)
        .first()
    )

    if not data_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data entry not found"
        )

    # Store entry details for audit log
    entry_title = data_entry.title
    entry_content_length = len(data_entry.content)

    db.delete(data_entry)
    db.commit()

    # Log data entry deletion
    AuditService.log_data_entry_action(
        db=db,
        action="delete_entry",
        user_id=current_user.id,
        entry_id=data_entry_id,
        details={"title": entry_title, "content_length": entry_content_length},
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    logger.info("Data entry deleted", user_id=current_user.id, entry_id=data_entry_id)

    return {"message": "Data entry deleted successfully"}
