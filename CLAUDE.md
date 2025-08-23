# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Development Commands

**Start the application:**
```bash
python start.py
```
Server runs on http://localhost:8000 with auto-reload enabled.

**Alternative dependency management:**
- Poetry: `poetry install && poetry run python start.py`  
- uv: `uv venv && uv pip install -r requirements.txt && uv run python start.py`

**Convex backend (optional logging):**
```bash
# In project root (requires Node 18+)
npm install
npx convex dev
```

## Architecture Overview

This is an AI-powered apology assistance system built with FastAPI that helps users create personalized apology strategies and reconciliation plans.

### Core Components

**Multi-Agent System (`apology_agents/peace_agent.py`):**
- `ContextAnalyzer`: Analyzes interpersonal situations and relationship dynamics
- `StrategyPlanner`: Creates comprehensive multi-step apology strategies
- `ActionExecutor`: Executes concrete recommendations using external tools

**Models (`models/`):**
- `ApologyContext`: Input structure (situation, recipient, relationship type, severity, preferences, budget, location)
- `ApologyResponse`: Complete response with message, strategy, actions, cost estimate, success probability

**Tools (`tools/`):**
- `gift_finder.py`: Gift recommendations and Amazon search
- `restaurant_booker.py`: Restaurant finding and reservation system  
- `flower_delivery.py`: Flower arrangement options
- `message_crafter.py`: Personalized message generation

### Key Endpoints

- `POST /create-apology`: Main apology generation endpoint
- `GET /`: Dashboard HTML interface
- `GET /health`: Health check

### Data Flow

1. User submits apology request via dashboard or API
2. `PeaceOfferingAgent.create_apology_plan()` orchestrates:
   - Situation analysis for emotional impact and relationship dynamics
   - Strategy planning with tool-assisted recommendations
   - Personalized message crafting
   - Action execution with specific details and costs
3. Structured response includes formatted text output for dashboard display
4. Optional logging to Convex backend (requires environment configuration)

### Database Integration

Optional Convex integration for request/response logging:
- Schema: `convex/schema.ts` defines logs table
- Mutation: `convex/logs.ts` handles log insertion  
- Environment: `CONVEX_URL`, `CONVEX_ADMIN_KEY` or `CONVEX_TOKEN`
- Logging failures are silently ignored to not impact main flow

### Development Notes

- Uses `agents` library for AI agent orchestration
- FastAPI with CORS middleware for web dashboard
- Async/await pattern throughout for performance
- Error handling designed to gracefully degrade
- Budget-aware recommendations with cost estimation
- Relationship-type specific success probability calculations