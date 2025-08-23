"""
Test suite for input validation and security features.
"""

import pytest
from datetime import datetime
from production_utils import RequestValidator, ValidationError, sanitize_input

class TestRequestValidator:
    """Test the RequestValidator class."""
    
    def test_validate_date_valid_formats(self):
        """Test valid date formats."""
        # Test YYYY-MM-DD format
        assert RequestValidator.validate_date("2025-08-31") == "2025-08-31"
        assert RequestValidator.validate_date("2025-12-25") == "2025-12-25"
        
        # Test MM/DD/YYYY format
        assert RequestValidator.validate_date("08/31/2025") == "08/31/2025"
        assert RequestValidator.validate_date("12/25/2025") == "12/25/2025"
        
        # Test M/D/YYYY format
        assert RequestValidator.validate_date("8/31/2025") == "8/31/2025"
        assert RequestValidator.validate_date("12/5/2025") == "12/5/2025"
    
    def test_validate_date_invalid_formats(self):
        """Test invalid date formats raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_date("invalid-date")
        assert "Invalid date format" in str(excinfo.value)
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_date("2025/08/31")  # Wrong separator
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_date("31-08-2025")  # Wrong order
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_date("")  # Empty string
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_date(None)  # None value
    
    def test_validate_time_valid_formats(self):
        """Test valid time formats."""
        # Test AM/PM formats
        assert RequestValidator.validate_time("7PM") == "7PM"
        assert RequestValidator.validate_time("7:30 PM") == "7:30 PM"
        assert RequestValidator.validate_time("12:00 AM") == "12:00 AM"
        
        # Test 24-hour format
        assert RequestValidator.validate_time("19:00") == "19:00"
        assert RequestValidator.validate_time("07:30") == "07:30"
        
        # Test case insensitive
        assert RequestValidator.validate_time("7pm") == "7PM"
        assert RequestValidator.validate_time("7:30 pm") == "7:30 PM"
    
    def test_validate_time_invalid_formats(self):
        """Test invalid time formats raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_time("invalid-time")
        assert "Invalid time format" in str(excinfo.value)
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_time("25:00")  # Invalid hour
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_time("7:60 PM")  # Invalid minute
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_time("")  # Empty string
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_time(None)  # None value
    
    def test_validate_party_size_valid(self):
        """Test valid party sizes."""
        assert RequestValidator.validate_party_size(1) == 1
        assert RequestValidator.validate_party_size(2) == 2
        assert RequestValidator.validate_party_size(10) == 10
        assert RequestValidator.validate_party_size(20) == 20
        
        # Test string inputs
        assert RequestValidator.validate_party_size("5") == 5
        assert RequestValidator.validate_party_size("15") == 15
    
    def test_validate_party_size_invalid(self):
        """Test invalid party sizes raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_party_size(0)
        assert "must be at least 1" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_party_size(21)
        assert "cannot exceed 20" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_party_size("invalid")
        assert "must be a number" in str(excinfo.value)
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_party_size(None)
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_party_size(-5)
    
    def test_validate_location_valid(self):
        """Test valid locations."""
        assert RequestValidator.validate_location("San Francisco") == "San Francisco"
        assert RequestValidator.validate_location("New York, NY") == "New York, NY"
        assert RequestValidator.validate_location("  Los Angeles  ") == "Los Angeles"  # Trimmed
    
    def test_validate_location_invalid(self):
        """Test invalid locations raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_location("")
        assert "Location is required" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_location("A")
        assert "at least 2 characters" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_location("A" * 101)
        assert "cannot exceed 100 characters" in str(excinfo.value)
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_location(None)
    
    def test_validate_email_valid(self):
        """Test valid email addresses."""
        assert RequestValidator.validate_email("test@example.com") == "test@example.com"
        assert RequestValidator.validate_email("user@agentmail.to") == "user@agentmail.to"
        assert RequestValidator.validate_email("  TEST@EXAMPLE.COM  ") == "test@example.com"  # Normalized
    
    def test_validate_email_invalid(self):
        """Test invalid email addresses raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_email("invalid-email")
        assert "Invalid email format" in str(excinfo.value)
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_email("@example.com")
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_email("test@")
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_email("")
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_email(None)
    
    def test_validate_phone_valid(self):
        """Test valid phone numbers."""
        # Test various formats
        assert RequestValidator.validate_phone("+14155551234") == "+14155551234"
        assert RequestValidator.validate_phone("4155551234") == "+14155551234"
        assert RequestValidator.validate_phone("14155551234") == "+14155551234"
        assert RequestValidator.validate_phone("(415) 555-1234") == "+14155551234"
        assert RequestValidator.validate_phone("415-555-1234") == "+14155551234"
        assert RequestValidator.validate_phone("415.555.1234") == "+14155551234"
    
    def test_validate_phone_invalid(self):
        """Test invalid phone numbers raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_phone("invalid-phone")
        assert "Invalid phone number format" in str(excinfo.value)
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_phone("123")  # Too short
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_phone("")  # Empty
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_phone(None)  # None
    
    def test_validate_name_valid(self):
        """Test valid names."""
        assert RequestValidator.validate_name("John", "first_name") == "John"
        assert RequestValidator.validate_name("Smith-Jones", "last_name") == "Smith-Jones"
        assert RequestValidator.validate_name("  Mary  ", "first_name") == "Mary"  # Trimmed
    
    def test_validate_name_invalid(self):
        """Test invalid names raise ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_name("", "first_name")
        assert "cannot be empty" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_name("A" * 51, "first_name")
        assert "cannot exceed 50 characters" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            RequestValidator.validate_name("John<script>", "first_name")
        assert "contains invalid characters" in str(excinfo.value)
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_name(None, "first_name")

class TestInputSanitization:
    """Test input sanitization functions."""
    
    def test_sanitize_input_normal(self):
        """Test normal input sanitization."""
        assert sanitize_input("Hello World") == "Hello World"
        assert sanitize_input("Restaurant Name") == "Restaurant Name"
        assert sanitize_input("  Trimmed  ") == "Trimmed"
    
    def test_sanitize_input_dangerous_chars(self):
        """Test removal of potentially dangerous characters."""
        assert sanitize_input("Hello<script>alert('xss')</script>") == "Helloscriptalert('xss')/script"
        assert sanitize_input("Test\"quote'test") == "Testquotetest"
        assert sanitize_input("Test&amp;test") == "Testamptest"
        assert sanitize_input("Test\x00\x01\x02") == "Test"  # Control characters
    
    def test_sanitize_input_length_limit(self):
        """Test length limiting."""
        long_input = "A" * 1500
        result = sanitize_input(long_input, max_length=1000)
        assert len(result) == 1000
        assert result == "A" * 1000
    
    def test_sanitize_input_none_empty(self):
        """Test handling of None and empty values."""
        assert sanitize_input(None) == ""
        assert sanitize_input("") == ""
        assert sanitize_input(0) == "0"
        assert sanitize_input(False) == "False"

# Integration tests
class TestValidationIntegration:
    """Integration tests for the complete validation system."""
    
    def test_complete_valid_request(self):
        """Test validation of a complete valid request."""
        request_data = {
            "date": "2025-08-31",
            "time": "7PM",
            "party_size": 2,
            "location": "San Francisco",
            "inbox_id": "test@agentmail.to",
            "phone": "4155551234",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        # Should not raise any exceptions
        validated_date = RequestValidator.validate_date(request_data["date"])
        validated_time = RequestValidator.validate_time(request_data["time"])
        validated_party = RequestValidator.validate_party_size(request_data["party_size"])
        validated_location = RequestValidator.validate_location(request_data["location"])
        validated_email = RequestValidator.validate_email(request_data["inbox_id"])
        validated_phone = RequestValidator.validate_phone(request_data["phone"])
        validated_first = RequestValidator.validate_name(request_data["first_name"], "first_name")
        validated_last = RequestValidator.validate_name(request_data["last_name"], "last_name")
        
        assert validated_date == "2025-08-31"
        assert validated_time == "7PM"
        assert validated_party == 2
        assert validated_location == "San Francisco"
        assert validated_email == "test@agentmail.to"
        assert validated_phone == "+14155551234"
        assert validated_first == "John"
        assert validated_last == "Doe"
    
    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are properly categorized."""
        # Test various invalid inputs
        invalid_requests = [
            {"field": "date", "value": "invalid", "validator": RequestValidator.validate_date},
            {"field": "time", "value": "25:00", "validator": RequestValidator.validate_time},
            {"field": "party_size", "value": 0, "validator": RequestValidator.validate_party_size},
            {"field": "location", "value": "", "validator": RequestValidator.validate_location},
            {"field": "email", "value": "invalid-email", "validator": RequestValidator.validate_email},
            {"field": "phone", "value": "123", "validator": RequestValidator.validate_phone},
        ]
        
        for request in invalid_requests:
            with pytest.raises(ValidationError) as excinfo:
                if request["field"] in ["first_name", "last_name"]:
                    request["validator"](request["value"], request["field"])
                else:
                    request["validator"](request["value"])
            
            # Verify the error contains field information
            error = excinfo.value
            assert error.category.value == "non_retryable_validation"
            assert error.message  # Should have a descriptive message
    
    def test_security_sanitization(self):
        """Test security-focused input sanitization."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "{{7*7}}",  # Template injection
            "../../../etc/passwd",  # Path traversal
            "javascript:alert('xss')",
            "onload=alert('xss')",
        ]
        
        for malicious_input in malicious_inputs:
            sanitized = sanitize_input(malicious_input)
            
            # Should not contain dangerous characters
            assert "<" not in sanitized
            assert ">" not in sanitized
            assert "'" not in sanitized
            assert '"' not in sanitized
            assert "&" not in sanitized
            
            # Should not be empty (still contains some content)
            assert len(sanitized) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])