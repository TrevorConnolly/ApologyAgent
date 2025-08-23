# Installation Guide - Restaurant Kernel Agent

## Quick Fix for Dependency Issues

If you're getting `pydantic` import errors, run this fix script:

```bash
# Fix dependency conflicts
./fix_deps.sh

# Test the fix
python quick_test.py
```

## Manual Installation Steps

### 1. Set up Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

### 2. Fix Pydantic Conflicts

```bash
# Upgrade pip first
pip install --upgrade pip

# Install specific compatible versions
pip install "pydantic>=2.5.0,<3.0.0"
pip install "pydantic-settings>=2.1.0,<3.0.0"
```

### 3. Install Core Dependencies

```bash
# Install browser automation
pip install browser-use
pip install playwright

# Install Playwright browsers
playwright install chromium

# Install other dependencies
pip install python-dotenv requests beautifulsoup4 openai
pip install aiofiles tenacity backoff psutil
```

### 4. Test Installation

```bash
# Quick validation
python quick_test.py

# Full testing (opens browser briefly)
python test_local.py
```

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'pydantic._internal._signature'`

**Solution:**
```bash
pip uninstall pydantic pydantic-settings browser-use
pip install "pydantic>=2.5.0,<3.0.0" "pydantic-settings>=2.1.0,<3.0.0"
pip install browser-use
```

### Issue: `playwright` not found

**Solution:**
```bash
pip install playwright
playwright install chromium
```

### Issue: Import errors in test scripts

**Solution:**
The test scripts are designed to handle missing dependencies gracefully. They'll skip tests for unavailable modules and show warnings instead of crashing.

### Issue: Virtual environment not activated

**Solution:**
```bash
# Make sure you see (.venv) in your prompt
source .venv/bin/activate

# If you don't have a venv, create one:
python -m venv .venv
source .venv/bin/activate
```

## Alternative Installation Methods

### Using uv (Fastest)

```bash
# Install uv if not available
pip install uv

# Install dependencies
uv sync

# Activate the environment uv creates
source .venv/bin/activate
```

### Using Poetry

```bash
# Install poetry if not available
pip install poetry

# Install dependencies
poetry install

# Activate shell
poetry shell
```

### Using requirements.txt (Fallback)

```bash
pip install -r requirements.txt
playwright install chromium
```

## Verification

After installation, verify everything works:

```bash
# Should show all green checkmarks
python quick_test.py

# Should open browser briefly to OpenTable
python test_local.py
```

## Next Steps

Once installation is working:

1. Set up environment: `cp .env.example .env`
2. Add your API keys to `.env`
3. Deploy: `./deploy.sh`

## Getting Help

If you're still having issues:

1. Check your Python version: `python --version` (needs 3.8+)
2. Check your virtual environment: `which python`
3. Share the full error message for specific help
4. Try the nuclear option: delete `.venv` and start fresh