from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum

class RelationshipType(str, Enum):
    FRIEND = "friend"
    FAMILY = "family"
    ROMANTIC = "romantic"
    COLLEAGUE = "colleague"
    ACQUAINTANCE = "acquaintance"

class ActionType(str, Enum):
    MESSAGE = "message"
    GIFT = "gift"
    FLOWERS = "flowers"
    RESTAURANT = "restaurant"
    EXPERIENCE = "experience"
    DONATION = "donation"
    SERVICE = "service"

class ApologyContext(BaseModel):
    situation: str = Field(..., description="Description of what happened")
    recipient_name: str = Field(..., description="Name of person to apologize to")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    severity: int = Field(..., ge=1, le=10, description="Severity of situation (1-10)")
    recipient_preferences: Dict[str, Any] = Field(default_factory=dict, description="Known preferences about recipient")
    budget: Optional[float] = Field(None, description="Available budget for actions")
    location: Optional[str] = Field(None, description="Location for local services/delivery")
    
class Action(BaseModel):
    type: ActionType
    description: str
    estimated_cost: Optional[float] = None
    execution_details: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(..., ge=1, le=5, description="Priority level (1=highest)")

class ApologyResponse(BaseModel):
    apology_message: str = Field(..., description="Personalized apology message")
    strategy_explanation: str = Field(..., description="Why this approach was chosen")
    recommended_actions: List[Action] = Field(..., description="Concrete actions to take")
    estimated_total_cost: Optional[float] = None
    success_probability: float = Field(..., ge=0, le=1, description="Estimated success rate")
    follow_up_suggestions: List[str] = Field(default_factory=list)
    
class RelationshipProfile(BaseModel):
    name: str
    relationship_type: RelationshipType
    known_preferences: Dict[str, Any] = Field(default_factory=dict)
    past_apologies: List[Dict] = Field(default_factory=list)
    communication_style: Optional[str] = None
    important_dates: Dict[str, str] = Field(default_factory=dict)