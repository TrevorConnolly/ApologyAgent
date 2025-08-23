"""
Test suite for error handling and retry logic.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from production_utils import (
    AgentError, ValidationError, BrowserError, TimeoutError, NetworkError,
    ErrorCategory, categorize_exception, should_retry_error,
    production_retry, CircuitBreaker, safe_async_operation
)

class TestErrorCategorization:
    """Test error categorization logic."""
    
    def test_agent_error_creation(self):
        """Test AgentError creation with different parameters."""
        error = AgentError("Test message", ErrorCategory.RETRYABLE_NETWORK)
        assert error.message == "Test message"
        assert error.category == ErrorCategory.RETRYABLE_NETWORK
        assert error.original_error is None
        assert error.context == {}
        assert error.timestamp is not None
    
    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError("Invalid input", field="email", value="invalid@")
        assert error.message == "Invalid input"
        assert error.category == ErrorCategory.NON_RETRYABLE_VALIDATION
        assert error.context["field"] == "email"
        assert error.context["value"] == "invalid@"
    
    def test_browser_error_creation(self):
        """Test BrowserError creation."""
        # Retryable browser error
        error = BrowserError("Browser connection failed", retryable=True)
        assert error.category == ErrorCategory.RETRYABLE_BROWSER
        
        # Non-retryable browser error
        error = BrowserError("Invalid browser configuration", retryable=False)
        assert error.category == ErrorCategory.NON_RETRYABLE_PERMANENT
    
    def test_timeout_error_creation(self):
        """Test TimeoutError creation."""
        error = TimeoutError("Operation timed out", timeout_seconds=30.0, operation="page_load")
        assert error.category == ErrorCategory.RETRYABLE_TIMEOUT
        assert error.context["timeout_seconds"] == 30.0
        assert error.context["operation"] == "page_load"
    
    def test_network_error_creation(self):
        """Test NetworkError creation."""
        error = NetworkError("Connection refused", status_code=503, url="https://example.com")
        assert error.category == ErrorCategory.RETRYABLE_NETWORK
        assert error.context["status_code"] == 503
        assert error.context["url"] == "https://example.com"

class TestExceptionCategorization:
    """Test the categorize_exception function."""
    
    def test_categorize_network_errors(self):
        """Test categorization of network-related exceptions."""
        network_exceptions = [
            Exception("connection timeout"),
            Exception("DNS resolution failed"),
            Exception("network unreachable"),
            Exception("connection reset by peer"),
            Exception("service unavailable")
        ]
        
        for exc in network_exceptions:
            category = categorize_exception(exc)
            assert category == ErrorCategory.RETRYABLE_NETWORK
    
    def test_categorize_browser_errors(self):
        """Test categorization of browser-related exceptions."""
        browser_exceptions = [
            Exception("browser crashed"),
            Exception("chromium process failed"),
            Exception("playwright timeout"),
            Exception("page navigation failed"),
            Exception("element not found")
        ]
        
        for exc in browser_exceptions:
            category = categorize_exception(exc)
            assert category == ErrorCategory.RETRYABLE_BROWSER
    
    def test_categorize_auth_errors(self):
        """Test categorization of authentication errors."""
        auth_exceptions = [
            Exception("unauthorized access"),
            Exception("invalid api key"),
            Exception("forbidden operation"),
            Exception("authentication failed")
        ]
        
        for exc in auth_exceptions:
            category = categorize_exception(exc)
            assert category == ErrorCategory.NON_RETRYABLE_AUTH
    
    def test_categorize_validation_errors(self):
        """Test categorization of validation errors."""
        validation_exceptions = [
            Exception("validation failed"),
            Exception("invalid input format"),
            Exception("required field missing"),
            Exception("malformed request")
        ]
        
        for exc in validation_exceptions:
            category = categorize_exception(exc)
            assert category == ErrorCategory.NON_RETRYABLE_VALIDATION
    
    def test_categorize_unknown_errors(self):
        """Test categorization of unknown exceptions."""
        unknown_exceptions = [
            Exception("some random error"),
            Exception("unexpected failure"),
            ValueError("unknown value error")
        ]
        
        for exc in unknown_exceptions:
            category = categorize_exception(exc)
            assert category == ErrorCategory.UNKNOWN

class TestRetryLogic:
    """Test retry logic and decision making."""
    
    def test_should_retry_agent_errors(self):
        """Test retry decisions for AgentError instances."""
        # Retryable errors
        retryable_errors = [
            AgentError("Network issue", ErrorCategory.RETRYABLE_NETWORK),
            AgentError("Browser issue", ErrorCategory.RETRYABLE_BROWSER),
            AgentError("Timeout", ErrorCategory.RETRYABLE_TIMEOUT)
        ]
        
        for error in retryable_errors:
            assert should_retry_error(error) is True
        
        # Non-retryable errors
        non_retryable_errors = [
            AgentError("Validation failed", ErrorCategory.NON_RETRYABLE_VALIDATION),
            AgentError("Auth failed", ErrorCategory.NON_RETRYABLE_AUTH),
            AgentError("Permanent failure", ErrorCategory.NON_RETRYABLE_PERMANENT),
            AgentError("Unknown error", ErrorCategory.UNKNOWN)
        ]
        
        for error in non_retryable_errors:
            assert should_retry_error(error) is False
    
    def test_should_retry_regular_exceptions(self):
        """Test retry decisions for regular exceptions."""
        # Should retry network-like errors
        assert should_retry_error(Exception("connection timeout")) is True
        assert should_retry_error(Exception("browser failed")) is True
        
        # Should not retry auth-like errors
        assert should_retry_error(Exception("unauthorized")) is False
        assert should_retry_error(Exception("validation error")) is False
    
    @pytest.mark.asyncio
    async def test_production_retry_success(self):
        """Test successful operation with retry decorator."""
        call_count = 0
        
        @production_retry(max_attempts=3)
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("temporary network issue")
            return "success"
        
        result = await flaky_operation()
        assert result == "success"
        assert call_count == 2  # Failed once, then succeeded
    
    @pytest.mark.asyncio
    async def test_production_retry_exhausted(self):
        """Test retry exhaustion."""
        call_count = 0
        
        @production_retry(max_attempts=3)
        async def always_failing_operation():
            nonlocal call_count
            call_count += 1
            raise NetworkError("persistent network issue")
        
        with pytest.raises(NetworkError):
            await always_failing_operation()
        
        assert call_count == 3  # Should have tried 3 times
    
    @pytest.mark.asyncio
    async def test_production_retry_non_retryable(self):
        """Test that non-retryable errors are not retried."""
        call_count = 0
        
        @production_retry(max_attempts=3)
        async def validation_error_operation():
            nonlocal call_count
            call_count += 1
            raise ValidationError("invalid input")
        
        with pytest.raises(ValidationError):
            await validation_error_operation()
        
        assert call_count == 1  # Should not have retried

class TestCircuitBreaker:
    """Test the CircuitBreaker implementation."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_normal_operation(self):
        """Test circuit breaker in normal (closed) state."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        
        @breaker
        async def successful_operation():
            return "success"
        
        # Should work normally
        result = await successful_operation()
        assert result == "success"
        assert breaker.state == 'CLOSED'
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opening after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        
        @breaker
        async def failing_operation():
            raise Exception("operation failed")
        
        # Fail enough times to open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await failing_operation()
        
        assert breaker.state == 'OPEN'
        
        # Next call should be blocked
        with pytest.raises(AgentError) as excinfo:
            await failing_operation()
        
        assert "Circuit breaker is OPEN" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        call_count = 0
        
        @breaker
        async def recovering_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("still failing")
            return "recovered"
        
        # Fail to open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await recovering_operation()
        
        assert breaker.state == 'OPEN'
        
        # Wait for recovery timeout
        await asyncio.sleep(0.2)
        
        # Should transition to half-open and then succeed
        result = await recovering_operation()
        assert result == "recovered"
        assert breaker.state == 'CLOSED'
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_failure(self):
        """Test circuit breaker returning to open state on half-open failure."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        @breaker
        async def still_failing_operation():
            raise Exception("still failing")
        
        # Fail to open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await still_failing_operation()
        
        assert breaker.state == 'OPEN'
        
        # Wait for recovery timeout
        await asyncio.sleep(0.2)
        
        # Should transition to half-open, fail, and go back to open
        with pytest.raises(Exception):
            await still_failing_operation()
        
        assert breaker.state == 'OPEN'

