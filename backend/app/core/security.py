import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

logger = structlog.get_logger()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        token_type_check: str = payload.get("type")

        if username is None or token_type_check != token_type:
            return None
        return username
    except JWTError as e:
        logger.warning("Token verification failed", error=str(e))
        return None


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def verify_password_reset_token(token: str) -> bool:
    # In a real implementation, you'd store these tokens in the database
    # with expiration times and verify against the database
    return len(token) > 20  # Basic validation for now


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return detailed feedback"""
    issues = []
    score = 0

    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    else:
        score += 1

    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    else:
        score += 1

    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    else:
        score += 1

    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")
    else:
        score += 1

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        issues.append("Password must contain at least one special character")
    else:
        score += 1

    return {
        "is_valid": len(issues) == 0,
        "score": score,
        "issues": issues,
        "strength": "weak" if score < 3 else "medium" if score < 5 else "strong",
    }
