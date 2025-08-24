#!/usr/bin/env python3
"""Test script to debug import issues"""

import sys
import os

# Set environment to suppress warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def test_step(name, func):
    try:
        print(f"Testing {name}...", end=" ")
        func()
        print("✅")
        return True
    except Exception as e:
        print(f"❌ {e}")
        return False

def test_agents_import():
    from agents import Agent, Runner
    
def test_models_import():
    from models.apology_context import ApologyContext, RelationshipType

def test_peace_agent_import():
    from apology_agents.peace_agent import PeaceOfferingAgent

def test_peace_agent_creation():
    from apology_agents.peace_agent import PeaceOfferingAgent
    agent = PeaceOfferingAgent()

if __name__ == "__main__":
    print("🔍 Debugging import issues...")
    
    all_good = True
    all_good &= test_step("agents import", test_agents_import)
    all_good &= test_step("models import", test_models_import)
    all_good &= test_step("peace_agent import", test_peace_agent_import)
    all_good &= test_step("peace_agent creation", test_peace_agent_creation)
    
    if all_good:
        print("\n🎉 All tests passed! PeaceOfferingAgent should work.")
    else:
        print("\n❌ Some tests failed. Need to debug further.")