"""
Production utilities for the Restaurant Kernel Agent.
Enhanced error handling, retry logic, and monitoring capabilities.
"""

import os
import asyncio
import logging
import time
import functools
from typing import Dict, Any, Optional, Callable, Union, List
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import re

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import backoff

# Configure logger for this module
logger = logging.getLogger(__name__)

class ErrorCategory(Enum):
    """Categorize errors for appropriate handling strategies."""
    RETRYABLE_NETWORK = "retryable_network"
    RETRYABLE_BROWSER = "retryable_browser"
    RETRYABLE_TIMEOUT = "retryable_timeout"
    NON_RETRYABLE_VALIDATION = "non_retryable_validation"
    NON_RETRYABLE_AUTH = "non_retryable_auth"
    NON_RETRYABLE_PERMANENT = "non_retryable_permanent"
    UNKNOWN = "unknown"

class AgentError(Exception):
    """Base exception for agent operations with error categorization."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN, 
                 original_error: Optional[Exception] = None, context: Optional[Dict] = None):
        self.message = message
        self.category = category
        self.original_error = original_error
        self.context = context or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

class ValidationError(AgentError):
    """Validation-specific error that should not be retried."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        context = {"field": field, "value": value} if field else {}
        super().__init__(message, ErrorCategory.NON_RETRYABLE_VALIDATION, context=context)

class BrowserError(AgentError):
    """Browser-specific error that may be retryable."""
    
    def __init__(self, message: str, retryable: bool = True, browser_context: Dict = None):
        category = ErrorCategory.RETRYABLE_BROWSER if retryable else ErrorCategory.NON_RETRYABLE_PERMANENT
        super().__init__(message, category, context=browser_context or {})

class TimeoutError(AgentError):
    """Timeout error that is typically retryable."""
    
    def __init__(self, message: str, timeout_seconds: float, operation: str = None):
        context = {"timeout_seconds": timeout_seconds, "operation": operation}
        super().__init__(message, ErrorCategory.RETRYABLE_TIMEOUT, context=context)

class NetworkError(AgentError):
    """Network-related error that is typically retryable."""
    
    def __init__(self, message: str, status_code: int = None, url: str = None):
        context = {"status_code": status_code, "url": url}
        super().__init__(message, ErrorCategory.RETRYABLE_NETWORK, context=context)

def categorize_exception(exception: Exception) -> ErrorCategory:
    """
    Categorize an exception to determine if it should be retried.
    
    Args:
        exception: The exception to categorize
        
    Returns:
        ErrorCategory indicating how the error should be handled
    """
    error_message = str(exception).lower()
    
    # Network-related errors (retryable)
    network_patterns = [
        "connection", "timeout", "network", "dns", "socket", 
        "unreachable", "reset", "refused", "unavailable"
    ]
    if any(pattern in error_message for pattern in network_patterns):
        return ErrorCategory.RETRYABLE_NETWORK
    
    # Browser-related errors (retryable)
    browser_patterns = [
        "browser", "chromium", "playwright", "page", "element", 
        "navigation", "screenshot", "session"
    ]
    if any(pattern in error_message for pattern in browser_patterns):
        return ErrorCategory.RETRYABLE_BROWSER
    
    # Authentication errors (non-retryable)
    auth_patterns = ["auth", "unauthorized", "forbidden", "invalid key", "invalid token"]
    if any(pattern in error_message for pattern in auth_patterns):
        return ErrorCategory.NON_RETRYABLE_AUTH
    
    # Validation errors (non-retryable)
    validation_patterns = ["validation", "invalid", "malformed", "required", "missing"]
    if any(pattern in error_message for pattern in validation_patterns):
        return ErrorCategory.NON_RETRYABLE_VALIDATION
    
    # Default to unknown (will be treated as non-retryable)
    return ErrorCategory.UNKNOWN

def should_retry_error(error: Exception) -> bool:
    """
    Determine if an error should be retried based on its category.
    
    Args:
        error: The exception to evaluate
        
    Returns:
        True if the error should be retried, False otherwise
    """
    if isinstance(error, AgentError):
        return error.category in [
            ErrorCategory.RETRYABLE_NETWORK,
            ErrorCategory.RETRYABLE_BROWSER,
            ErrorCategory.RETRYABLE_TIMEOUT
        ]
    
    # Categorize unknown exceptions
    category = categorize_exception(error)
    return category in [
        ErrorCategory.RETRYABLE_NETWORK,
        ErrorCategory.RETRYABLE_BROWSER,
        ErrorCategory.RETRYABLE_TIMEOUT
    ]

