from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime
from typing import Annotated, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid

from app.models.auth import (
    UserCreate,
    User,
    Token,
    RefreshTokenRequest,
    LogoutRequest,
    PasswordChangeRequest,
    UserProfile,
    UserSession,
)
from app.db.models.user import User as UserDB, UserRole
from app.core.config import settings
from app.core.database import get_db_session
from app.services.auth_service import auth_service
from app.services.redis_service import redis_service
from app.services.workspace_service import workspace_service

# This is still a mock database - will be replaced with real database when connected
USERS_DB = {}

router = APIRouter()
logger = logging.getLogger(__name__)


def get_user(email: str):
    """Get user by email from in-memory database"""
    if email in USERS_DB:
        user_dict = USERS_DB[email]
        return user_dict
    return None


def get_user_by_id(user_id: int):
    """Get user by ID from in-memory database"""
    for user_data in USERS_DB.values():
        if user_data["id"] == user_id:
            return user_data
    return None


async def get_db_user(db: AsyncSession, email: str):
    """Get user by email from database"""
    stmt = select(UserDB).where(UserDB.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_db_user_by_id(db: AsyncSession, user_id: uuid.UUID):
    """Get user by ID from database"""
    stmt = select(UserDB).where(UserDB.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def authenticate_user(email: str, password: str):
    """Authenticate user with email and password (in-memory mode)"""
    user = get_user(email)
    if not user:
        return False
    if not auth_service.verify_password(password, user["hashed_password"]):
        return False
    return user


async def authenticate_db_user(db: AsyncSession, email: str, password: str):
    """Authenticate user with email and password (database mode)"""
    user = await get_db_user(db, email)
    if not user:
        return False
    if not auth_service.verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(
    token: Annotated[str, Depends(auth_service.oauth2_scheme)],
    db: AsyncSession = Depends(get_db_session),
):
    """Get current user from access token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = auth_service.verify_token(token, "access")
    if not token_data:
        raise credentials_exception

    if db:
        # Database mode
        user = await get_db_user_by_id(db, token_data.user_id)
        if user is None:
            raise credentials_exception

        # Convert to dict for compatibility
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "hashed_password": user.hashed_password,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "role": user.role.value,
            "workspace_id": user.workspace_id,
            "created_at": user.created_at,
            "last_login": getattr(user, "last_login", None),
        }

        # Update last activity if session tracking is enabled
        if token_data.jti:
            # Note: In production, this would update the session in the database
            pass

        return user_dict

    else:
        # In-memory mode
        user = get_user_by_id(token_data.user_id)
        if user is None:
            raise credentials_exception

        # Update last activity if session tracking is enabled
        if token_data.jti:
            # Note: In production, this would update the session in the database
            pass

        return user


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get current active user"""
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


@router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserCreate, request: Request, db: AsyncSession = Depends(get_db_session)
):
    """Register a new user with enhanced security validation and workspace assignment"""

    # Check rate limiting
    auth_service.check_auth_rate_limit(request)

    if db:
        # Database mode - full multi-tenant registration

        # Check if user already exists
        stmt = select(UserDB).where(UserDB.email == user.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Validate password strength
        is_strong, message = auth_service.validate_password_strength(user.password)
        if not is_strong:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        # Hash password
        hashed_password = auth_service.get_password_hash(user.password)

        try:
            # Create default workspace for the user
            workspace = await workspace_service.create_default_workspace(
                db, None
            )  # Will set user_id after creation

            # Create user record
            user_db = UserDB(
                email=user.email,
                username=user.username,
                hashed_password=hashed_password,
                is_active=True,
                is_verified=False,
                workspace_id=workspace.id,
                role=UserRole.OWNER,  # User is owner of their default workspace
            )

            db.add(user_db)
            await db.flush()  # Get the user ID

            # Update workspace created_by field
            workspace.created_by = user_db.id

            await db.commit()
            await db.refresh(user_db)

            logger.info(
                f"New user registered: {user.email} (ID: {user_db.id}) with workspace: {workspace.slug}"
            )

            return User(
                id=user_db.id,
                email=user_db.email,
                username=user_db.username,
                is_active=user_db.is_active,
                is_verified=user_db.is_verified,
                role=user_db.role.value,
                created_at=user_db.created_at,
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to register user {user.email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed. Please try again.",
            )

    else:
        # Fallback to in-memory mode

        # Check if user already exists
        if user.email in USERS_DB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Validate password strength (additional validation beyond Pydantic)
        is_strong, message = auth_service.validate_password_strength(user.password)
        if not is_strong:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        # Hash password with secure settings
        hashed_password = auth_service.get_password_hash(user.password)
        user_id = len(USERS_DB) + 1

        # Create user record
        user_data = {
            "id": user_id,
            "email": user.email,
            "username": user.username,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_verified": False,  # Email verification would be implemented in production
            "role": "user",
            "created_at": datetime.utcnow(),
            "last_login": None,
        }

        USERS_DB[user.email] = user_data

        logger.info(f"New user registered: {user.email} (ID: {user_id})")

        return User(
            id=user_id,
            email=user.email,
            username=user.username,
            is_active=True,
            is_verified=False,
            role="user",
            created_at=user_data["created_at"],
        )


@router.post("/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Login with email/password and return access + refresh tokens"""

    # Check rate limiting
    auth_service.check_auth_rate_limit(request)

    if db:
        # Database mode
        user = await authenticate_db_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(
                f"Failed login attempt for: {form_data.username} from {auth_service._get_client_ip(request)}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Account is deactivated"
            )

        # Extract device information
        device_info = auth_service.extract_device_info(request)

        # Create tokens
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )

        refresh_token = auth_service.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )

        # Create session
        auth_service.create_session(user.id, refresh_token, device_info)

        # Update last login (if this field exists in your model)
        # user.last_login = datetime.utcnow()
        # await db.commit()

        logger.info(
            f"Successful login: {user.email} (ID: {user.id}) from {device_info.ip_address}"
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    else:
        # In-memory mode
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.warning(
                f"Failed login attempt for: {form_data.username} from {auth_service._get_client_ip(request)}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Account is deactivated"
            )

        # Extract device information
        device_info = auth_service.extract_device_info(request)

        # Create tokens
        access_token = auth_service.create_access_token(
            data={"sub": str(user["id"]), "email": user["email"]}
        )

        refresh_token = auth_service.create_refresh_token(
            data={"sub": str(user["id"]), "email": user["email"]}
        )

        # Create session
        auth_service.create_session(user["id"], refresh_token, device_info)

        # Update last login
        user["last_login"] = datetime.utcnow()

        logger.info(
            f"Successful login: {user['email']} (ID: {user['id']}) from {device_info.ip_address}"
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


@router.post("/auth/refresh", response_model=Token)
async def refresh_access_token(refresh_request: RefreshTokenRequest, request: Request):
    """Refresh access token using refresh token"""

    # Check rate limiting
    auth_service.check_auth_rate_limit(request)

    # Verify refresh token
    token_data = auth_service.verify_token(refresh_request.refresh_token, "refresh")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Get user
    user = get_user_by_id(token_data.user_id)
    if not user or not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Update session activity
    if token_data.jti:
        redis_service.update_session_activity(user["id"], token_data.jti)

    # Create new access token
    access_token = auth_service.create_access_token(
        data={"sub": str(user["id"]), "email": user["email"]}
    )

    logger.info(f"Token refreshed for user: {user['email']} (ID: {user['id']})")

    return Token(
        access_token=access_token,
        refresh_token=refresh_request.refresh_token,  # Reuse existing refresh token
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/auth/logout")
async def logout(
    logout_request: LogoutRequest,
    current_user: Annotated[dict, Depends(get_current_active_user)],
    request: Request,
):
    """Logout user and invalidate tokens"""

    user_id = current_user["id"]

    if logout_request.logout_all:
        # Logout from all devices
        auth_service.invalidate_all_sessions(user_id)
        logger.info(
            f"User logged out from all devices: {current_user['email']} (ID: {user_id})"
        )
        return {"message": "Logged out from all devices successfully"}

    elif logout_request.refresh_token:
        # Logout from specific session
        auth_service.blacklist_token(logout_request.refresh_token, "refresh")
        auth_service.invalidate_session(user_id, logout_request.refresh_token)
        logger.info(
            f"User logged out from device: {current_user['email']} (ID: {user_id})"
        )
        return {"message": "Logged out successfully"}

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either refresh_token or logout_all must be provided",
        )


@router.get("/auth/me", response_model=UserProfile)
async def read_users_me(
    current_user: Annotated[dict, Depends(get_current_active_user)],
):
    """Get current user profile with session information"""

    # Get active sessions count
    sessions = auth_service.get_user_sessions(current_user["id"])

    return UserProfile(
        id=current_user["id"],
        email=current_user["email"],
        username=current_user["username"],
        is_active=current_user["is_active"],
        is_verified=current_user.get("is_verified", False),
        role=current_user.get("role", "user"),
        created_at=current_user.get("created_at"),
        last_login=current_user.get("last_login"),
        active_sessions=len(sessions),
    )


@router.get("/auth/sessions", response_model=List[UserSession])
async def get_user_sessions(
    current_user: Annotated[dict, Depends(get_current_active_user)],
):
    """Get all active sessions for the current user"""

    sessions = auth_service.get_user_sessions(current_user["id"])

    session_list = []
    for session in sessions:
        session_list.append(
            UserSession(
                user_id=session["user_id"],
                refresh_token_jti=session["refresh_token_jti"],
                created_at=datetime.fromisoformat(session["created_at"]),
                last_activity=datetime.fromisoformat(session["last_activity"]),
                device_info=session["device_info"],
            )
        )

    return session_list


@router.delete("/auth/sessions/{session_jti}")
async def revoke_session(
    session_jti: str, current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Revoke a specific session"""

    user_id = current_user["id"]

    # Verify the session belongs to the current user
    sessions = auth_service.get_user_sessions(user_id)
    session_exists = any(s["refresh_token_jti"] == session_jti for s in sessions)

    if not session_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    # Revoke the session
    success = redis_service.invalidate_user_session(user_id, session_jti)

    if success:
        logger.info(f"Session revoked: {session_jti} for user {current_user['email']}")
        return {"message": "Session revoked successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session",
        )


@router.post("/auth/change-password")
async def change_password(
    password_request: PasswordChangeRequest,
    current_user: Annotated[dict, Depends(get_current_active_user)],
    request: Request,
):
    """Change user password"""

    # Check rate limiting
    auth_service.check_auth_rate_limit(request)

    # Verify current password
    if not auth_service.verify_password(
        password_request.current_password, current_user["hashed_password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password strength
    is_strong, message = auth_service.validate_password_strength(
        password_request.new_password
    )
    if not is_strong:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Check if new password is different from current
    if auth_service.verify_password(
        password_request.new_password, current_user["hashed_password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Update password
    new_hashed_password = auth_service.get_password_hash(password_request.new_password)
    current_user["hashed_password"] = new_hashed_password

    # Invalidate all other sessions (security best practice)
    auth_service.invalidate_all_sessions(current_user["id"])

    logger.info(
        f"Password changed for user: {current_user['email']} (ID: {current_user['id']})"
    )

    return {
        "message": "Password changed successfully. Please log in again on other devices."
    }
