import os
import time
import json
import hashlib
import logging
from typing import Any, Dict, Optional, Callable, Union
import redis
import pickle
import zlib
from functools import wraps

class AdvancedCacheManager:
    """
    Sophisticated multi-layer caching system with advanced features
    Supports in-memory, Redis, and disk-based caching strategies
    """
    
    def __init__(self, 
                 redis_host: str = 'localhost', 
                 redis_port: int = 6379, 
                 redis_db: int = 0,
                 cache_dir: Optional[str] = None):
        """
        Initialize advanced cache manager
        
        :param redis_host: Redis server host
        :param redis_port: Redis server port
        :param redis_db: Redis database number
        :param cache_dir: Directory for disk-based caching
        """
        # Logging configuration
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Redis connection
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=redis_db
            )
            self.redis_client.ping()
            self.logger.info("Redis connection established successfully")
        except redis.ConnectionError:
            self.logger.warning("Redis connection failed. Falling back to local caching.")
            self.redis_client = None
        
        # Disk-based cache configuration
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # In-memory cache
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

    def _generate_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """
        Generate a unique cache key based on function name and arguments
        
        :param func_name: Name of the function
        :param args: Positional arguments
        :param kwargs: Keyword arguments
        :return: Unique cache key
        """
        # Serialize arguments
        serialized_args = pickle.dumps((args, kwargs))
        
        # Create hash
        hash_key = hashlib.sha256(
            f"{func_name}:{serialized_args}".encode()
        ).hexdigest()
        
        return hash_key

    def _compress_data(self, data: Any) -> bytes:
        """
        Compress data using zlib
        
        :param data: Data to compress
        :return: Compressed data
        """
        return zlib.compress(pickle.dumps(data))

    def _decompress_data(self, compressed_data: bytes) -> Any:
        """
        Decompress data
        
        :param compressed_data: Compressed data
        :return: Decompressed data
        """
        return pickle.loads(zlib.decompress(compressed_data))

    def cache(self, 
              ttl: int = 3600, 
              cache_none: bool = False, 
              layer: str = 'multi') -> Callable:
        """
        Decorator for caching function results
        
        :param ttl: Time-to-live for cached result
        :param cache_none: Whether to cache None results
        :param layer: Caching layer (memory/redis/disk/multi)
        :return: Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_cache_key(func.__name__, *args, **kwargs)
                
                # Check cache layers based on strategy
                if layer in ['memory', 'multi']:
                    memory_result = self.get_from_memory_cache(cache_key)
                    if memory_result is not None:
                        return memory_result
                
                if layer in ['redis', 'multi'] and self.redis_client:
                    redis_result = self.get_from_redis_cache(cache_key)
                    if redis_result is not None:
                        return redis_result
                
                if layer in ['disk', 'multi']:
                    disk_result = self.get_from_disk_cache(cache_key)
                    if disk_result is not None:
                        return disk_result
                
                # Execute function if no cached result
                result = func(*args, **kwargs)
                
                # Cache result if not None or cache_none is True
                if result is not None or cache_none:
                    self.set_cache(cache_key, result, ttl, layer)
                
                return result
            return wrapper
        return decorator

    def set_cache(self, 
                  key: str, 
                  value: Any, 
                  ttl: int = 3600, 
                  layer: str = 'multi'):
        """
        Set cache across different layers
        
        :param key: Cache key
        :param value: Value to cache
        :param ttl: Time-to-live for cached result
        :param layer: Caching layer
        """
        compressed_value = self._compress_data(value)
        
        if layer in ['memory', 'multi']:
            self.memory_cache[key] = {
                'value': compressed_value,
                'expiry': time.time() + ttl
            }
        
        if layer in ['redis', 'multi'] and self.redis_client:
            try:
                self.redis_client.setex(key, ttl, compressed_value)
            except Exception as e:
                self.logger.error(f"Redis cache set error: {e}")
        
        if layer in ['disk', 'multi']:
            disk_path = os.path.join(self.cache_dir, key)
            with open(disk_path, 'wb') as f:
                json.dump({
                    'value': compressed_value.decode('latin-1'),
                    'expiry': time.time() + ttl
                }, f)

    def get_from_memory_cache(self, key: str) -> Optional[Any]:
        """
        Retrieve value from memory cache
        
        :param key: Cache key
        :return: Cached value or None
        """
        cache_entry = self.memory_cache.get(key)
        
        if cache_entry:
            if time.time() < cache_entry['expiry']:
                return self._decompress_data(cache_entry['value'])
            else:
                del self.memory_cache[key]
        
        return None

    def get_from_redis_cache(self, key: str) -> Optional[Any]:
        """
        Retrieve value from Redis cache
        
        :param key: Cache key
        :return: Cached value or None
        """
        if not self.redis_client:
            return None
        
        try:
            compressed_value = self.redis_client.get(key)
            if compressed_value:
                return self._decompress_data(compressed_value)
        except Exception as e:
            self.logger.error(f"Redis cache get error: {e}")
        
        return None

    def get_from_disk_cache(self, key: str) -> Optional[Any]:
        """
        Retrieve value from disk cache
        
        :param key: Cache key
        :return: Cached value or None
        """
        disk_path = os.path.join(self.cache_dir, key)
        
        if os.path.exists(disk_path):
            try:
                with open(disk_path, 'r') as f:
                    cache_entry = json.load(f)
                
                if time.time() < cache_entry['expiry']:
                    return self._decompress_data(
                        cache_entry['value'].encode('latin-1')
                    )
                else:
                    os.remove(disk_path)
            except Exception as e:
                self.logger.error(f"Disk cache read error: {e}")
        
        return None

    def invalidate_cache(self, key: Optional[str] = None, layer: str = 'multi'):
        """
        Invalidate cache for a specific key or entire cache
        
        :param key: Optional specific cache key to invalidate
        :param layer: Cache layer to invalidate
        """
        if layer in ['memory', 'multi']:
            if key:
                self.memory_cache.pop(key, None)
            else:
                self.memory_cache.clear()
        
        if layer in ['redis', 'multi'] and self.redis_client:
            try:
                if key:
                    self.redis_client.delete(key)
                else:
                    self.redis_client.flushdb()
            except Exception as e:
                self.logger.error(f"Redis cache invalidation error: {e}")
        
        if layer in ['disk', 'multi']:
            if key:
                disk_path = os.path.join(self.cache_dir, key)
                if os.path.exists(disk_path):
                    os.remove(disk_path)
            else:
                for filename in os.listdir(self.cache_dir):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        self.logger.error(f"Disk cache deletion error: {e}")

def create_cache_manager(
    redis_host: str = 'localhost', 
    redis_port: int = 6379, 
    redis_db: int = 0,
    cache_dir: Optional[str] = None
) -> AdvancedCacheManager:
    """
    Factory method to create cache manager
    
    :param redis_host: Redis server host
    :param redis_port: Redis server port
    :param redis_db: Redis database number
    :param cache_dir: Directory for disk-based caching
    :return: Configured cache manager
    """
    return AdvancedCacheManager(
        redis_host, 
        redis_port, 
        redis_db, 
        cache_dir
    )
