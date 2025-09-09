"""
Group cache service for performance optimization
"""
from typing import Dict, List, Set, Optional
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from collections import defaultdict
import structlog

logger = structlog.get_logger(__name__)


class GroupCacheService:
    """Service for caching group data and hierarchy"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._hierarchy_cache: Dict[int, List[int]] = {}
        self._accessible_groups_cache: Dict[int, Set[int]] = {}
        self._group_levels_cache: Dict[int, int] = {}
    
    async def get_group_hierarchy(self) -> Dict[int, List[int]]:
        """Get group hierarchy from cache or database"""
        if not self._hierarchy_cache:
            await self._load_hierarchy_cache()
        return self._hierarchy_cache
    
    async def _load_hierarchy_cache(self):
        """Load group hierarchy into cache"""
        try:
            result = await self.db.execute(select(text('id, parent_id')).select_from(text('groups')))
            hierarchy = defaultdict(list)
            
            for group_id, parent_id in result.all():
                if parent_id:
                    hierarchy[parent_id].append(group_id)
            
            self._hierarchy_cache = dict(hierarchy)
            logger.debug("Group hierarchy cache loaded", groups_count=len(self._hierarchy_cache))
            
        except Exception as e:
            logger.error("Error loading group hierarchy cache", error=str(e))
            self._hierarchy_cache = {}
    
    async def get_user_accessible_groups(self, user_id: int, is_admin: bool) -> Set[int]:
        """Get accessible groups for user from cache or database"""
        cache_key = f"user_{user_id}_admin_{is_admin}"
        
        if cache_key in self._accessible_groups_cache:
            return self._accessible_groups_cache[cache_key]
        
        accessible_groups = await self._calculate_accessible_groups(user_id, is_admin)
        self._accessible_groups_cache[cache_key] = accessible_groups
        
        return accessible_groups
    
    async def _calculate_accessible_groups(self, user_id: int, is_admin: bool) -> Set[int]:
        """Calculate accessible groups for user"""
        if is_admin:
            # Admin can access all groups
            result = await self.db.execute(select(text('id')).select_from(text('groups')))
            return {row[0] for row in result.all()}
        
        # Get directly assigned groups
        result = await self.db.execute(
            text("SELECT group_id FROM user_group_permissions WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        direct_groups = {row[0] for row in result.all()}
        
        if not direct_groups:
            return set()
        
        # Get all groups in the hierarchy (children of assigned groups)
        accessible_groups = set(direct_groups)
        hierarchy = await self.get_group_hierarchy()
        
        # Recursively find all children
        def find_children(group_ids: Set[int]) -> Set[int]:
            children = set()
            for group_id in group_ids:
                if group_id in hierarchy:
                    children.update(hierarchy[group_id])
            return children
        
        # Keep finding children until no more are found
        current_level = direct_groups
        while current_level:
            children = find_children(current_level)
            new_groups = children - accessible_groups
            if not new_groups:
                break
            accessible_groups.update(new_groups)
            current_level = new_groups
        
        return accessible_groups
    
    async def get_group_levels(self, group_ids: Set[int]) -> Dict[int, int]:
        """Get hierarchical levels for groups from cache or database"""
        cache_key = tuple(sorted(group_ids))
        
        # Check if we have cached levels for these groups
        cached_levels = {}
        uncached_groups = set()
        
        for group_id in group_ids:
            if group_id in self._group_levels_cache:
                cached_levels[group_id] = self._group_levels_cache[group_id]
            else:
                uncached_groups.add(group_id)
        
        if uncached_groups:
            new_levels = await self._calculate_group_levels(uncached_groups)
            self._group_levels_cache.update(new_levels)
            cached_levels.update(new_levels)
        
        return {group_id: cached_levels.get(group_id, 0) for group_id in group_ids}
    
    async def _calculate_group_levels(self, group_ids: Set[int]) -> Dict[int, int]:
        """Calculate hierarchical levels for groups"""
        if not group_ids:
            return {}
        
        # Get all groups with their parent relationships
        result = await self.db.execute(
            select(text('id, parent_id'))
            .select_from(text('groups'))
            .where(text('id').in_(group_ids))
        )
        
        parent_map = {row[0]: row[1] for row in result.all()}
        levels = {}
        
        def calculate_level(group_id: int) -> int:
            if group_id in levels:
                return levels[group_id]
            
            parent_id = parent_map.get(group_id)
            if parent_id is None:
                levels[group_id] = 0
            else:
                levels[group_id] = calculate_level(parent_id) + 1
            
            return levels[group_id]
        
        for group_id in group_ids:
            calculate_level(group_id)
        
        return levels
    
    def invalidate_cache(self):
        """Invalidate all caches"""
        self._hierarchy_cache.clear()
        self._accessible_groups_cache.clear()
        self._group_levels_cache.clear()
        logger.debug("Group cache invalidated")
    
    def invalidate_user_cache(self, user_id: int):
        """Invalidate cache for specific user"""
        keys_to_remove = [key for key in self._accessible_groups_cache.keys() if f"user_{user_id}_" in key]
        for key in keys_to_remove:
            del self._accessible_groups_cache[key]
        logger.debug("User group cache invalidated", user_id=user_id)
    
    def invalidate_hierarchy_cache(self):
        """Invalidate hierarchy cache"""
        self._hierarchy_cache.clear()
        self._group_levels_cache.clear()
        logger.debug("Group hierarchy cache invalidated")
