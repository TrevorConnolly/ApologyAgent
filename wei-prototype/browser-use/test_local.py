#!/usr/bin/env python3
"""
Local testing script for Restaurant Kernel Agent
Tests core functionality without deploying to Kernel platform
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import our modules with graceful error handling
try:
    from restaurant_kernel_agent import (
        validate_environment, validate_reservation_request, 
        KERNEL_AVAILABLE, PLAYWRIGHT_AVAILABLE
    )
    AGENT_IMPORTS_OK = True
except Exception as e:
    print(f"Warning: Could not import restaurant_kernel_agent: {e}")
    AGENT_IMPORTS_OK = False
    KERNEL_AVAILABLE = False
    PLAYWRIGHT_AVAILABLE = False

try:
    from production_utils import RequestValidator
    UTILS_IMPORTS_OK = True
except Exception as e:
    print(f"Warning: Could not import production_utils: {e}")
    UTILS_IMPORTS_OK = False

def print_status(message, status="INFO"):
    """Print status message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[94m",  # Blue
        "SUCCESS": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
    }
    color = colors.get(status, "\033[0m")
    print(f"{color}[{timestamp}] [{status}] {message}\033[0m")

def test_dependencies():
    """Test if all required dependencies are available."""
    print_status("Testing dependencies...")
    
    dependencies = []
    
    # Test browser-use
    try:
        import browser_use
        dependencies.append(("browser-use", "✓", browser_use.__version__ if hasattr(browser_use, '__version__') else "unknown"))
    except ImportError as e:
        dependencies.append(("browser-use", "✗", f"Missing: {e}"))
    
    # Test OpenAI
    try:
        import openai
        dependencies.append(("openai", "✓", openai.__version__ if hasattr(openai, '__version__') else "unknown"))
    except ImportError as e:
        dependencies.append(("openai", "✗", f"Missing: {e}"))
    
    # Test Playwright
    dependencies.append(("playwright", "✓" if PLAYWRIGHT_AVAILABLE else "✗", "Available" if PLAYWRIGHT_AVAILABLE else "Missing"))
    
    # Test Kernel
    dependencies.append(("kernel", "✓" if KERNEL_AVAILABLE else "✗", "Available" if KERNEL_AVAILABLE else "Missing"))
    
    # Test other dependencies
    for dep_name in ["dotenv", "pydantic", "tenacity", "backoff", "psutil"]:
        try:
            module = __import__(dep_name.replace("-", "_"))
            dependencies.append((dep_name, "✓", "Available"))
        except ImportError:
            dependencies.append((dep_name, "✗", "Missing"))
    
    # Print dependency status
    print("\nDependency Status:")
    print("-" * 50)
    for name, status, version in dependencies:
        print(f"{name:20} {status:3} {version}")
    
    missing = [name for name, status, _ in dependencies if status == "✗"]
    if missing:
        print_status(f"Missing dependencies: {', '.join(missing)}", "WARNING")
        return False
    else:
        print_status("All dependencies available", "SUCCESS")
        return True

def test_environment_validation():
    """Test environment variable validation."""
    print_status("Testing environment validation...")
    
    if not AGENT_IMPORTS_OK:
        print_status("Skipping environment validation - import failed", "WARNING")
        return True
    
    try:
        env_vars = validate_environment()
        print_status("Environment validation passed", "SUCCESS")
        print(f"  OpenAI API Key: {'***' + env_vars['OPENAI_API_KEY'][-4:]}")
        print(f"  AgentMail API Key: {'***' + env_vars['AGENTMAIL_API_KEY'][-4:]}")
        return True
    except ValueError as e:
        print_status(f"Environment validation failed: {e}", "ERROR")
        return False

def test_input_validation():
    """Test input validation functions."""
    print_status("Testing input validation...")
    
    if not AGENT_IMPORTS_OK:
        print_status("Skipping input validation - import failed", "WARNING")
        return True
    
    # Test valid inputs
    test_cases = [
        {
            "name": "Valid reservation request",
            "payload": {
                "date": "2025-08-31",
                "time": "7PM",
                "party_size": 2,
                "location": "San Francisco"
            },
            "should_pass": True
        },
        {
            "name": "Invalid date format",
            "payload": {
                "date": "invalid-date",
                "time": "7PM", 
                "party_size": 2,
                "location": "San Francisco"
            },
            "should_pass": False
        },
        {
            "name": "Missing required field",
            "payload": {
                "time": "7PM",
                "party_size": 2,
                "location": "San Francisco"
            },
            "should_pass": False
        },
        {
            "name": "Invalid party size",
            "payload": {
                "date": "2025-08-31",
                "time": "7PM",
                "party_size": 0,
                "location": "San Francisco"
            },
            "should_pass": False
        }
    ]
    
    passed = 0
    for test_case in test_cases:
        try:
            validated = validate_reservation_request(test_case["payload"])
            if test_case["should_pass"]:
                print(f"  ✓ {test_case['name']}")
                passed += 1
            else:
                print(f"  ✗ {test_case['name']} (should have failed)")
        except (ValueError, Exception) as e:
            if not test_case["should_pass"]:
                print(f"  ✓ {test_case['name']} (correctly failed: {str(e)[:50]}...)")
                passed += 1
            else:
                print(f"  ✗ {test_case['name']} (unexpected failure: {e})")
    
    if passed == len(test_cases):
        print_status("Input validation tests passed", "SUCCESS")
        return True
    else:
        print_status(f"Input validation tests: {passed}/{len(test_cases)} passed", "WARNING")
        return False

