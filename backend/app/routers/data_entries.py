from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..core.database import get_db
from ..core.audit import AuditService
from ..core.logging import get_logger
from ..models.user import User
from ..models.data_entry import DataEntry
from ..schemas.data_entry import DataEntryCreate, DataEntryResponse, DataEntryUpdate
from .auth import get_current_user

router = APIRouter(prefix="/data-entries", tags=["data entries"])
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.get("/", response_model=List[DataEntryResponse])
@limiter.limit("100/hour")
def get_data_entries(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data_entries = db.query(DataEntry).filter(
        DataEntry.owner_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    # Log data access
    AuditService.log_data_entry_action(
        db=db,
        action="list_entries",
        user_id=current_user.id,
        entry_id=0,  # No specific entry for list operation
        details={"count": len(data_entries), "skip": skip, "limit": limit},
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent")
    )
    
    return data_entries


@router.post("/", response_model=DataEntryResponse)
@limiter.limit("50/hour")
def create_data_entry(
    request: Request,
    data_entry: DataEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_data_entry = DataEntry(
        title=data_entry.title,
        content=data_entry.content,
        owner_id=current_user.id
    )
    db.add(db_data_entry)
    db.commit()
    db.refresh(db_data_entry)
    
    # Log data entry creation
    AuditService.log_data_entry_action(
        db=db,
        action="create_entry",
        user_id=current_user.id,
        entry_id=db_data_entry.id,
        details={"title": data_entry.title, "content_length": len(data_entry.content)},
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent")
    )
    
    logger.info("Data entry created", user_id=current_user.id, entry_id=db_data_entry.id)
    
    return db_data_entry


@router.get("/{data_entry_id}", response_model=DataEntryResponse)
def get_data_entry(
    request: Request,
    data_entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data_entry = db.query(DataEntry).filter(
        DataEntry.id == data_entry_id,
        DataEntry.owner_id == current_user.id
    ).first()
    
    if not data_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data entry not found"
        )
    
    # Log data entry access
    AuditService.log_data_entry_action(
        db=db,
        action="view_entry",
        user_id=current_user.id,
        entry_id=data_entry_id,
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent")
    )
    
    return data_entry


@router.put("/{data_entry_id}", response_model=DataEntryResponse)
@limiter.limit("50/hour")
def update_data_entry(
    request: Request,
    data_entry_id: int,
    data_entry_update: DataEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data_entry = db.query(DataEntry).filter(
        DataEntry.id == data_entry_id,
        DataEntry.owner_id == current_user.id
    ).first()
    
    if not data_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data entry not found"
        )
    
    # Store old values for audit log
    old_title = data_entry.title
    old_content = data_entry.content
    
    if data_entry_update.title is not None:
        data_entry.title = data_entry_update.title
    if data_entry_update.content is not None:
        data_entry.content = data_entry_update.content
    
    db.commit()
    db.refresh(data_entry)
    
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
            "content_length": len(data_entry.content)
        },
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent")
    )
    
    logger.info("Data entry updated", user_id=current_user.id, entry_id=data_entry_id)
    
    return data_entry


@router.delete("/{data_entry_id}")
@limiter.limit("20/hour")
def delete_data_entry(
    request: Request,
    data_entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data_entry = db.query(DataEntry).filter(
        DataEntry.id == data_entry_id,
        DataEntry.owner_id == current_user.id
    ).first()
    
    if not data_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data entry not found"
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
        details={
            "title": entry_title,
            "content_length": entry_content_length
        },
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent")
    )
    
    logger.info("Data entry deleted", user_id=current_user.id, entry_id=data_entry_id)
    
    return {"message": "Data entry deleted successfully"}
