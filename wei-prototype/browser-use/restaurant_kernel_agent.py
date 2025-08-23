import os
import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json

# Import Kernel if available (for deployment), graceful fallback for local testing
try:
    import kernel
    KERNEL_AVAILABLE = True
except ImportError:
    KERNEL_AVAILABLE = False
    print("Warning: Kernel not available. Running in local mode.")

from browser_use import Agent, BrowserSession, BrowserProfile, Controller, ActionResult
from browser_use.llm import ChatOpenAI
from dotenv import load_dotenv

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not available. Browser functionality will be limited.")

from utils import get_copy_code

# Load environment variables
load_dotenv()

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('restaurant_agent.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Kernel client if available
if KERNEL_AVAILABLE:
    client = kernel.Kernel()
    app = kernel.App("restaurant-reservation-agent")
else:
    client = None
    app = None

# Production configuration constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30000  # 30 seconds
MAX_TIMEOUT = 120000     # 2 minutes
BROWSER_CONNECT_RETRY_DELAY = 2  # seconds

# Controller for custom browser actions
controller = Controller()

@controller.action("Get verification code from email")
def get_verification_code(inbox_id: str) -> ActionResult:
    """
    Retrieves verification code from the latest email in the specified inbox.
    
    Args:
        inbox_id: Email inbox ID to check for verification codes
        
    Returns:
        ActionResult with verification code or error message
    """
    try:
        logger.info(f"Attempting to retrieve verification code from inbox: {inbox_id}")
        code = get_copy_code(inbox_id)
        if code:
            logger.info(f"Successfully retrieved verification code: {code}")
            return ActionResult(extracted_content=f"Found verification code: {code}")
        else:
            logger.warning("No verification code found in email yet")
            return ActionResult(
                extracted_content="No verification code found in email yet. You may need to wait a moment for the email to arrive, then try again."
            )
    except Exception as e:
        logger.error(f"Error retrieving verification code: {str(e)}")
        return ActionResult(
            extracted_content=f"Error retrieving verification code: {str(e)}. You may need to check the email manually."
        )

def validate_environment() -> Dict[str, str]:
    """
    Validate all required environment variables are present.
    
    Returns:
        Dict containing validated environment variables
        
    Raises:
        ValueError: If required environment variables are missing
    """
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for LLM',
        'AGENTMAIL_API_KEY': 'AgentMail API key for email verification'
    }
    
    env_vars = {}
    missing_vars = []
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if not value:
            missing_vars.append(f"{var_name} ({description})")
        else:
            env_vars[var_name] = value
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return env_vars

