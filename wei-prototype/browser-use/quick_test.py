#!/usr/bin/env python3
"""
Quick validation script for Restaurant Kernel Agent
Tests basic functionality without external dependencies
"""

import os
import sys
from datetime import datetime

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

def test_file_structure():
    """Test if all required files exist."""
    print_status("Checking file structure...")
    
    required_files = [
        "restaurant_kernel_agent.py",
        "production_utils.py", 
        "monitoring.py",
        "utils.py",
        "requirements.txt",
        "pyproject.toml",
        ".env.example",
        "README.md",
        "deploy.sh"
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file}")
            missing.append(file)
    
    if missing:
        print_status(f"Missing files: {', '.join(missing)}", "ERROR")
        return False
    else:
        print_status("All required files present", "SUCCESS")
        return True

def test_python_imports():
    """Test basic Python imports."""
    print_status("Testing basic imports...")
    
    # Test if we can import our modules
    try:
        sys.path.insert(0, '.')
        
        # Test production_utils
        from production_utils import RequestValidator, ValidationError
        print("  ✓ production_utils imported successfully")
        
        # Test basic validation
        validator = RequestValidator()
        test_date = validator.validate_date("2025-08-31")
        assert test_date == "2025-08-31"
        print("  ✓ RequestValidator working")
        
        return True
        
    except Exception as e:
        print_status(f"Import test failed: {e}", "ERROR")
        return False

def test_environment_template():
    """Test .env.example file structure."""
    print_status("Checking environment template...")
    
    try:
        with open('.env.example', 'r') as f:
            content = f.read()
        
        required_vars = [
            'OPENAI_API_KEY',
            'AGENTMAIL_API_KEY',
            'BROWSER_USE_HEADLESS',
            'LOG_LEVEL'
        ]
        
        missing = []
        for var in required_vars:
            if var not in content:
                missing.append(var)
            else:
                print(f"  ✓ {var} found in template")
        
        if missing:
            print_status(f"Missing env vars in template: {', '.join(missing)}", "WARNING")
            return False
        else:
            print_status("Environment template looks good", "SUCCESS")
            return True
            
    except FileNotFoundError:
        print_status(".env.example not found", "ERROR")
        return False

def test_deployment_script():
    """Test deployment script exists and is executable."""
    print_status("Checking deployment script...")
    
    if not os.path.exists('deploy.sh'):
        print_status("deploy.sh not found", "ERROR")
        return False
    
    # Check if executable (Unix-like systems)
    if os.name != 'nt':  # Not Windows
        if not os.access('deploy.sh', os.X_OK):
            print_status("deploy.sh not executable - run: chmod +x deploy.sh", "WARNING")
        else:
            print("  ✓ deploy.sh is executable")
    
    print_status("Deployment script ready", "SUCCESS")
    return True

def show_next_steps():
    """Show user what to do next."""
    print("\n" + "=" * 60)
    print("🚀 Ready for deployment! Next steps:")
    print("=" * 60)
    
    print("\n1. 📝 Set up environment variables:")
    print("   cp .env.example .env")
    print("   # Edit .env with your API keys")
    
    print("\n2. 🔧 Install dependencies (choose one):")
    print("   pip install -r requirements.txt")
    print("   # OR")  
    print("   uv sync")
    print("   # OR")
    print("   poetry install")
    
    print("\n3. 🧪 Test locally (optional):")
    print("   python test_local.py")
    
    print("\n4. 🚀 Deploy to Kernel:")
    print("   kernel login")
    print("   ./deploy.sh")
    
    print("\n5. ✅ Test deployment:")
    print("   kernel invoke restaurant-reservation-agent health-check")
    
    print("\n📚 For more details, see README.md")

def main():
    """Run quick validation tests."""
    print("🔍 Restaurant Kernel Agent - Quick Validation")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Python Imports", test_python_imports),
        ("Environment Template", test_environment_template),
        ("Deployment Script", test_deployment_script),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Validation Summary:")
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
        print_status("🎉 All validation checks passed!", "SUCCESS")
        show_next_steps()
        return 0
    else:
        print_status("❌ Some validation checks failed.", "ERROR")
        print("Please fix the issues above before proceeding with deployment.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)