"""
Authentication service with Redis caching and session management
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import structlog
from app.models.user import User
from app.schemas.auth import UserLogin, UserRegister
from app.core.cache import (
    cache_manager, 
    cached, 
    user_cache_key, 
    invalidate_user_cache
)
from app.core.session import session_manager, create_user_session
from app.config import settings

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service with caching and session management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @cached(key_func=lambda self, user_id: user_cache_key(user_id), expire=1800)
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with caching"""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                logger.debug("User retrieved from database", user_id=user_id)
            else:
                logger.warning("User not found", user_id=user_id)
            
            return user
            
        except Exception as e:
            logger.error("Error getting user by ID", user_id=user_id, error=str(e))
            return None
    
    @cached(key_func=lambda self, email: f"user:email:{email}", expire=1800)
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email with caching"""
        try:
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if user:
                logger.debug("User retrieved by email", email=email)
            else:
                logger.debug("User not found by email", email=email)
            
            return user
            
        except Exception as e:
            logger.error("Error getting user by email", email=email, error=str(e))
            return None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning("Token verification failed", error=str(e))
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = await self.get_user_by_email(email)
            if not user:
                logger.warning("Authentication failed - user not found", email=email)
                return None
            
            if not self.verify_password(password, user.password_hash):
                logger.warning("Authentication failed - invalid password", email=email)
                return None
            
            if not user.enabled:
                logger.warning("Authentication failed - user disabled", email=email)
                return None
            
            logger.info("User authenticated successfully", user_id=user.id, email=email)
            return user
            
        except Exception as e:
            logger.error("Error authenticating user", email=email, error=str(e))
            return None
    
    async def login_user(self, login_data: UserLogin) -> Optional[Dict[str, Any]]:
        """Login user and create session"""
        try:
            # Authenticate user
            user = await self.authenticate_user(login_data.email, login_data.password)
            if not user:
                return None
            
            # Create tokens
            access_token = self.create_access_token(data={"sub": str(user.id)})
            refresh_token = self.create_refresh_token(data={"sub": str(user.id)})
            
            # Create session
            user_data = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "admin": user.admin,
                "enabled": user.enabled
            }
            session_token = await create_user_session(user.id, user_data)
            
            # Update last login
            user.last_login = datetime.utcnow()
            await self.db.commit()
            
            # Invalidate user cache to refresh last_login
            await invalidate_user_cache(user.id)
            
            logger.info("User logged in successfully", user_id=user.id, email=user.email)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "session_token": session_token,
                "token_type": "bearer",
                "user": user_data
            }
            
        except Exception as e:
            logger.error("Error logging in user", email=login_data.email, error=str(e))
            return None
    
    async def register_user(self, register_data: UserRegister) -> Optional[Dict[str, Any]]:
        """Register new user"""
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_email(register_data.email)
            if existing_user:
                logger.warning("Registration failed - user already exists", email=register_data.email)
                return None
            
            # Create new user
            hashed_password = self.get_password_hash(register_data.password)
            user = User(
                email=register_data.email,
                name=register_data.name,
                password_hash=hashed_password,
                admin=register_data.admin if hasattr(register_data, 'admin') else False,
                enabled=True
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            # Create tokens
            access_token = self.create_access_token(data={"sub": str(user.id)})
            refresh_token = self.create_refresh_token(data={"sub": str(user.id)})
            
            # Create session
            user_data = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "admin": user.admin,
                "enabled": user.enabled
            }
            session_token = await create_user_session(user.id, user_data)
            
            logger.info("User registered successfully", user_id=user.id, email=user.email)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "session_token": session_token,
                "token_type": "bearer",
                "user": user_data
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error registering user", email=register_data.email, error=str(e))
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token"""
        try:
            payload = self.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            user = await self.get_user_by_id(int(user_id))
            if not user or not user.enabled:
                return None
            
            # Create new access token
            access_token = self.create_access_token(data={"sub": str(user.id)})
            
            logger.info("Token refreshed successfully", user_id=user.id)
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error("Error refreshing token", error=str(e))
            return None
    
    async def logout_user(self, session_token: str) -> bool:
        """Logout user and invalidate session"""
        try:
            # Get session data
            session_data = await session_manager.get_session(session_token)
            if not session_data:
                return False
            
            user_id = session_data.get("user_id")
            
            # Delete session
            await session_manager.delete_session(session_token)
            
            # Invalidate user cache
            if user_id:
                await invalidate_user_cache(user_id)
            
            logger.info("User logged out successfully", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Error logging out user", error=str(e))
            return False
    
    async def get_current_user_from_token(self, token: str) -> Optional[User]:
        """Get current user from JWT token"""
        try:
            payload = self.verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            user = await self.get_user_by_id(int(user_id))
            if not user or not user.enabled:
                return None
            
            return user
            
        except Exception as e:
            logger.error("Error getting current user from token", error=str(e))
            return None
    
    async def get_current_user_from_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get current user from session token"""
        try:
            session_data = await session_manager.get_session(session_token)
            if not session_data:
                return None
            
            user_id = session_data.get("user_id")
            if not user_id:
                return None
            
            # Verify user still exists and is enabled
            user = await self.get_user_by_id(user_id)
            if not user or not user.enabled:
                # Invalidate session if user is disabled
                await session_manager.delete_session(session_token)
                return None
            
            return {
                "user": session_data.get("user_data"),
                "session": session_data
            }
            
        except Exception as e:
            logger.error("Error getting current user from session", error=str(e))
            return None
    
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Verify old password
            if not self.verify_password(old_password, user.password_hash):
                logger.warning("Password change failed - invalid old password", user_id=user_id)
                return False
            
            # Update password
            user.password_hash = self.get_password_hash(new_password)
            await self.db.commit()
            
            # Invalidate user cache
            await invalidate_user_cache(user_id)
            
            logger.info("Password changed successfully", user_id=user_id)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error changing password", user_id=user_id, error=str(e))
            return False
    
    async def get_user_sessions(self, user_id: int) -> list:
        """Get all active sessions for a user"""
        return await session_manager.get_active_sessions(user_id)
    
    async def revoke_all_sessions(self, user_id: int) -> int:
        """Revoke all sessions for a user"""
        return await session_manager.delete_user_sessions(user_id)


# Service functions for backward compatibility
async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID"""
    service = AuthService(db)
    return await service.get_user_by_id(user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    service = AuthService(db)
    return await service.get_user_by_email(email)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate user"""
    service = AuthService(db)
    return await service.authenticate_user(email, password)


async def login_user(db: AsyncSession, login_data: UserLogin) -> Optional[Dict[str, Any]]:
    """Login user"""
    service = AuthService(db)
    return await service.login_user(login_data)


async def register_user(db: AsyncSession, register_data: UserRegister) -> Optional[Dict[str, Any]]:
    """Register user"""
    service = AuthService(db)
    return await service.register_user(register_data)


async def get_current_user_from_token(db: AsyncSession, token: str) -> Optional[User]:
    """Get current user from token"""
    service = AuthService(db)
    return await service.get_current_user_from_token(token)