def validate_reservation_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize reservation request payload.
    
    Args:
        payload: Raw request payload
        
    Returns:
        Sanitized payload with validated parameters
        
    Raises:
        ValueError: If required parameters are missing or invalid
    """
    required_fields = ['date', 'time', 'party_size', 'location']
    sanitized = {}
    
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")
        sanitized[field] = str(payload[field]).strip()
    
    # Validate date format using production utils if available
    try:
        from production_utils import RequestValidator
        sanitized['date'] = RequestValidator.validate_date(sanitized['date'])
        sanitized['time'] = RequestValidator.validate_time(sanitized['time'])
        sanitized['location'] = RequestValidator.validate_location(sanitized['location'])
    except ImportError:
        # Fallback to basic validation if production_utils not available
        import re
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{1,2}/\d{1,2}/\d{4}$',  # M/D/YYYY
        ]
        if not any(re.match(pattern, sanitized['date']) for pattern in date_patterns):
            raise ValueError("Invalid date format. Expected formats: YYYY-MM-DD, MM/DD/YYYY, or M/D/YYYY")
    
    # Optional fields with defaults
    sanitized['inbox_id'] = payload.get('inbox_id', 'opentable_2@agentmail.to')
    sanitized['phone'] = payload.get('phone', '+18777804236')
    sanitized['first_name'] = payload.get('first_name', 'WAGENT')
    sanitized['last_name'] = payload.get('last_name', 'SRY')
    
    # Validate party size
    try:
        party_size = int(sanitized['party_size'])
        if party_size < 1 or party_size > 20:
            raise ValueError("Party size must be between 1 and 20")
        sanitized['party_size'] = party_size
    except (ValueError, TypeError):
        raise ValueError("Invalid party size - must be a number between 1 and 20")
    
    logger.info(f"Validated reservation request for {sanitized['party_size']} people on {sanitized['date']} at {sanitized['time']} in {sanitized['location']}")
    
    return sanitized

async def create_kernel_browser_session(invocation_id: str) -> tuple:
    """
    Create and connect to a Kernel browser with retry logic.
    
    Args:
        invocation_id: Runtime context invocation ID
        
    Returns:
        Tuple of (kernel_browser, playwright_browser, browser_session)
        
    Raises:
        RuntimeError: If browser creation fails after retries
    """
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Creating Kernel browser (attempt {attempt + 1}/{MAX_RETRIES})")
            
            # Create Kernel browser
            kernel_browser = await client.browsers.create(
                invocation_id=invocation_id
            )
            
            logger.info(f"Kernel browser created with session ID: {kernel_browser.session_id}")
            
            # Connect with Playwright  
            if not PLAYWRIGHT_AVAILABLE:
                raise RuntimeError("Playwright not available - cannot create browser session")
                
            async with async_playwright() as playwright:
                playwright_browser = await playwright.chromium.connect_over_cdp(
                    kernel_browser.cdp_ws_url
                )
                
                # Get or create browser context and page
                context = playwright_browser.contexts[0] if playwright_browser.contexts else await playwright_browser.new_context()
                page = context.pages[0] if context.pages else await context.new_page()
                
                # Create Browser Use session
                browser_session = BrowserSession(
                    browser_profile=None,  # Use existing Kernel browser
                    playwright_browser=playwright_browser
                )
                
                logger.info("Successfully created Kernel browser session")
                return kernel_browser, playwright_browser, browser_session
                
        except Exception as e:
            logger.error(f"Browser creation attempt {attempt + 1} failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(BROWSER_CONNECT_RETRY_DELAY * (attempt + 1))
            else:
                raise RuntimeError(f"Failed to create browser after {MAX_RETRIES} attempts: {str(e)}")

async def execute_reservation_task(browser_session: BrowserSession, llm: ChatOpenAI, reservation_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the restaurant reservation task using Browser Use agent.
    
    Args:
        browser_session: Connected Kernel browser session
        llm: Configured OpenAI LLM
        reservation_params: Validated reservation parameters
        
    Returns:
        Task execution results with reservation details
    """
    # Create detailed task instructions
    task_details = f"""
    Complete a restaurant reservation on OpenTable with the following requirements:
    
    RESERVATION DETAILS:
    - Date: {reservation_params['date']}
    - Time: {reservation_params['time']}
    - Party size: {reservation_params['party_size']} people
    - Location: {reservation_params['location']}
    - Contact email: {reservation_params['inbox_id']}
    
    STEP-BY-STEP PROCESS:
    1. Navigate to opentable.com
    2. Fill out the search form with the exact date, time, party size, and location specified above
    3. Click search to find available restaurants
    4. Select the FIRST available restaurant from the search results
    5. Proceed with making a reservation using email {reservation_params['inbox_id']}
    6. If the restaurant requires credit card information, go back and choose a different restaurant
    7. When prompted for verification code:
       - Use the "Get verification code from email" action to retrieve the code
       - Enter the verification code to complete the reservation
       - If no code is found initially, wait 10 seconds and try the action again
    8. When prompted for personal information, use:
       - Phone: {reservation_params['phone']} (note: +1 is USA country code)
       - First Name: {reservation_params['first_name']}
       - Last Name: {reservation_params['last_name']}
    9. Complete the reservation process fully
    10. Return the final confirmation details including:
        - Restaurant name and full address
        - Reservation date and time
        - Number of people
        - Confirmation number or reference
        - Any special instructions or notes
    
    IMPORTANT REQUIREMENTS:
    - Do NOT pause or stop when verification is needed - use the custom function immediately
    - If a restaurant requires payment, skip it and choose another option
    - Ensure all form fields are properly filled before submission
    - Take screenshots at key steps for debugging purposes
    - Return comprehensive confirmation details
    """
    
    logger.info("Starting reservation task execution")
    start_time = time.time()
    
    # Create Browser Use agent with Kernel browser session
    agent = Agent(
        task=task_details,
        llm=llm,
        browser_session=browser_session,
        controller=controller,
        max_steps=50,
        save_conversation_path=f"reservation_conversation_{int(start_time)}.json",
    )
    
    # Execute the agent task
    result = await agent.run()
    
    execution_time = time.time() - start_time
    logger.info(f"Task execution completed in {execution_time:.2f} seconds")
    
    # Extract and format the final result
    final_output = str(
        result.final_result() if hasattr(result, "final_result") else result
    )
    
    return {
        "success": True,
        "reservation_details": final_output,
        "execution_time_seconds": round(execution_time, 2),
        "task_steps_completed": getattr(result, 'steps_taken', 'unknown'),
        "conversation_log": f"reservation_conversation_{int(start_time)}.json"
    }