# Production-grade retry decorator using tenacity
def production_retry(
    max_attempts: int = 3,
    min_wait_seconds: float = 1.0,
    max_wait_seconds: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """
    Production-grade retry decorator with exponential backoff and jitter.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait_seconds: Minimum wait time between retries
        max_wait_seconds: Maximum wait time between retries
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to wait times
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(
            multiplier=min_wait_seconds,
            max=max_wait_seconds,
            exp_base=exponential_base,
            jitter=jitter
        ),
        retry=retry_if_exception_type(Exception) & should_retry_error,
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )

class CircuitBreaker:
    """
    Circuit breaker implementation for preventing cascading failures.
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0, 
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        
    def __call__(self, func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                    logger.info("Circuit breaker transitioning to HALF_OPEN state")
                else:
                    raise AgentError(
                        "Circuit breaker is OPEN - requests blocked",
                        ErrorCategory.NON_RETRYABLE_PERMANENT,
                        context={"circuit_breaker_state": self.state}
                    )
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
                
            except self.expected_exception as e:
                self._on_failure()
                raise
                
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt a reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
            logger.info("Circuit breaker reset to CLOSED state")
        self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

class RequestValidator:
    """
    Comprehensive input validation for restaurant reservation requests.
    """
    
    # Validation patterns
    DATE_PATTERNS = [
        r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
        r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
        r'^\d{1,2}/\d{1,2}/\d{4}$',  # M/D/YYYY
    ]
    
    TIME_PATTERNS = [
        r'^\d{1,2}:\d{2}\s?(AM|PM)$',  # 7:00 PM
        r'^\d{1,2}(AM|PM)$',           # 7PM
        r'^\d{1,2}:\d{2}$',            # 19:00 (24-hour)
    ]
    
    PHONE_PATTERN = r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    @classmethod
    def validate_date(cls, date_str: str) -> str:
        """
        Validate and normalize date string.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            Normalized date string
            
        Raises:
            ValidationError: If date is invalid
        """
        if not date_str or not isinstance(date_str, str):
            raise ValidationError("Date is required and must be a string", "date", date_str)
        
        date_str = date_str.strip()
        
        # Check if date matches any valid pattern
        if not any(re.match(pattern, date_str, re.IGNORECASE) for pattern in cls.DATE_PATTERNS):
            raise ValidationError(
                f"Invalid date format. Expected formats: YYYY-MM-DD, MM/DD/YYYY, or M/D/YYYY",
                "date",
                date_str
            )
        
        # Additional validation: check if date is not in the past
        # (This could be enhanced with actual date parsing)
        return date_str
    
    @classmethod
    def validate_time(cls, time_str: str) -> str:
        """
        Validate and normalize time string.
        
        Args:
            time_str: Time string to validate
            
        Returns:
            Normalized time string
            
        Raises:
            ValidationError: If time is invalid
        """
        if not time_str or not isinstance(time_str, str):
            raise ValidationError("Time is required and must be a string", "time", time_str)
        
        time_str = time_str.strip().upper()
        
        # Check if time matches any valid pattern
        if not any(re.match(pattern, time_str, re.IGNORECASE) for pattern in cls.TIME_PATTERNS):
            raise ValidationError(
                f"Invalid time format. Expected formats: 7:00 PM, 7PM, or 19:00",
                "time",
                time_str
            )
        
        return time_str
    
    @classmethod
    def validate_party_size(cls, party_size: Union[int, str]) -> int:
        """
        Validate party size.
        
        Args:
            party_size: Number of people for reservation
            
        Returns:
            Validated party size as integer
            
        Raises:
            ValidationError: If party size is invalid
        """
        try:
            size = int(party_size)
            if size < 1:
                raise ValidationError("Party size must be at least 1", "party_size", party_size)
            if size > 20:
                raise ValidationError("Party size cannot exceed 20", "party_size", party_size)
            return size
        except (ValueError, TypeError):
            raise ValidationError("Party size must be a number", "party_size", party_size)
    
    @classmethod
    def validate_location(cls, location: str) -> str:
        """
        Validate location string.
        
        Args:
            location: Location for restaurant search
            
        Returns:
            Normalized location string
            
        Raises:
            ValidationError: If location is invalid
        """
        if not location or not isinstance(location, str):
            raise ValidationError("Location is required and must be a string", "location", location)
        
        location = location.strip()
        
        if len(location) < 2:
            raise ValidationError("Location must be at least 2 characters", "location", location)
        
        if len(location) > 100:
            raise ValidationError("Location cannot exceed 100 characters", "location", location)
        
        return location
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        Validate email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            Normalized email address
            
        Raises:
            ValidationError: If email is invalid
        """
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required and must be a string", "inbox_id", email)
        
        email = email.strip().lower()
        
        if not re.match(cls.EMAIL_PATTERN, email):
            raise ValidationError("Invalid email format", "inbox_id", email)
        
        return email
    
    @classmethod
    def validate_phone(cls, phone: str) -> str:
        """
        Validate phone number.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Normalized phone number
            
        Raises:
            ValidationError: If phone is invalid
        """
        if not phone or not isinstance(phone, str):
            raise ValidationError("Phone number is required and must be a string", "phone", phone)
        
        phone = phone.strip()
        
        if not re.match(cls.PHONE_PATTERN, phone):
            raise ValidationError("Invalid phone number format", "phone", phone)
        
        # Normalize to +1XXXXXXXXXX format
        digits = re.sub(r'[^\d]', '', phone)
        if len(digits) == 10:
            phone = f"+1{digits}"
        elif len(digits) == 11 and digits[0] == '1':
            phone = f"+{digits}"
        
        return phone
    
    @classmethod
    def validate_name(cls, name: str, field_name: str) -> str:
        """
        Validate first/last name.
        
        Args:
            name: Name to validate
            field_name: Field name for error reporting
            
        Returns:
            Normalized name
            
        Raises:
            ValidationError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValidationError(f"{field_name} is required and must be a string", field_name, name)
        
        name = name.strip()
        
        if len(name) < 1:
            raise ValidationError(f"{field_name} cannot be empty", field_name, name)
        
        if len(name) > 50:
            raise ValidationError(f"{field_name} cannot exceed 50 characters", field_name, name)
        
        # Check for potentially harmful characters
        if re.search(r'[<>\"\'&]', name):
            raise ValidationError(f"{field_name} contains invalid characters", field_name, name)
        
        return name

class PerformanceMonitor:
    """
    Monitor and track performance metrics for the agent.
    """
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation_name: str, context: Dict = None) -> str:
        """Start timing an operation."""
        timer_id = f"{operation_name}_{int(time.time() * 1000)}"
        self.start_times[timer_id] = {
            'start_time': time.time(),
            'operation': operation_name,
            'context': context or {}
        }
        return timer_id
    
    def end_timer(self, timer_id: str) -> float:
        """End timing an operation and record the metric."""
        if timer_id not in self.start_times:
            logger.warning(f"Timer {timer_id} not found")
            return 0.0
        
        start_info = self.start_times.pop(timer_id)
        duration = time.time() - start_info['start_time']
        
        operation = start_info['operation']
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        metric_entry = {
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat(),
            'context': start_info['context']
        }
        
        self.metrics[operation].append(metric_entry)
        
        logger.info(f"Operation '{operation}' completed in {duration:.2f}s", 
                   extra={'performance_metric': metric_entry})
        
        return duration
    
    def get_metrics(self) -> Dict:
        """Get all collected metrics."""
        summary = {}
        for operation, entries in self.metrics.items():
            if entries:
                durations = [e['duration'] for e in entries]
                summary[operation] = {
                    'count': len(durations),
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'total_duration': sum(durations),
                    'last_execution': entries[-1]['timestamp']
                }
        return summary
    
    def context_manager(self, operation_name: str, context: Dict = None):
        """Context manager for timing operations."""
        return TimingContext(self, operation_name, context)

class TimingContext:
    """Context manager for performance timing."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str, context: Dict = None):
        self.monitor = monitor
        self.operation_name = operation_name
        self.context = context
        self.timer_id = None
    
    def __enter__(self):
        self.timer_id = self.monitor.start_timer(self.operation_name, self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer_id:
            self.monitor.end_timer(self.timer_id)

def sanitize_input(value: Any, max_length: int = 1000) -> str:
    """
    Sanitize input to prevent injection attacks and ensure safe logging.
    
    Args:
        value: Input value to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string value
    """
    if value is None:
        return ""
    
    # Convert to string and truncate
    sanitized = str(value)[:max_length]
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>\"\'&\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    return sanitized.strip()

def generate_request_id() -> str:
    """Generate a unique request ID for tracking."""
    timestamp = int(time.time() * 1000)
    return f"req_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}"

async def safe_async_operation(operation: Callable, *args, **kwargs) -> Any:
    """
    Safely execute an async operation with comprehensive error handling.
    
    Args:
        operation: Async function to execute
        *args: Positional arguments for the operation
        **kwargs: Keyword arguments for the operation
        
    Returns:
        Operation result
        
    Raises:
        AgentError: Categorized error based on the original exception
    """
    try:
        return await operation(*args, **kwargs)
    except Exception as e:
        category = categorize_exception(e)
        raise AgentError(
            f"Operation {operation.__name__} failed: {str(e)}",
            category=category,
            original_error=e
        )

# Global performance monitor instance
performance_monitor = PerformanceMonitor()