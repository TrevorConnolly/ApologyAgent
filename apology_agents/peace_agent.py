from agents import Agent, Runner, function_tool
from typing import List, Dict, Any, Optional
import json
import asyncio

from models.apology_context import ApologyContext, ApologyResponse, Action, ActionType
from tools.gift_finder import search_gifts, search_amazon
from tools.restaurant_booker import find_restaurants, make_reservation
from tools.flower_delivery import find_flower_options
from tools.message_crafter import craft_personalized_message

class PeaceOfferingAgent:
    def __init__(self):
        self.context_analyzer = Agent(
            name="ContextAnalyzer",
            instructions=(
                "You are an expert at analyzing interpersonal situations and relationships. "
                "Analyze the given situation to understand:\n"
                "1. What exactly went wrong and why the person is upset\n"
                "2. The relationship dynamics and history\n"
                "3. The recipient's likely emotional state and needs\n"
                "4. The severity and potential long-term impact\n"
                "5. What kind of apology approach would be most effective\n"
                "Return a JSON analysis with emotional_impact, key_issues, recipient_needs, and recommended_approach."
            ),
            tools=[]
        )
        
        self.strategy_planner = Agent(
            name="StrategyPlanner", 
            instructions=(
                "You are a relationship expert who creates comprehensive apology strategies. "
                "Based on the context analysis, create a multi-step plan that includes:\n"
                "1. The right tone and messaging approach\n"
                "2. Specific concrete actions to demonstrate sincerity\n"
                "3. Timeline for when to do what\n"
                "4. How to follow up and rebuild trust\n"
                "Focus on genuine, thoughtful actions that match the relationship and situation."
            ),
            tools=[search_gifts, find_restaurants, find_flower_options]
        )
        
        self.action_executor = Agent(
            name="ActionExecutor",
            instructions=(
                "You execute concrete apology actions. Use the available tools to:\n"
                "1. Find and recommend specific gifts, flowers, or experiences\n" 
                "2. Make actual reservations when requested\n"
                "3. Provide detailed execution instructions\n"
                "4. Estimate costs and logistics\n"
                "Be specific with recommendations and provide all necessary details."
            ),
            tools=[search_gifts, search_amazon, find_restaurants, make_reservation, find_flower_options]
        )

    async def create_apology_plan(self, context: ApologyContext) -> ApologyResponse:
        # Step 1: Analyze the situation and relationship context
        analysis_prompt = f"""
        Analyze this situation requiring an apology:
        
        Situation: {context.situation}
        Recipient: {context.recipient_name} ({context.relationship_type})
        Severity: {context.severity}/10
        Budget: ${context.budget or 'flexible'}
        Location: {context.location or 'not specified'}
        Known preferences: {context.recipient_preferences}
        
        Provide analysis as JSON with: emotional_impact, key_issues, recipient_needs, recommended_approach
        """
        
        analysis_result = await Runner.run(self.context_analyzer, analysis_prompt)
        
        try:
            analysis = json.loads(analysis_result.final_output)
        except:
            analysis = {
                "emotional_impact": "moderate to high",
                "key_issues": ["trust", "communication"],
                "recipient_needs": ["acknowledgment", "sincere apology"],
                "recommended_approach": "direct and heartfelt"
            }

        # Step 2: Create strategy and find specific actions
        strategy_prompt = f"""
        Create a comprehensive apology strategy for this situation:
        
        Context: {context.situation}
        Relationship: {context.relationship_type} with {context.recipient_name}
        Analysis: {analysis}
        Budget: ${context.budget or 'flexible'}
        Location: {context.location or 'anywhere'}
        
        Use tools to find specific recommendations for:
        1. Meaningful gifts appropriate for this relationship and situation
        2. Experience options (restaurants, activities)  
        3. Flower arrangements if appropriate
        
        Create a ranked list of 3-5 concrete actions with estimated costs.
        """
        
        strategy_result = await Runner.run(self.strategy_planner, strategy_prompt)
        
        # Step 3: Craft personalized apology message
        message_prompt = f"""
        Write a sincere, personalized apology message for:
        
        Situation: {context.situation}
        Recipient: {context.recipient_name} ({context.relationship_type})
        Tone: {analysis.get('recommended_approach', 'heartfelt and direct')}
        
        The message should:
        - Acknowledge what went wrong specifically
        - Take full responsibility without excuses
        - Show understanding of impact on them
        - Express genuine remorse
        - Indicate concrete steps to make it right
        - Be appropriate for the relationship type
        
        Keep it sincere and avoid being overly dramatic.
        """
        
        message_result = await Runner.run(
            Agent(name="MessageCrafter", instructions="Write sincere, appropriate apology messages.", tools=[]),
            message_prompt
        )

        # Step 4: Execute specific action recommendations
        action_prompt = f"""
        Based on this strategy: {strategy_result.final_output}
        
        Use tools to find and provide specific recommendations with:
        - Product links and prices for gifts
        - Restaurant names, contact info for reservations  
        - Flower arrangement options with delivery details
        - Any other concrete actions mentioned
        
        Provide execution details for each recommended action.
        """
        
        action_result = await Runner.run(self.action_executor, action_prompt)

        # Parse and structure the response
        actions = self._parse_actions(strategy_result.final_output, action_result.final_output, context)
        
        return ApologyResponse(
            apology_message=message_result.final_output.strip(),
            strategy_explanation=self._extract_strategy_explanation(strategy_result.final_output),
            recommended_actions=actions,
            estimated_total_cost=sum(a.estimated_cost or 0 for a in actions),
            success_probability=self._estimate_success_probability(context, analysis),
            follow_up_suggestions=self._generate_followup_suggestions(context, analysis)
        )

    def _parse_actions(self, strategy_output: str, action_output: str, context: ApologyContext) -> List[Action]:
        # Parse the strategy and action outputs to create structured Action objects
        actions = []
        
        # This is a simplified parser - in production you'd want more robust parsing
        if "gift" in strategy_output.lower() or "present" in strategy_output.lower():
            actions.append(Action(
                type=ActionType.GIFT,
                description="Thoughtful gift based on recipient's interests",
                estimated_cost=min(context.budget * 0.3 if context.budget else 50, 100),
                priority=2,
                execution_details={"source": "personalized selection", "delivery": "in person preferred"}
            ))
        
        if "restaurant" in strategy_output.lower() or "dinner" in strategy_output.lower():
            actions.append(Action(
                type=ActionType.RESTAURANT,
                description="Dinner at a meaningful restaurant",
                estimated_cost=min(context.budget * 0.4 if context.budget else 80, 200),
                priority=1,
                execution_details={"setting": "intimate", "timing": "when they're ready to talk"}
            ))
            
        if "flowers" in strategy_output.lower() or "bouquet" in strategy_output.lower():
            actions.append(Action(
                type=ActionType.FLOWERS,
                description="Flower arrangement with personal note",
                estimated_cost=40,
                priority=3,
                execution_details={"delivery": "to their home or office", "include_note": True}
            ))

        # Always include the apology message as an action
        actions.insert(0, Action(
            type=ActionType.MESSAGE,
            description="Sincere personal apology conversation",
            estimated_cost=0,
            priority=1,
            execution_details={"format": "in person preferred", "timing": "as soon as appropriate"}
        ))
        
        return actions[:5]  # Limit to top 5 actions

    def _extract_strategy_explanation(self, strategy_output: str) -> str:
        lines = strategy_output.split('\n')
        explanation_lines = []
        for line in lines:
            if any(word in line.lower() for word in ['because', 'since', 'approach', 'strategy', 'effective']):
                explanation_lines.append(line.strip())
        
        return ' '.join(explanation_lines) if explanation_lines else "Multi-faceted approach combining sincere communication with meaningful actions."

    def _estimate_success_probability(self, context: ApologyContext, analysis: Dict) -> float:
        base_probability = 0.7
        
        # Adjust based on severity
        severity_penalty = (context.severity - 5) * 0.05
        base_probability -= severity_penalty
        
        # Adjust based on relationship type
        relationship_bonuses = {
            "romantic": 0.1,  # High stakes but high reward
            "family": 0.15,   # Family tends to forgive
            "friend": 0.1,
            "colleague": -0.1  # Professional relationships are trickier
        }
        
        base_probability += relationship_bonuses.get(context.relationship_type, 0)
        
        return max(0.2, min(0.95, base_probability))

    def _generate_followup_suggestions(self, context: ApologyContext, analysis: Dict) -> List[str]:
        suggestions = [
            "Give them space to process if they need it",
            "Follow up in a few days to check how they're feeling",
            "Be consistent with any promises made in the apology"
        ]
        
        if context.severity >= 7:
            suggestions.append("Consider couples/family counseling if appropriate")
            
        if context.relationship_type in ["romantic", "family"]:
            suggestions.append("Plan regular check-ins to rebuild trust over time")
            
        return suggestions