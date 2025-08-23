#!/bin/bash

# Fix dependency issues for Restaurant Kernel Agent
# This script resolves common dependency conflicts

set -e

echo "🔧 Fixing dependency issues..."

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: Not in a virtual environment. Consider using:"
    echo "   python -m venv .venv"
    echo "   source .venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

echo "🧹 Uninstalling problematic packages..."
pip uninstall -y pydantic pydantic-settings browser-use || true

echo "📥 Installing specific versions to fix conflicts..."

# Install pydantic first with specific version
pip install "pydantic>=2.5.0,<3.0.0"

# Install pydantic-settings with compatible version  
pip install "pydantic-settings>=2.1.0,<3.0.0"

# Install browser-use
pip install browser-use

# Install other core dependencies
pip install python-dotenv requests beautifulsoup4 openai

# Install async dependencies
pip install aiofiles tenacity backoff psutil

# Install Playwright and browsers
pip install playwright
echo "🌐 Installing Playwright browsers..."
playwright install chromium

echo "✅ Dependencies fixed!"
echo ""
echo "🧪 Test the fix:"
echo "   python quick_test.py"
echo "   python test_local.py"
echo ""
echo "If you still have issues, try:"
echo "   pip freeze > current_deps.txt"
echo "   pip uninstall -r current_deps.txt -y"
echo "   pip install -r requirements.txt"