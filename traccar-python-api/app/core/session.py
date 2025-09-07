"""
Session management using Redis
"""
import json
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import structlog
from app.core.cache import cache_manager
from app.config import settings

logger = structlog.get_logger(__name__)


class SessionManager:
    """Redis-based session manager"""
    
    def __init__(self, cache_manager):
        self.cache = cache_manager
        self.session_prefix = "session:"
        self.default_expire = 3600 * 24 * 7  # 7 days
    
    async def create_session(
        self, 
        user_id: int, 
        user_data: Dict[str, Any],
        expire: Optional[int] = None
    ) -> str:
        """
        Create a new session
        
        Args:
            user_id: User ID
            user_data: User data to store in session
            expire: Session expiration in seconds
        
        Returns:
            Session token
        """
        try:
            # Generate secure session token
            session_token = secrets.token_urlsafe(32)
            session_key = f"{self.session_prefix}{session_token}"
            
            # Prepare session data
            session_data = {
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "user_data": user_data,
                "ip_address": None,  # Will be set by middleware
                "user_agent": None,  # Will be set by middleware
            }
            
            # Store session
            expire_time = expire or self.default_expire
            await self.cache.set(session_key, session_data, expire=expire_time)
            
            # Also store user -> session mapping for cleanup
            user_sessions_key = f"user_sessions:{user_id}"
            user_sessions = await self.cache.get(user_sessions_key) or []
            user_sessions.append(session_token)
            await self.cache.set(user_sessions_key, user_sessions, expire=expire_time)
            
            logger.info("Session created", user_id=user_id, session_token=session_token[:8])
            return session_token
            
        except Exception as e:
            logger.error("Error creating session", user_id=user_id, error=str(e))
            raise
    
    async def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Get session data
        
        Args:
            session_token: Session token
        
        Returns:
            Session data or None if not found/expired
        """
        try:
            session_key = f"{self.session_prefix}{session_token}"
            session_data = await self.cache.get(session_key)
            
            if session_data:
                # Update last accessed time
                session_data["last_accessed"] = datetime.utcnow().isoformat()
                await self.cache.set(session_key, session_data)
                
                logger.debug("Session accessed", session_token=session_token[:8])
                return session_data
            
            return None
            
        except Exception as e:
            logger.error("Error getting session", session_token=session_token[:8], error=str(e))
            return None
    
    async def update_session(
        self, 
        session_token: str, 
        data: Dict[str, Any]
    ) -> bool:
        """
        Update session data
        
        Args:
            session_token: Session token
            data: Data to update
        
        Returns:
            True if updated successfully
        """
        try:
            session_key = f"{self.session_prefix}{session_token}"
            session_data = await self.cache.get(session_key)
            
            if session_data:
                # Update session data
                session_data.update(data)
                session_data["last_accessed"] = datetime.utcnow().isoformat()
                
                await self.cache.set(session_key, session_data)
                logger.debug("Session updated", session_token=session_token[:8])
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error updating session", session_token=session_token[:8], error=str(e))
            return False
    
    async def delete_session(self, session_token: str) -> bool:
        """
        Delete session
        
        Args:
            session_token: Session token
        
        Returns:
            True if deleted successfully
        """
        try:
            session_key = f"{self.session_prefix}{session_token}"
            
            # Get session data to find user_id
            session_data = await self.cache.get(session_key)
            if session_data:
                user_id = session_data.get("user_id")
                
                # Remove from user sessions list
                if user_id:
                    user_sessions_key = f"user_sessions:{user_id}"
                    user_sessions = await self.cache.get(user_sessions_key) or []
                    if session_token in user_sessions:
                        user_sessions.remove(session_token)
                        await self.cache.set(user_sessions_key, user_sessions)
            
            # Delete session
            result = await self.cache.delete(session_key)
            logger.info("Session deleted", session_token=session_token[:8])
            return result
            
        except Exception as e:
            logger.error("Error deleting session", session_token=session_token[:8], error=str(e))
            return False
    
    async def delete_user_sessions(self, user_id: int) -> int:
        """
        Delete all sessions for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Number of sessions deleted
        """
        try:
            user_sessions_key = f"user_sessions:{user_id}"
            user_sessions = await self.cache.get(user_sessions_key) or []
            
            deleted_count = 0
            for session_token in user_sessions:
                if await self.delete_session(session_token):
                    deleted_count += 1
            
            # Clear user sessions list
            await self.cache.delete(user_sessions_key)
            
            logger.info("User sessions deleted", user_id=user_id, count=deleted_count)
            return deleted_count
            
        except Exception as e:
            logger.error("Error deleting user sessions", user_id=user_id, error=str(e))
            return 0
    
    async def extend_session(self, session_token: str, expire: Optional[int] = None) -> bool:
        """
        Extend session expiration
        
        Args:
            session_token: Session token
            expire: New expiration time in seconds
        
        Returns:
            True if extended successfully
        """
        try:
            session_key = f"{self.session_prefix}{session_token}"
            session_data = await self.cache.get(session_key)
            
            if session_data:
                expire_time = expire or self.default_expire
                await self.cache.set(session_key, session_data, expire=expire_time)
                logger.debug("Session extended", session_token=session_token[:8])
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error extending session", session_token=session_token[:8], error=str(e))
            return False
    
    async def get_active_sessions(self, user_id: int) -> list:
        """
        Get all active sessions for a user
        
        Args:
            user_id: User ID
        
        Returns:
            List of active sessions
        """
        try:
            user_sessions_key = f"user_sessions:{user_id}"
            user_sessions = await self.cache.get(user_sessions_key) or []
            
            active_sessions = []
            for session_token in user_sessions:
                session_data = await self.get_session(session_token)
                if session_data:
                    active_sessions.append({
                        "token": session_token[:8] + "...",  # Truncated for security
                        "created_at": session_data.get("created_at"),
                        "last_accessed": session_data.get("last_accessed"),
                        "ip_address": session_data.get("ip_address"),
                        "user_agent": session_data.get("user_agent")
                    })
            
            return active_sessions
            
        except Exception as e:
            logger.error("Error getting active sessions", user_id=user_id, error=str(e))
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (Redis handles this automatically, but this can be used for logging)
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            # Get all session keys
            pattern = f"{self.session_prefix}*"
            session_keys = await self.cache.redis.keys(pattern) if self.cache.redis else []
            
            # Check which sessions are still valid
            valid_sessions = 0
            for key in session_keys:
                if await self.cache.exists(key):
                    valid_sessions += 1
            
            expired_count = len(session_keys) - valid_sessions
            logger.info("Session cleanup completed", total_keys=len(session_keys), expired=expired_count)
            
            return expired_count
            
        except Exception as e:
            logger.error("Error cleaning up sessions", error=str(e))
            return 0
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics
        
        Returns:
            Session statistics
        """
        try:
            # Get all session keys
            pattern = f"{self.session_prefix}*"
            session_keys = await self.cache.redis.keys(pattern) if self.cache.redis else []
            
            # Get all user session keys
            user_pattern = "user_sessions:*"
            user_session_keys = await self.cache.redis.keys(user_pattern) if self.cache.redis else []
            
            return {
                "total_sessions": len(session_keys),
                "total_users_with_sessions": len(user_session_keys),
                "average_sessions_per_user": len(session_keys) / max(len(user_session_keys), 1)
            }
            
        except Exception as e:
            logger.error("Error getting session stats", error=str(e))
            return {}


# Global session manager instance
session_manager = SessionManager(cache_manager)


# Session utilities
async def create_user_session(user_id: int, user_data: Dict[str, Any]) -> str:
    """Create a session for a user"""
    return await session_manager.create_session(user_id, user_data)


async def get_user_from_session(session_token: str) -> Optional[Dict[str, Any]]:
    """Get user data from session token"""
    session_data = await session_manager.get_session(session_token)
    if session_data:
        return {
            "user_id": session_data["user_id"],
            "user_data": session_data["user_data"]
        }
    return None


async def invalidate_user_session(session_token: str) -> bool:
    """Invalidate a specific session"""
    return await session_manager.delete_session(session_token)


async def invalidate_all_user_sessions(user_id: int) -> int:
    """Invalidate all sessions for a user"""
    return await session_manager.delete_user_sessions(user_id)


# Session middleware data
async def update_session_context(session_token: str, ip_address: str, user_agent: str):
    """Update session with request context"""
    await session_manager.update_session(session_token, {
        "ip_address": ip_address,
        "user_agent": user_agent
    })
