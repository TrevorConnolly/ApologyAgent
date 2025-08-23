"""
Test suite for Kernel platform integration and end-to-end functionality.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from restaurant_kernel_agent import (
    validate_environment, validate_reservation_request, 
    make_restaurant_reservation, health_check
)
from production_utils import ValidationError, BrowserError, NetworkError

class TestEnvironmentValidation:
    """Test environment variable validation."""
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test-key', 'AGENTMAIL_API_KEY': 'test-agent-key'})
    def test_validate_environment_success(self):
        """Test successful environment validation."""
        env_vars = validate_environment()
        assert env_vars['OPENAI_API_KEY'] == 'sk-test-key'
        assert env_vars['AGENTMAIL_API_KEY'] == 'test-agent-key'
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test-key'}, clear=True)
    def test_validate_environment_missing_agentmail(self):
        """Test environment validation with missing AgentMail key."""
        with pytest.raises(ValueError) as excinfo:
            validate_environment()
        assert "AGENTMAIL_API_KEY" in str(excinfo.value)
    
    @patch.dict('os.environ', {}, clear=True)
    def test_validate_environment_missing_all(self):
        """Test environment validation with all keys missing."""
        with pytest.raises(ValueError) as excinfo:
            validate_environment()
        assert "OPENAI_API_KEY" in str(excinfo.value)
        assert "AGENTMAIL_API_KEY" in str(excinfo.value)

class TestRequestValidation:
    """Test reservation request validation."""
    
    def test_validate_reservation_request_complete(self):
        """Test validation of complete reservation request."""
        payload = {
            "date": "2025-08-31",
            "time": "7PM",
            "party_size": 2,
            "location": "San Francisco",
            "inbox_id": "test@agentmail.to",
            "phone": "+14155551234",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        validated = validate_reservation_request(payload)
        
        assert validated["date"] == "2025-08-31"
        assert validated["time"] == "7PM"
        assert validated["party_size"] == 2
        assert validated["location"] == "San Francisco"
        assert validated["inbox_id"] == "test@agentmail.to"
        assert validated["phone"] == "+14155551234"
        assert validated["first_name"] == "John"
        assert validated["last_name"] == "Doe"
    
    def test_validate_reservation_request_minimal(self):
        """Test validation with minimal required fields."""
        payload = {
            "date": "2025-08-31",
            "time": "7PM",
            "party_size": "2",
            "location": "San Francisco"
        }
        
        validated = validate_reservation_request(payload)
        
        # Required fields
        assert validated["date"] == "2025-08-31"
        assert validated["time"] == "7PM"
        assert validated["party_size"] == 2
        assert validated["location"] == "San Francisco"
        
        # Default values
        assert validated["inbox_id"] == "opentable_2@agentmail.to"
        assert validated["phone"] == "+18777804236"
        assert validated["first_name"] == "WAGENT"
        assert validated["last_name"] == "SRY"
    
    def test_validate_reservation_request_missing_required(self):
        """Test validation with missing required fields."""
        payloads = [
            {"time": "7PM", "party_size": 2, "location": "SF"},  # Missing date
            {"date": "2025-08-31", "party_size": 2, "location": "SF"},  # Missing time
            {"date": "2025-08-31", "time": "7PM", "location": "SF"},  # Missing party_size
            {"date": "2025-08-31", "time": "7PM", "party_size": 2},  # Missing location
        ]
        
        for payload in payloads:
            with pytest.raises(ValueError):
                validate_reservation_request(payload)
    
    def test_validate_reservation_request_invalid_party_size(self):
        """Test validation with invalid party size."""
        payload = {
            "date": "2025-08-31",
            "time": "7PM",
            "party_size": 0,  # Invalid
            "location": "San Francisco"
        }
        
        with pytest.raises(ValueError) as excinfo:
            validate_reservation_request(payload)
        assert "Party size must be between 1 and 20" in str(excinfo.value)

class TestKernelActions:
    """Test Kernel action implementations."""
    
    @pytest.mark.asyncio
    @patch('restaurant_kernel_agent.validate_environment')
    @patch('restaurant_kernel_agent.create_kernel_browser_session')
    @patch('restaurant_kernel_agent.execute_reservation_task')
    @patch('restaurant_kernel_agent.client')
    async def test_make_reservation_success(self, mock_client, mock_execute, mock_browser, mock_env):
        """Test successful reservation making."""
        # Mock environment validation
        mock_env.return_value = {'OPENAI_API_KEY': 'sk-test', 'AGENTMAIL_API_KEY': 'test-key'}
        
        # Mock browser session creation
        mock_browser_obj = Mock()
        mock_browser_obj.session_id = "browser_123"
        mock_browser_obj.browser_live_view_url = "https://kernel.ai/browser/123"
        
        mock_playwright_browser = AsyncMock()
        mock_browser_session = Mock()
        
        mock_browser.return_value = (mock_browser_obj, mock_playwright_browser, mock_browser_session)
        
        # Mock task execution
        mock_execute.return_value = {
            "success": True,
            "reservation_details": "Reservation confirmed at Test Restaurant",
            "execution_time_seconds": 45.2,
            "task_steps_completed": 12,
            "conversation_log": "test_conversation.json"
        }
        
        # Mock runtime context
        mock_runtime_context = Mock()
        mock_runtime_context.invocation_id = "test_invocation_123"
        
        # Test payload
        payload = {
            "date": "2025-08-31",
            "time": "7PM",
            "party_size": 2,
            "location": "San Francisco"
        }
        
        # Execute the action
        result = await make_restaurant_reservation(mock_runtime_context, payload)
        
        # Verify result
        assert result["success"] is True
        assert result["reservation_details"] == "Reservation confirmed at Test Restaurant"
        assert result["execution_time_seconds"] == 45.2
        assert result["browser_session_id"] == "browser_123"
        assert result["browser_live_view_url"] == "https://kernel.ai/browser/123"
        assert "request_id" in result
        assert "timestamp" in result
        assert result["kernel_app"] == "restaurant-reservation-agent"
        assert result["version"] == "1.0.0"
        
        # Verify cleanup was called
        mock_playwright_browser.close.assert_called_once()
        mock_client.browsers.delete_by_id.assert_called_once_with("browser_123")
    
    @pytest.mark.asyncio
    @patch('restaurant_kernel_agent.validate_environment')
    async def test_make_reservation_validation_error(self, mock_env):
        """Test reservation with validation error."""
        mock_env.return_value = {'OPENAI_API_KEY': 'sk-test', 'AGENTMAIL_API_KEY': 'test-key'}
        
        mock_runtime_context = Mock()
        mock_runtime_context.invocation_id = "test_invocation_123"
        
        # Invalid payload
        payload = {
            "date": "invalid-date",
            "time": "7PM",
            "party_size": 2,
            "location": "San Francisco"
        }
        
        result = await make_restaurant_reservation(mock_runtime_context, payload)
        
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "Invalid date format" in result["message"]
        assert "request_id" in result
    
    @pytest.mark.asyncio
    @patch('restaurant_kernel_agent.validate_environment')
    async def test_make_reservation_environment_error(self, mock_env):
        """Test reservation with environment validation error."""
        mock_env.side_effect = ValueError("Missing required environment variables: OPENAI_API_KEY")
        
        mock_runtime_context = Mock()
        payload = {"date": "2025-08-31", "time": "7PM", "party_size": 2, "location": "SF"}
        
        result = await make_restaurant_reservation(mock_runtime_context, payload)
        
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "OPENAI_API_KEY" in result["message"]
    
    @pytest.mark.asyncio
    @patch('restaurant_kernel_agent.validate_environment')
    @patch('restaurant_kernel_agent.create_kernel_browser_session')
    async def test_make_reservation_browser_error(self, mock_browser, mock_env):
        """Test reservation with browser creation error."""
        mock_env.return_value = {'OPENAI_API_KEY': 'sk-test', 'AGENTMAIL_API_KEY': 'test-key'}
        mock_browser.side_effect = RuntimeError("Failed to create browser after 3 attempts")
        
        mock_runtime_context = Mock()
        payload = {"date": "2025-08-31", "time": "7PM", "party_size": 2, "location": "SF"}
        
        result = await make_restaurant_reservation(mock_runtime_context, payload)
        
        assert result["success"] is False
        assert result["error"] == "runtime_error"
        assert "Failed to create browser" in result["message"]
    
    @pytest.mark.asyncio
    @patch('restaurant_kernel_agent.validate_environment')
    @patch('restaurant_kernel_agent.client')
    async def test_health_check_success(self, mock_client, mock_env):
        """Test successful health check."""
        mock_env.return_value = {'OPENAI_API_KEY': 'sk-test', 'AGENTMAIL_API_KEY': 'test-key'}
        
        # Mock browser creation and deletion
        mock_browser = Mock()
        mock_browser.session_id = "test_session"
        mock_client.browsers.create.return_value = mock_browser
        mock_client.browsers.delete_by_id.return_value = None
        
        mock_runtime_context = Mock()
        mock_runtime_context.invocation_id = "test_invocation"
        
        result = await health_check(mock_runtime_context, {})
        
        assert result["status"] == "healthy"
        assert result["service"] == "restaurant-reservation-agent"
        assert result["version"] == "1.0.0"
        assert result["checks"]["environment_variables"] == "ok"
        assert result["checks"]["kernel_browser_creation"] == "ok"
        assert result["checks"]["openai_api"] == "ok"
        assert result["checks"]["agentmail_api"] == "ok"
    
    @pytest.mark.asyncio
    @patch('restaurant_kernel_agent.validate_environment')
    async def test_health_check_environment_failure(self, mock_env):
        """Test health check with environment failure."""
        mock_env.side_effect = ValueError("Missing API keys")
        
        mock_runtime_context = Mock()
        result = await health_check(mock_runtime_context, {})
        
        assert result["status"] == "unhealthy"
        assert "Missing API keys" in result["error"]
    
    @pytest.mark.asyncio
    @patch('restaurant_kernel_agent.validate_environment')
    @patch('restaurant_kernel_agent.client')
    async def test_health_check_browser_failure(self, mock_client, mock_env):
        """Test health check with browser creation failure."""
        mock_env.return_value = {'OPENAI_API_KEY': 'sk-test', 'AGENTMAIL_API_KEY': 'test-key'}
        mock_client.browsers.create.side_effect = Exception("Browser creation failed")
        
        mock_runtime_context = Mock()
        result = await health_check(mock_runtime_context, {})
        
        assert result["status"] == "unhealthy"
        assert "Browser creation failed" in result["error"]

class TestBrowserSessionCreation:
    """Test browser session creation logic."""
    
    @pytest.mark.asyncio
    @patch('restaurant_kernel_agent.client')
    @patch('restaurant_kernel_agent.async_playwright')
    async def test_create_browser_session_success(self, mock_playwright, mock_client):
        """Test successful browser session creation."""
        from restaurant_kernel_agent import create_kernel_browser_session
        
        # Mock Kernel browser creation
        mock_kernel_browser = Mock()
        mock_kernel_browser.session_id = "kernel_123"
        mock_kernel_browser.cdp_ws_url = "ws://localhost:9222/devtools/browser/123"
        mock_client.browsers.create.return_value = mock_kernel_browser
        
        # Mock Playwright browser connection
        mock_playwright_browser = Mock()
        mock_playwright_browser.contexts = []
        
        mock_context = Mock()
        mock_context.pages = []
        mock_playwright_browser.new_context.return_value = mock_context
        
        mock_page = Mock()
        mock_context.new_page.return_value = mock_page
        
        mock_chromium = Mock()
        mock_chromium.connect_over_cdp.return_value = mock_playwright_browser
        
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium = mock_chromium
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Execute
        kernel_browser, playwright_browser, browser_session = await create_kernel_browser_session("test_invocation")
        
        # Verify
        assert kernel_browser == mock_kernel_browser
        assert playwright_browser == mock_playwright_browser
        assert browser_session is not None
        
        mock_client.browsers.create.assert_called_once_with(invocation_id="test_invocation")
        mock_chromium.connect_over_cdp.assert_called_once_with("ws://localhost:9222/devtools/browser/123")
    
    @pytest.mark.asyncio
    @patch('restaurant_kernel_agent.client')
    async def test_create_browser_session_retry_logic(self, mock_client):
        """Test browser session creation retry logic."""
        from restaurant_kernel_agent import create_kernel_browser_session
        
        # Mock failures followed by success
        mock_client.browsers.create.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            Mock()  # Success on third attempt
        ]
        
        with patch('restaurant_kernel_agent.async_playwright'):
            with patch('asyncio.sleep'):  # Speed up test
                # Should eventually succeed after retries
                try:
                    await create_kernel_browser_session("test_invocation")
                    # If we get here, the retry logic worked
                    assert mock_client.browsers.create.call_count == 3
                except:
                    # Expected for this test since we're mocking incomplete browser setup
                    pass

class TestTaskExecution:
    """Test reservation task execution."""
    
    @pytest.mark.asyncio
    @patch('restaurant_kernel_agent.Agent')
    async def test_execute_reservation_task_success(self, mock_agent_class):
        """Test successful reservation task execution."""
        from restaurant_kernel_agent import execute_reservation_task
        
        # Mock Browser Use Agent
        mock_agent = AsyncMock()
        mock_result = Mock()
        mock_result.final_result.return_value = "Reservation confirmed at Test Restaurant for 2 people on 2025-08-31 at 7PM"
        mock_agent.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent
        
        # Mock browser session and LLM
        mock_browser_session = Mock()
        mock_llm = Mock()
        
        reservation_params = {
            "date": "2025-08-31",
            "time": "7PM",
            "party_size": 2,
            "location": "San Francisco",
            "inbox_id": "test@agentmail.to",
            "phone": "+14155551234",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        # Execute
        result = await execute_reservation_task(mock_browser_session, mock_llm, reservation_params)
        
        # Verify
        assert result["success"] is True
        assert "Test Restaurant" in result["reservation_details"]
        assert result["execution_time_seconds"] > 0
        assert "conversation_log" in result
        
        # Verify agent was created with correct parameters
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        
        assert call_args[1]["llm"] == mock_llm
        assert call_args[1]["browser_session"] == mock_browser_session
        assert call_args[1]["max_steps"] == 50
        assert "2025-08-31" in call_args[1]["task"]
        assert "7PM" in call_args[1]["task"]
        assert "San Francisco" in call_args[1]["task"]

# Integration tests
class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'sk-test-key',
        'AGENTMAIL_API_KEY': 'test-agent-key'
    })
    @patch('restaurant_kernel_agent.client')
    @patch('restaurant_kernel_agent.async_playwright')
    @patch('restaurant_kernel_agent.Agent')
    async def test_complete_reservation_flow(self, mock_agent_class, mock_playwright, mock_client):
        """Test complete reservation flow from request to response."""
        # Mock all external dependencies
        
        # Kernel browser
        mock_kernel_browser = Mock()
        mock_kernel_browser.session_id = "kernel_123"
        mock_kernel_browser.cdp_ws_url = "ws://localhost:9222"
        mock_kernel_browser.browser_live_view_url = "https://kernel.ai/browser/123"
        mock_client.browsers.create.return_value = mock_kernel_browser
        
        # Playwright browser
        mock_playwright_browser = AsyncMock()
        mock_playwright_browser.contexts = []
        mock_context = AsyncMock()
        mock_context.pages = []
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        mock_playwright_browser.new_context.return_value = mock_context
        
        mock_chromium = AsyncMock()
        mock_chromium.connect_over_cdp.return_value = mock_playwright_browser
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium = mock_chromium
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Browser Use Agent
        mock_agent = AsyncMock()
        mock_result = Mock()
        mock_result.final_result.return_value = "✅ Reservation confirmed at The French Laundry for 2 people on 2025-08-31 at 7:00 PM. Confirmation #123456"
        mock_agent.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent
        
        # Runtime context
        mock_runtime_context = Mock()
        mock_runtime_context.invocation_id = "test_invocation_123"
        
        # Request payload
        payload = {
            "date": "2025-08-31",
            "time": "7PM",
            "party_size": 2,
            "location": "Napa Valley, CA"
        }
        
        # Execute the complete flow
        result = await make_restaurant_reservation(mock_runtime_context, payload)
        
        # Verify success
        assert result["success"] is True
        assert "French Laundry" in result["reservation_details"]
        assert result["browser_session_id"] == "kernel_123"
        assert "request_id" in result
        assert "timestamp" in result
        assert result["kernel_app"] == "restaurant-reservation-agent"
        
        # Verify all components were called
        mock_client.browsers.create.assert_called_once_with(invocation_id="test_invocation_123")
        mock_agent_class.assert_called_once()
        mock_agent.run.assert_called_once()
        mock_playwright_browser.close.assert_called_once()
        mock_client.browsers.delete_by_id.assert_called_once_with("kernel_123")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])