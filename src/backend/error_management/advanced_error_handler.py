import os
import sys
import traceback
import logging
import json
import time
from typing import Dict, Any, Optional, Callable, Union, List
import uuid
import asyncio
import functools
import sentry_sdk
from tenacity import retry, stop_after_attempt, wait_exponential
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

class AdvancedErrorHandler:
    """
    Comprehensive error handling and recovery system
    Supports multiple error management strategies
    """
    
    def __init__(self, 
                 log_dir: str = 'error_logs', 
                 sentry_dsn: Optional[str] = None,
                 max_retry_attempts: int = 3):
        """
        Initialize advanced error handler
        
        :param log_dir: Directory for storing error logs
        :param sentry_dsn: Sentry DSN for error tracking
        :param max_retry_attempts: Maximum number of retry attempts
        """
        # Create log directory
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Logging configuration
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Sentry initialization
        if sentry_dsn:
            sentry_sdk.init(dsn=sentry_dsn)
        
        # Retry configuration
        self.max_retry_attempts = max_retry_attempts
        
        # Thread pool for concurrent error handling
        self.thread_pool = ThreadPoolExecutor(max_workers=10)

    def log_error(self, 
                  error: Exception, 
                  context: Optional[Dict[str, Any]] = None) -> str:
        """
        Comprehensive error logging
        
        :param error: Exception to log
        :param context: Optional additional context
        :return: Unique error identifier
        """
        # Generate unique error ID
        error_id = str(uuid.uuid4())
        
        # Prepare error details
        error_details = {
            'error_id': error_id,
            'timestamp': time.time(),
            'type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        # Log to file
        log_file = os.path.join(
            self.log_dir, 
            f'error_{error_id}.json'
        )
        
        try:
            with open(log_file, 'w') as f:
                json.dump(error_details, f, indent=2)
            
            # Log to Sentry if configured
            if sentry_sdk.Hub.current:
                sentry_sdk.capture_exception(error)
            
            # Log to standard logging
            self.logger.error(
                f"Error logged: {error_id}\n"
                f"Type: {error_details['type']}\n"
                f"Message: {error_details['message']}"
            )
        
        except Exception as log_error:
            self.logger.error(f"Error logging failed: {log_error}")
        
        return error_id

    def retry_with_backoff(self, 
                            func: Optional[Callable] = None, 
                            max_attempts: Optional[int] = None,
                            base_wait: int = 1,
                            max_wait: int = 10):
        """
        Decorator for retry with exponential backoff
        
        :param func: Function to retry
        :param max_attempts: Maximum retry attempts
        :param base_wait: Base wait time between retries
        :param max_wait: Maximum wait time between retries
        :return: Decorated function
        """
        def decorator(f):
            @retry(
                stop=stop_after_attempt(max_attempts or self.max_retry_attempts),
                wait=wait_exponential(
                    multiplier=base_wait, 
                    max=max_wait
                )
            )
            def wrapper(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    # Log error
                    error_id = self.log_error(
                        e, 
                        context={
                            'function': f.__name__,
                            'args': args,
                            'kwargs': kwargs
                        }
                    )
                    raise RuntimeError(f"Retry failed. Error ID: {error_id}") from e
            return wrapper
        
        return decorator(func) if func else decorator

    def timeout_with_recovery(self, 
                               timeout: float = 30.0, 
                               recovery_func: Optional[Callable] = None):
        """
        Decorator for function timeout with optional recovery
        
        :param timeout: Timeout duration in seconds
        :param recovery_func: Optional recovery function
        :return: Decorated function
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    # Submit function to thread pool
                    future = self.thread_pool.submit(func, *args, **kwargs)
                    
                    try:
                        # Wait for result with timeout
                        result = future.result(timeout=timeout)
                        return result
                    
                    except FuturesTimeoutError:
                        # Timeout occurred
                        error_id = self.log_error(
                            TimeoutError(f"Function {func.__name__} timed out"),
                            context={
                                'timeout': timeout,
                                'function': func.__name__
                            }
                        )
                        
                        # Call recovery function if provided
                        if recovery_func:
                            return recovery_func(*args, **kwargs)
                        
                        raise TimeoutError(f"Operation timed out. Error ID: {error_id}")
                
                except Exception as e:
                    # Log unexpected errors
                    error_id = self.log_error(
                        e, 
                        context={
                            'function': func.__name__,
                            'args': args,
                            'kwargs': kwargs
                        }
                    )
                    raise RuntimeError(f"Unexpected error. Error ID: {error_id}") from e
            return wrapper
        return decorator

    async def async_retry_with_backoff(self, 
                                       func: Optional[Callable] = None, 
                                       max_attempts: Optional[int] = None,
                                       base_wait: int = 1,
                                       max_wait: int = 10):
        """
        Async decorator for retry with exponential backoff
        
        :param func: Async function to retry
        :param max_attempts: Maximum retry attempts
        :param base_wait: Base wait time between retries
        :param max_wait: Maximum wait time between retries
        :return: Decorated async function
        """
        def decorator(f):
            @functools.wraps(f)
            async def wrapper(*args, **kwargs):
                attempts = 0
                while attempts < (max_attempts or self.max_retry_attempts):
                    try:
                        return await f(*args, **kwargs)
                    except Exception as e:
                        attempts += 1
                        
                        # Log error
                        error_id = self.log_error(
                            e, 
                            context={
                                'function': f.__name__,
                                'args': args,
                                'kwargs': kwargs,
                                'attempt': attempts
                            }
                        )
                        
                        # Calculate wait time with exponential backoff
                        wait_time = min(
                            base_wait * (2 ** attempts), 
                            max_wait
                        )
                        
                        # Wait before next attempt
                        await asyncio.sleep(wait_time)
                
                # Final attempt fails
                raise RuntimeError(f"All retry attempts failed. Last Error ID: {error_id}")
            return wrapper
        
        return decorator(func) if func else decorator

    def global_exception_handler(self, 
                                 exc_type: Type[BaseException], 
                                 exc_value: BaseException, 
                                 exc_traceback: TracebackType):
        """
        Global exception handler
        
        :param exc_type: Exception type
        :param exc_value: Exception value
        :param exc_traceback: Exception traceback
        """
        # Log unhandled exception
        error_id = self.log_error(
            exc_value,
            context={
                'type': exc_type.__name__,
                'traceback': traceback.format_tb(exc_traceback)
            }
        )
        
        # Optionally send critical alert
        if sentry_sdk.Hub.current:
            sentry_sdk.capture_exception((exc_type, exc_value, exc_traceback))
        
        # Default behavior: log and exit
        self.logger.critical(
            f"Unhandled exception. Error ID: {error_id}\n"
            f"Type: {exc_type.__name__}\n"
            f"Message: {exc_value}"
        )
        
        # Optionally perform system-level recovery
        sys.exit(1)

def create_error_handler(
    log_dir: str = 'error_logs', 
    sentry_dsn: Optional[str] = None,
    max_retry_attempts: int = 3
) -> AdvancedErrorHandler:
    """
    Factory method to create error handler
    
    :param log_dir: Directory for storing error logs
    :param sentry_dsn: Sentry DSN for error tracking
    :param max_retry_attempts: Maximum number of retry attempts
    :return: Configured error handler
    """
    return AdvancedErrorHandler(
        log_dir, 
        sentry_dsn, 
        max_retry_attempts
    )
