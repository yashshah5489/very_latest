"""
Cache Manager for API responses to minimize external API calls
"""
import os
import json
import time
import logging
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path

import config

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manages caching of API responses to minimize external API calls.
    Uses simple file-based cache with TTL (time-to-live) expiry.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, enabled: Optional[bool] = None):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            enabled: Whether caching is enabled (defaults to config setting)
        """
        self.cache_dir = Path(cache_dir or config.CACHE_DIR)
        self.enabled = config.ENABLE_RESPONSE_CACHING if enabled is None else enabled
        self.cache_expiry = config.CACHE_EXPIRY_SECONDS  # Default TTL in seconds
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Track API usage
        self._api_usage = {
            "tavily": {"count": 0, "last_reset": time.time()},
            "groq": {"count": 0, "last_reset": time.time()}
        }
        
        # Load any existing API usage data
        self._load_api_usage()
        
        logger.info(f"Cache manager initialized. Caching {'enabled' if self.enabled else 'disabled'}.")
    
    def _get_cache_path(self, key: str) -> Path:
        """Get the path to the cache file for a key."""
        # Use hash of key as filename to avoid invalid characters
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hashed_key}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached response for a key if it exists and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached response or None if not found or expired
        """
        if not self.enabled:
            return None
        
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cached data is expired
            if cached_data.get('expires_at', 0) < time.time():
                logger.debug(f"Cache expired for key: {key}")
                cache_path.unlink(missing_ok=True)  # Remove expired cache
                return None
            
            logger.debug(f"Cache hit for key: {key}")
            return cached_data.get('data')
            
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache: {str(e)}")
            return None
    
    def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        Cache data for a key.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds (defaults to global setting)
        """
        if not self.enabled:
            return
        
        ttl = ttl or self.cache_expiry
        expires_at = time.time() + ttl
        
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            'data': data,
            'cached_at': time.time(),
            'expires_at': expires_at
        }
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
            
            logger.debug(f"Cached data for key: {key}, expires in {ttl} seconds")
            
        except IOError as e:
            logger.warning(f"Error writing cache: {str(e)}")
    
    def clear(self, key: Optional[str] = None) -> None:
        """
        Clear cache for a specific key or all cache if key is None.
        
        Args:
            key: Optional cache key to clear
        """
        if key:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
                logger.debug(f"Cleared cache for key: {key}")
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            
            logger.debug("Cleared all cache files")
    
    def track_api_call(self, api_name: str) -> bool:
        """
        Track API call and check if rate limit is exceeded.
        
        Args:
            api_name: API name ('tavily' or 'groq')
            
        Returns:
            True if call is allowed, False if rate limit exceeded
        """
        # Check if we need to reset the counter (daily)
        current_time = time.time()
        one_day_seconds = 24 * 60 * 60
        
        if api_name not in self._api_usage:
            self._api_usage[api_name] = {"count": 0, "last_reset": current_time}
        
        if current_time - self._api_usage[api_name]["last_reset"] > one_day_seconds:
            # Reset counter if it's been more than a day
            self._api_usage[api_name] = {"count": 0, "last_reset": current_time}
        
        # Get the appropriate rate limit based on API name
        rate_limit = None
        if api_name.lower() == "tavily":
            rate_limit = config.TAVILY_RATE_LIMIT_PER_DAY
        elif api_name.lower() == "groq":
            rate_limit = config.GROQ_RATE_LIMIT_PER_DAY
        
        if rate_limit is None:
            # Unknown API, allow the call
            return True
        
        # Check if we've exceeded the rate limit
        if self._api_usage[api_name]["count"] >= rate_limit:
            logger.warning(f"{api_name} API daily rate limit exceeded: {rate_limit} calls/day")
            return False
        
        # Increment the counter and save usage
        self._api_usage[api_name]["count"] += 1
        self._save_api_usage()
        
        # Log when approaching limit
        usage_percent = (self._api_usage[api_name]["count"] / rate_limit) * 100
        if usage_percent >= 80:
            logger.warning(f"{api_name} API usage at {usage_percent:.1f}% of daily limit")
        elif usage_percent >= 50:
            logger.info(f"{api_name} API usage at {usage_percent:.1f}% of daily limit")
        
        return True
    
    def _save_api_usage(self) -> None:
        """Save API usage data to file."""
        usage_path = self.cache_dir / "api_usage.json"
        
        try:
            with open(usage_path, 'w') as f:
                json.dump(self._api_usage, f)
        except IOError as e:
            logger.warning(f"Error saving API usage data: {str(e)}")
    
    def _load_api_usage(self) -> None:
        """Load API usage data from file if it exists."""
        usage_path = self.cache_dir / "api_usage.json"
        
        if not usage_path.exists():
            return
        
        try:
            with open(usage_path, 'r') as f:
                self._api_usage = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading API usage data: {str(e)}")
    
    def get_api_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get API usage statistics.
        
        Returns:
            Dictionary with API usage statistics
        """
        current_time = time.time()
        one_day_seconds = 24 * 60 * 60
        
        stats = {}
        for api_name, usage in self._api_usage.items():
            if api_name.lower() == "tavily":
                limit = config.TAVILY_RATE_LIMIT_PER_DAY
            elif api_name.lower() == "groq":
                limit = config.GROQ_RATE_LIMIT_PER_DAY
            else:
                limit = 0
            
            # Calculate time until reset
            elapsed = current_time - usage["last_reset"]
            time_until_reset = max(0, one_day_seconds - elapsed)
            
            stats[api_name] = {
                "count": usage["count"],
                "limit": limit,
                "usage_percent": (usage["count"] / limit * 100) if limit > 0 else 0,
                "reset_in_seconds": time_until_reset,
                "reset_in_hours": time_until_reset / 3600
            }
        
        return stats


# Create a global cache manager instance
cache_manager = CacheManager()