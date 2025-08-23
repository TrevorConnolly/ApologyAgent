from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import json
import os

from apology_agents.peace_agent import PeaceOfferingAgent
from models.apology_context import ApologyContext, ApologyResponse

app = FastAPI(title="Peace Offering Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

peace_agent = PeaceOfferingAgent()

class ApologyRequest(BaseModel):
    situation: str
    recipient_name: str
    relationship_type: str  # "friend", "family", "romantic", "colleague"
    severity: int  # 1-10 scale
    recipient_preferences: Optional[Dict] = None
    budget: Optional[float] = None
    location: Optional[str] = None

@app.post("/create-apology")
async def create_apology(request: ApologyRequest):
    try:
        context = ApologyContext(
            situation=request.situation,
            recipient_name=request.recipient_name,
            relationship_type=request.relationship_type,
            severity=request.severity,
            recipient_preferences=request.recipient_preferences or {},
            budget=request.budget,
            location=request.location
        )
        
        response = await peace_agent.create_apology_plan(context)
        
        # Format response as pretty printed text
        formatted_response = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                            🕊️  APOLOGY STRATEGY PLAN  🕊️                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📝 PERSONALIZED APOLOGY MESSAGE:
{'-' * 80}
{response.apology_message}

📋 STRATEGY EXPLANATION:
{'-' * 80}
{response.strategy_explanation}

🎯 RECOMMENDED ACTIONS:
{'-' * 80}
"""
        
        for i, action in enumerate(response.recommended_actions, 1):
            priority_stars = "⭐" * action.priority
            cost_text = f"${action.estimated_cost:.2f}" if action.estimated_cost else "Free"
            formatted_response += f"""
{i}. {action.description.upper()}
   Type: {action.type.value}
   Priority: {priority_stars} ({action.priority}/5)
   Estimated Cost: {cost_text}
   Details: {json.dumps(action.execution_details, indent=2)}
"""

        formatted_response += f"""
💰 ESTIMATED TOTAL COST: ${response.estimated_total_cost:.2f}
📊 SUCCESS PROBABILITY: {response.success_probability:.1%}

🔮 FOLLOW-UP SUGGESTIONS:
{'-' * 80}
"""
        
        for i, suggestion in enumerate(response.follow_up_suggestions, 1):
            formatted_response += f"{i}. {suggestion}\n"
        
        formatted_response += "\n" + "═" * 80
        
        return {"formatted_response": formatted_response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def dashboard():
    """Serve the dashboard HTML"""
    try:
        with open("dashboard.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard not found. Please ensure dashboard.html exists.</h1>", status_code=404)

@app.get("/dashboard")
async def dashboard_alt():
    """Alternative dashboard endpoint"""
    return await dashboard()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "Peace Offering Agent"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)