class TestSafeAsyncOperation:
    """Test the safe_async_operation wrapper."""
    
    @pytest.mark.asyncio
    async def test_safe_operation_success(self):
        """Test successful operation wrapping."""
        async def successful_op(value):
            return f"processed: {value}"
        
        result = await safe_async_operation(successful_op, "test")
        assert result == "processed: test"
    
    @pytest.mark.asyncio
    async def test_safe_operation_exception_wrapping(self):
        """Test exception wrapping in safe operation."""
        async def failing_op():
            raise ValueError("original error")
        
        with pytest.raises(AgentError) as excinfo:
            await safe_async_operation(failing_op)
        
        error = excinfo.value
        assert "Operation failing_op failed" in error.message
        assert isinstance(error.original_error, ValueError)
        assert error.category == ErrorCategory.NON_RETRYABLE_VALIDATION  # ValueError categorized as validation

# Integration tests
class TestErrorHandlingIntegration:
    """Integration tests for complete error handling system."""
    
    @pytest.mark.asyncio
    async def test_layered_error_handling(self):
        """Test error handling through multiple layers."""
        # Simulate a complex operation with multiple potential failure points
        call_count = 0
        
        async def complex_operation():
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise NetworkError("network timeout")  # Should retry
            elif call_count == 2:
                raise BrowserError("browser connection lost")  # Should retry
            elif call_count == 3:
                return "success after retries"
        
        # Wrap with circuit breaker and retry logic
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=0.1)
        
        @breaker
        @production_retry(max_attempts=5, min_wait_seconds=0.01, max_wait_seconds=0.02)
        async def wrapped_operation():
            return await safe_async_operation(complex_operation)
        
        result = await wrapped_operation()
        assert result == "success after retries"
        assert call_count == 3
        assert breaker.state == 'CLOSED'
    
    @pytest.mark.asyncio
    async def test_non_retryable_error_flow(self):
        """Test that non-retryable errors bypass retry logic."""
        call_count = 0
        
        async def validation_failing_operation():
            nonlocal call_count
            call_count += 1
            raise ValidationError("invalid input format", field="date")
        
        @production_retry(max_attempts=3)
        async def wrapped_operation():
            return await safe_async_operation(validation_failing_operation)
        
        with pytest.raises(AgentError) as excinfo:
            await wrapped_operation()
        
        # Should not have retried
        assert call_count == 1
        
        # Should preserve the original error information
        error = excinfo.value
        assert error.category == ErrorCategory.NON_RETRYABLE_VALIDATION
        assert "invalid input format" in error.message
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry_interaction(self):
        """Test interaction between circuit breaker and retry logic."""
        call_count = 0
        
        async def intermittent_operation():
            nonlocal call_count
            call_count += 1
            
            # Fail for a while, then succeed
            if call_count < 8:
                raise NetworkError("intermittent network issue")
            return "finally succeeded"
        
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
        
        @breaker
        @production_retry(max_attempts=2, min_wait_seconds=0.01)
        async def wrapped_operation():
            return await safe_async_operation(intermittent_operation)
        
        # First few attempts should exhaust retries and open circuit
        with pytest.raises((NetworkError, AgentError)):
            await wrapped_operation()
        
        # Circuit should be open after failures
        assert breaker.state == 'OPEN'
        
        # Wait for recovery and reset call count for testing recovery
        await asyncio.sleep(0.2)
        call_count = 0
        
        # Should work after circuit recovers
        result = await wrapped_operation()
        assert result == "finally succeeded"
        assert breaker.state == 'CLOSED'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])