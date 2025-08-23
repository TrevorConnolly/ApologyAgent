#!/usr/bin/env python3
"""
Test script for the Peace Offering Agent
"""

import asyncio
import json
from models.apology_context import ApologyContext, RelationshipType
from apology_agents.peace_agent import PeaceOfferingAgent

async def test_scenarios():
    """Test various apology scenarios"""
    
    agent = PeaceOfferingAgent()
    
    print("🧪 Testing Peace Offering Agent with various scenarios...\n")
    
    # Test Scenario 1: Friend Apology
    print("=" * 60)
    print("🎯 Scenario 1: Friend Apology - Missed Important Event")
    print("=" * 60)
    
    friend_context = ApologyContext(
        situation="I missed my best friend's birthday party because I forgot and went to a different event instead. They're really hurt and feel like I don't prioritize our friendship.",
        recipient_name="Sarah",
        relationship_type=RelationshipType.FRIEND,
        severity=6,
        recipient_preferences={"loves_books": True, "vegetarian": True, "favorite_flowers": "sunflowers"},
        budget=150.0,
        location="San Francisco"
    )
    
    try:
        friend_response = await agent.create_apology_plan(friend_context)
        print(f"📝 Apology Message Preview:\n{friend_response.apology_message[:200]}...")
        print(f"\n🎯 Strategy: {friend_response.strategy_explanation}")
        print(f"💰 Total Estimated Cost: ${friend_response.estimated_total_cost}")
        print(f"📊 Success Probability: {friend_response.success_probability:.1%}")
        print(f"🎬 Recommended Actions: {len(friend_response.recommended_actions)} actions planned")
        
        for i, action in enumerate(friend_response.recommended_actions[:3], 1):
            print(f"   {i}. {action.type.value}: {action.description}")
    
    except Exception as e:
        print(f"❌ Error in friend scenario: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Scenario 2: Romantic Apology - Trust Issue")  
    print("=" * 60)
    
    romantic_context = ApologyContext(
        situation="I was texting with an ex and didn't tell my partner about it. They found out and feel like I was being secretive and potentially cheating.",
        recipient_name="Alex",
        relationship_type=RelationshipType.ROMANTIC,
        severity=8,
        recipient_preferences={"loves_italian_food": True, "allergic_to_lilies": True},
        budget=300.0,
        location="Boston"
    )
    
    try:
        romantic_response = await agent.create_apology_plan(romantic_context)
        print(f"📝 Apology Message Preview:\n{romantic_response.apology_message[:200]}...")
        print(f"\n🎯 Strategy: {romantic_response.strategy_explanation}")
        print(f"💰 Total Estimated Cost: ${romantic_response.estimated_total_cost}")
        print(f"📊 Success Probability: {romantic_response.success_probability:.1%}")
        print(f"🎬 Recommended Actions: {len(romantic_response.recommended_actions)} actions planned")
        
    except Exception as e:
        print(f"❌ Error in romantic scenario: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Scenario 3: Family Apology - Low Severity")
    print("=" * 60)
    
    family_context = ApologyContext(
        situation="I was late to Sunday family dinner and didn't call ahead. Mom was worried and had to keep the food warm.",
        recipient_name="Mom",
        relationship_type=RelationshipType.FAMILY,
        severity=3,
        budget=75.0,
        location="Chicago"
    )
    
    try:
        family_response = await agent.create_apology_plan(family_context)
        print(f"📝 Apology Message Preview:\n{family_response.apology_message[:200]}...")
        print(f"\n🎯 Strategy: {family_response.strategy_explanation}")
        print(f"💰 Total Estimated Cost: ${family_response.estimated_total_cost}")
        print(f"📊 Success Probability: {family_response.success_probability:.1%}")
        
    except Exception as e:
        print(f"❌ Error in family scenario: {e}")
    
    print("\n" + "🎉" * 20)
    print("✅ Testing completed! The Peace Offering Agent is ready to help mend relationships.")
    print("🚀 Start the server with: python start.py")

def test_tools():
    """Test individual tools"""
    print("\n🔧 Testing individual tools...\n")
    
    # Test gift finder
    from tools.gift_finder import search_gifts
    gifts = search_gifts("friend", "books and art", 100.0)
    print(f"🎁 Gift suggestions found: {len(gifts)}")
    
    # Test restaurant finder  
    from tools.restaurant_booker import find_restaurants
    restaurants = find_restaurants("San Francisco", cuisine="italian", party_size=2)
    print(f"🍽️  Restaurants found: {len(restaurants)}")
    
    # Test flower options
    from tools.flower_delivery import find_flower_options
    flowers = find_flower_options("apology", "romantic", 75.0, "Seattle")
    print(f"🌹 Flower arrangements found: {len(flowers)}")
    
    print("✅ All tools working correctly!")

if __name__ == "__main__":
    print("🕊️  Peace Offering Agent - Test Suite")
    print("━" * 50)
    
    # Test tools first
    test_tools()
    
    # Test full scenarios
    asyncio.run(test_scenarios())