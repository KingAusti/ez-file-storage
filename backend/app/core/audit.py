from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from sqlalchemy.orm import Session

from ..models.audit_log import AuditLog
from ..models.user import User
from .database import get_db

logger = structlog.get_logger()


class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log an audit action to the database"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(audit_log)
            db.commit()

            logger.info(
                "Audit log created",
                action=action,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
            )
        except Exception as e:
            logger.error("Failed to create audit log", error=str(e))
            db.rollback()
            raise

    @staticmethod
    def log_login(
        db: Session,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log a successful login"""
        AuditService.log_action(
            db=db,
            action="login",
            user_id=user.id,
            details={"username": user.username, "email": user.email},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_login_failure(
        db: Session,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log a failed login attempt"""
        AuditService.log_action(
            db=db,
            action="login_failure",
            details={"username": username},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_data_entry_action(
        db: Session,
        action: str,
        user_id: int,
        entry_id: int,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log data entry related actions"""
        AuditService.log_action(
            db=db,
            action=action,
            user_id=user_id,
            resource_type="data_entry",
            resource_id=entry_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_user_action(
        db: Session,
        action: str,
        user_id: int,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log user account related actions"""
        AuditService.log_action(
            db=db,
            action=action,
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