# Kernel actions - only define if Kernel is available
if KERNEL_AVAILABLE and app is not None:
    @app.action("make-reservation")
    async def make_restaurant_reservation(runtime_context, payload):
        """
        Main Kernel action to make restaurant reservations using Browser Use.
        
        Args:
            runtime_context: Kernel runtime context with invocation ID
            payload: Reservation request parameters
            
        Returns:
            Structured response with reservation details or error information
        """
        request_id = f"req_{int(time.time())}"
        logger.info(f"Starting reservation request {request_id}")
        
        try:
            # Validate environment variables
            env_vars = validate_environment()
            logger.info("Environment validation successful")
            
            # Validate and sanitize input payload
            reservation_params = validate_reservation_request(payload)
            logger.info(f"Request validation successful for {request_id}")
            
            # Initialize OpenAI LLM
            llm = ChatOpenAI(
                api_key=env_vars['OPENAI_API_KEY'],
                model="o3",
                timeout=DEFAULT_TIMEOUT
            )
            
            # Create Kernel browser session
            kernel_browser, playwright_browser, browser_session = await create_kernel_browser_session(
                runtime_context.invocation_id
            )
            
            try:
                # Execute reservation task
                task_result = await execute_reservation_task(
                    browser_session, llm, reservation_params
                )
                
                # Add browser session info to result
                task_result.update({
                    "request_id": request_id,
                    "browser_session_id": kernel_browser.session_id,
                    "browser_live_view_url": kernel_browser.browser_live_view_url,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "kernel_app": "restaurant-reservation-agent",
                    "version": "1.0.0"
                })
                
                logger.info(f"Reservation request {request_id} completed successfully")
                return task_result
                
            finally:
                # Clean up browser resources
                try:
                    await playwright_browser.close()
                    await client.browsers.delete_by_id(kernel_browser.session_id)
                    logger.info(f"Browser resources cleaned up for request {request_id}")
                except Exception as cleanup_error:
                    logger.warning(f"Browser cleanup warning for {request_id}: {cleanup_error}")
    
        except ValueError as validation_error:
            error_msg = f"Validation error for {request_id}: {str(validation_error)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": "validation_error",
                "message": str(validation_error),
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        except RuntimeError as runtime_error:
            error_msg = f"Runtime error for {request_id}: {str(runtime_error)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": "runtime_error",
                "message": str(runtime_error),
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as unexpected_error:
            error_msg = f"Unexpected error for {request_id}: {str(unexpected_error)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": "unexpected_error",
                "message": "An unexpected error occurred. Please check logs for details.",
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    @app.action("health-check")
    async def health_check(runtime_context, payload):
        """
        Health check endpoint for monitoring and readiness probes.
        
        Returns:
            System health status and configuration
        """
        try:
            # Validate environment
            env_vars = validate_environment()
            
            # Test browser creation capability
            test_browser = await client.browsers.create(
                invocation_id=runtime_context.invocation_id
            )
            await client.browsers.delete_by_id(test_browser.session_id)
            
            return {
                "status": "healthy",
                "service": "restaurant-reservation-agent",
                "version": "1.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": {
                    "environment_variables": "ok",
                    "kernel_browser_creation": "ok",
                    "openai_api": "ok" if env_vars.get('OPENAI_API_KEY') else "missing",
                    "agentmail_api": "ok" if env_vars.get('AGENTMAIL_API_KEY') else "missing"
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "restaurant-reservation-agent",
                "version": "1.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }

    # Additional utility actions for monitoring and debugging

    @app.action("list-browser-sessions")
    async def list_browser_sessions(runtime_context, payload):
        """
        List active browser sessions for debugging purposes.
        
        Returns:
            List of active browser sessions
        """
        try:
            # This would need to be implemented based on Kernel's browser management API
            return {
                "success": True,
                "message": "Browser session listing not yet implemented",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

if __name__ == "__main__":
    # Local testing capability
    print("Restaurant Kernel Agent - Production Ready")
    print("Use 'kernel deploy' to deploy this agent to the Kernel platform")
    print("Environment validation...")
    
    try:
        env_vars = validate_environment()
        print("✅ All required environment variables are present")
        print("🚀 Ready for deployment to Kernel platform")
    except ValueError as e:
        print(f"❌ Environment validation failed: {e}")
        print("Please set the required environment variables before deployment")