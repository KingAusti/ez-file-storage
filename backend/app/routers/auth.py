import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..core.audit import AuditService
from ..core.config import settings
from ..core.database import get_db
from ..core.logging import get_logger
from ..core.security import (
    create_access_token,
    create_refresh_token,
    generate_password_reset_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
    verify_token,
)
from ..models.user import PasswordResetToken, RefreshToken, User
from ..schemas.token import Token, TokenRefresh
from ..schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


def get_current_user(
    credentials=Depends(security), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    username = verify_token(credentials.credentials, "access")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed login attempts",
        )

    return user


@router.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")
def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    # Validate password strength
    password_validation = validate_password_strength(user.password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet requirements: {', '.join(password_validation['issues'])}",
        )

    # Check if user already exists
    db_user = (
        db.query(User)
        .filter((User.username == user.username) | (User.email == user.email))
        .first()
    )
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_verified=False,  # Email verification required
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Log user registration
    AuditService.log_user_action(
        db=db,
        action="register",
        user_id=db_user.id,
        details={"username": user.username, "email": user.email},
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    logger.info("User registered", user_id=db_user.id, username=user.username)

    return db_user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()

    # Check if account is locked
    if user and user.locked_until and user.locked_until > datetime.utcnow():
        AuditService.log_login_failure(
            db=db,
            username=username,
            ip_address=get_remote_address(request),
            user_agent=request.headers.get("user-agent"),
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed login attempts",
        )

    if (
        not user
        or not verify_password(password, user.hashed_password)
        or not user.is_active
    ):
        # Increment failed login attempts
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            db.commit()

        AuditService.log_login_failure(
            db=db,
            username=username,
            ip_address=get_remote_address(request),
            user_agent=request.headers.get("user-agent"),
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()

    # Create tokens
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})

    # Store refresh token in database
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow()
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(db_refresh_token)
    db.commit()

    # Log successful login
    AuditService.log_login(
        db=db,
        user=user,
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    logger.info("User logged in", user_id=user.id, username=user.username)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    request: Request, refresh_data: TokenRefresh, db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    # Verify refresh token
    username = verify_token(refresh_data.refresh_token, "refresh")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Check if refresh token exists in database
    token_hash = hashlib.sha256(refresh_data.refresh_token.encode()).hexdigest()
    db_refresh_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if not db_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Get user
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Log token refresh
    AuditService.log_user_action(
        db=db,
        action="token_refresh",
        user_id=user.id,
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_data.refresh_token,  # Keep same refresh token
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout user by revoking refresh tokens"""
    # Revoke all refresh tokens for the user
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id, RefreshToken.is_revoked == False
    ).update({"is_revoked": True})
    db.commit()

    # Log logout
    AuditService.log_user_action(
        db=db,
        action="logout",
        user_id=current_user.id,
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    logger.info(
        "User logged out", user_id=current_user.id, username=current_user.username
    )

    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(
    request: Request, email: str = Form(...), db: Session = Depends(get_db)
):
    """Request password reset"""
    user = db.query(User).filter(User.email == email).first()

    if user:
        # Generate reset token
        reset_token = generate_password_reset_token()
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()

        # Store reset token
        db_reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=1),  # 1 hour expiry
        )
        db.add(db_reset_token)
        db.commit()

        # Log password reset request
        AuditService.log_user_action(
            db=db,
            action="password_reset_requested",
            user_id=user.id,
            details={"email": email},
            ip_address=get_remote_address(request),
            user_agent=request.headers.get("user-agent"),
        )

        # In production, send email with reset link
        logger.info("Password reset requested", user_id=user.id, email=email)

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Reset password using reset token"""
    # Validate password strength
    password_validation = validate_password_strength(new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet requirements: {', '.join(password_validation['issues'])}",
        )

    # Check reset token
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db_reset_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if not db_reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Update password
    user = db_reset_token.user
    user.hashed_password = get_password_hash(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None

    # Mark token as used
    db_reset_token.is_used = True

    db.commit()

    # Log password reset
    AuditService.log_user_action(
        db=db,
        action="password_reset_completed",
        user_id=user.id,
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    logger.info("Password reset completed", user_id=user.id, username=user.username)

    return {"message": "Password has been reset successfully"}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
