import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from flask import request, jsonify
import redis
import hashlib

class AdvancedRateLimiter:
    """
    Sophisticated API rate limiting middleware
    Supports multiple rate limiting strategies and configurations
    """
    
    def __init__(self, 
                 redis_host: str = 'localhost', 
                 redis_port: int = 6379, 
                 redis_db: int = 1):
        """
        Initialize rate limiter
        
        :param redis_host: Redis server host
        :param redis_port: Redis server port
        :param redis_db: Redis database number
        """
        self.logger = logging.getLogger(__name__)
        
        # Redis connection
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=redis_db
            )
            self.redis_client.ping()
            self.logger.info("Redis connection established for rate limiting")
        except redis.ConnectionError:
            self.logger.warning("Redis connection failed. Falling back to in-memory rate limiting.")
            self.redis_client = None
        
        # In-memory fallback
        self.memory_limits: Dict[str, Dict[str, Any]] = {}

    def _generate_rate_limit_key(self, 
                                  identifier: str, 
                                  endpoint: str) -> str:
        """
        Generate a unique rate limit key
        
        :param identifier: User or IP identifier
        :param endpoint: API endpoint
        :return: Unique rate limit key
        """
        return hashlib.sha256(
            f"{identifier}:{endpoint}".encode()
        ).hexdigest()

    def rate_limit(self, 
                   limit: int = 100, 
                   window: int = 3600, 
                   error_message: Optional[str] = None,
                   dynamic_limit: Optional[Callable[[str], int]] = None) -> Callable:
        """
        Decorator for rate limiting API endpoints
        
        :param limit: Maximum number of requests
        :param window: Time window in seconds
        :param error_message: Custom error message
        :param dynamic_limit: Function to dynamically calculate rate limit
        :return: Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Determine rate limit identifier
                identifier = self._get_rate_limit_identifier()
                endpoint = request.path
                
                # Dynamically calculate limit if provided
                current_limit = (
                    dynamic_limit(identifier) 
                    if dynamic_limit 
                    else limit
                )
                
                # Check rate limit
                if not self._check_rate_limit(
                    identifier, 
                    endpoint, 
                    current_limit, 
                    window
                ):
                    return jsonify({
                        'error': error_message or 'Rate limit exceeded',
                        'retry_after': window
                    }), 429
                
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def _get_rate_limit_identifier(self) -> str:
        """
        Determine rate limit identifier
        Prioritizes authenticated user, falls back to IP
        
        :return: Rate limit identifier
        """
        # Check for authenticated user
        if hasattr(request, 'user') and request.user:
            return str(request.user.id)
        
        # Fallback to IP address
        return request.remote_addr

    def _check_rate_limit(self, 
                           identifier: str, 
                           endpoint: str, 
                           limit: int, 
                           window: int) -> bool:
        """
        Check and update rate limit
        
        :param identifier: User or IP identifier
        :param endpoint: API endpoint
        :param limit: Maximum number of requests
        :param window: Time window in seconds
        :return: Whether request is allowed
        """
        rate_limit_key = self._generate_rate_limit_key(identifier, endpoint)
        current_time = int(time.time())
        
        if self.redis_client:
            return self._redis_rate_limit(
                rate_limit_key, 
                limit, 
                window, 
                current_time
            )
        else:
            return self._memory_rate_limit(
                rate_limit_key, 
                limit, 
                window, 
                current_time
            )

    def _redis_rate_limit(self, 
                           key: str, 
                           limit: int, 
                           window: int, 
                           current_time: int) -> bool:
        """
        Redis-based rate limiting
        
        :param key: Rate limit key
        :param limit: Maximum number of requests
        :param window: Time window in seconds
        :param current_time: Current timestamp
        :return: Whether request is allowed
        """
        try:
            # Use Redis sorted set for efficient tracking
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time - window)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.zcard(key)
            pipe.expire(key, window)
            
            results = pipe.execute()
            request_count = results[2]
            
            return request_count <= limit
        
        except Exception as e:
            self.logger.error(f"Redis rate limit error: {e}")
            return True  # Fail open

    def _memory_rate_limit(self, 
                            key: str, 
                            limit: int, 
                            window: int, 
                            current_time: int) -> bool:
        """
        In-memory rate limiting
        
        :param key: Rate limit key
        :param limit: Maximum number of requests
        :param window: Time window in seconds
        :param current_time: Current timestamp
        :return: Whether request is allowed
        """
        if key not in self.memory_limits:
            self.memory_limits[key] = {
                'timestamps': [],
                'last_cleanup': current_time
            }
        
        entry = self.memory_limits[key]
        
        # Periodic cleanup
        if current_time - entry['last_cleanup'] > window:
            entry['timestamps'] = [
                ts for ts in entry['timestamps'] 
                if ts > current_time - window
            ]
            entry['last_cleanup'] = current_time
        
        entry['timestamps'].append(current_time)
        
        # Remove old timestamps
        entry['timestamps'] = [
            ts for ts in entry['timestamps'] 
            if ts > current_time - window
        ]
        
        return len(entry['timestamps']) <= limit

def create_rate_limiter(
    redis_host: str = 'localhost', 
    redis_port: int = 6379, 
    redis_db: int = 1
) -> AdvancedRateLimiter:
    """
    Factory method to create rate limiter
    
    :param redis_host: Redis server host
    :param redis_port: Redis server port
    :param redis_db: Redis database number
    :return: Configured rate limiter
    """
    return AdvancedRateLimiter(
        redis_host, 
        redis_port, 
        redis_db
    )