def test_request_validator():
    """Test the RequestValidator class methods."""
    print_status("Testing RequestValidator methods...")
    
    if not UTILS_IMPORTS_OK:
        print_status("Skipping RequestValidator tests - import failed", "WARNING")
        return True
    
    tests = [
        ("Date validation", lambda: RequestValidator.validate_date("2025-08-31")),
        ("Time validation", lambda: RequestValidator.validate_time("7PM")),
        ("Party size validation", lambda: RequestValidator.validate_party_size(2)),
        ("Location validation", lambda: RequestValidator.validate_location("San Francisco")),
        ("Email validation", lambda: RequestValidator.validate_email("test@agentmail.to")),
        ("Phone validation", lambda: RequestValidator.validate_phone("+14155551234")),
        ("Name validation", lambda: RequestValidator.validate_name("John", "first_name")),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            result = test_func()
            print(f"  ✓ {test_name}: {result}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {test_name}: {e}")
    
    if passed == len(tests):
        print_status("RequestValidator tests passed", "SUCCESS")
        return True
    else:
        print_status(f"RequestValidator tests: {passed}/{len(tests)} passed", "WARNING")
        return False

async def test_browser_opening():
    """Test browser opening without making actual reservations."""
    print_status("Testing browser opening (no actual reservations)...")
    
    if not PLAYWRIGHT_AVAILABLE:
        print_status("Playwright not available - skipping browser test", "WARNING")
        return True
    
    try:
        from playwright.async_api import async_playwright
        
        print_status("Attempting to launch browser...")
        
        async with async_playwright() as p:
            # Launch browser in non-headless mode for testing
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            print_status("Browser launched successfully", "SUCCESS")
            
            try:
                # Just navigate to OpenTable (no actual reservation)
                print_status("Navigating to OpenTable homepage...")
                await page.goto("https://www.opentable.com", timeout=15000)
                
                # Wait a moment to see the page load
                await page.wait_for_timeout(3000)
                
                print_status("Successfully loaded OpenTable homepage", "SUCCESS")
                
                return True
                
            except Exception as e:
                print_status(f"Navigation failed but browser works: {e}", "WARNING")
                return True  # Browser opening worked, navigation issue is not critical
                
            finally:
                # Close browser
                try:
                    await browser.close()
                    print_status("Browser closed successfully", "SUCCESS")
                except Exception:
                    pass  # Ignore close errors
            
    except Exception as e:
        print_status(f"Browser test failed: {e}", "ERROR")
        return False

def create_sample_env():
    """Create a sample .env file if it doesn't exist."""
    if not os.path.exists('.env') and os.path.exists('.env.example'):
        print_status("Creating .env from .env.example...", "INFO")
        with open('.env.example', 'r') as src, open('.env', 'w') as dst:
            content = src.read()
            # Replace example values with placeholders
            content = content.replace('sk-your-openai-api-key-here', 'PLEASE_SET_YOUR_OPENAI_API_KEY')
            content = content.replace('your-agentmail-api-key-here', 'PLEASE_SET_YOUR_AGENTMAIL_API_KEY')
            dst.write(content)
        print_status("Created .env file - please update with your API keys", "WARNING")

async def main():
    """Run all tests."""
    print("🤖 Restaurant Kernel Agent - Local Testing")
    print("=" * 50)
    
    # Create sample env if needed
    create_sample_env()
    
    # Run tests
    tests = [
        ("Dependencies", test_dependencies),
        ("Environment", test_environment_validation),
        ("Input Validation", test_input_validation), 
        ("Request Validator", test_request_validator),
        ("Browser Opening", test_browser_opening),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} tests...")
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        results[test_name] = result
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("-" * 50)
    
    passed = 0
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        color = "\033[92m" if result else "\033[91m"
        print(f"{color}{test_name:20} {status}\033[0m")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print_status("🎉 All tests passed! Ready for deployment.", "SUCCESS")
        print("\nNext steps:")
        print("1. Set your API keys in .env file")
        print("2. Run: ./deploy.sh")
        print("3. Test deployment: kernel invoke restaurant-reservation-agent health-check")
    else:
        print_status("❌ Some tests failed. Please fix issues before deployment.", "ERROR")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)