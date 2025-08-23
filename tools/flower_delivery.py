import requests
from typing import List, Dict, Optional
from agents import function_tool
import random
from datetime import datetime, timedelta

@function_tool
def find_flower_options(occasion: str = "apology", recipient_type: str = "friend", budget: float = 75.0, location: str = "") -> List[Dict]:
    """
    Find appropriate flower arrangements for apologies based on relationship and budget.
    """
    
    # Flower meanings and appropriateness for apologies
    apology_flowers = {
        "white_roses": {
            "meaning": "New beginnings, sincerity, humility",
            "appropriate_for": ["romantic", "friend", "family"],
            "message": "Perfect for sincere apologies, symbolizes fresh start"
        },
        "pink_roses": {
            "meaning": "Gratitude, appreciation, gentle emotions", 
            "appropriate_for": ["romantic", "friend", "family"],
            "message": "Shows appreciation for the relationship"
        },
        "white_lilies": {
            "meaning": "Rebirth, purity, commitment to change",
            "appropriate_for": ["family", "friend"],
            "message": "Symbolizes commitment to being better"
        },
        "purple_tulips": {
            "meaning": "Forgiveness, royalty, rebirth",
            "appropriate_for": ["romantic", "friend"],
            "message": "Specifically associated with seeking forgiveness"
        },
        "white_chrysanthemums": {
            "meaning": "Honesty, devoted love, sincerity",
            "appropriate_for": ["romantic", "family"],
            "message": "Represents honest emotions and devotion"
        },
        "pink_carnations": {
            "meaning": "Gratitude, admiration, first love",
            "appropriate_for": ["friend", "family", "colleague"],
            "message": "Gentle and thoughtful choice"
        }
    }
    
    arrangements = []
    
    # Create arrangements based on budget and relationship
    if budget >= 100:
        arrangements.extend([
            {
                "name": "Premium Apology Bouquet",
                "flowers": "2 dozen white roses with baby's breath",
                "price": 120,
                "size": "large",
                "message_suggestion": "For when you need to make a significant gesture",
                "delivery_options": ["same_day", "next_day", "scheduled"],
                "vase_included": True
            },
            {
                "name": "Elegant Mixed Arrangement", 
                "flowers": "White lilies, pink roses, and eucalyptus",
                "price": 95,
                "size": "large",
                "message_suggestion": "Sophisticated choice showing thoughtfulness",
                "delivery_options": ["same_day", "next_day"],
                "vase_included": True
            }
        ])
    
    if budget >= 60:
        arrangements.extend([
            {
                "name": "Sincere Apology Arrangement",
                "flowers": "1 dozen white roses with greenery",
                "price": 75,
                "size": "medium",
                "message_suggestion": "Classic choice for heartfelt apologies",
                "delivery_options": ["same_day", "next_day", "scheduled"],
                "vase_included": True
            },
            {
                "name": "Forgiveness Tulip Bouquet",
                "flowers": "Purple tulips with white accent flowers",
                "price": 65,
                "size": "medium", 
                "message_suggestion": "Specifically chosen for seeking forgiveness",
                "delivery_options": ["next_day", "scheduled"],
                "vase_included": False
            }
        ])
    
    if budget >= 30:
        arrangements.extend([
            {
                "name": "Gentle Apology Posy",
                "flowers": "Pink carnations and white chrysanthemums",
                "price": 45,
                "size": "small",
                "message_suggestion": "Sweet and sincere gesture",
                "delivery_options": ["next_day", "scheduled"],
                "vase_included": False
            },
            {
                "name": "Simple Sincerity Bouquet",
                "flowers": "6 white roses with baby's breath",
                "price": 35,
                "size": "small",
                "message_suggestion": "Simple but meaningful choice",
                "delivery_options": ["next_day"],
                "vase_included": False
            }
        ])

    # Filter by budget and add delivery info
    suitable_arrangements = [a for a in arrangements if a["price"] <= budget]
    
    for arrangement in suitable_arrangements:
        arrangement.update({
            "florist": f"{location} Flowers & More" if location else "Local Florist",
            "phone": "(555) 123-ROSE",
            "estimated_delivery": "2-4 hours for same day, next morning for next day",
            "care_instructions": "Trim stems, change water daily, keep away from direct sunlight",
            "appropriateness_for_apology": "High" if arrangement["price"] > 50 else "Good"
        })
    
    return sorted(suitable_arrangements, key=lambda x: x["price"], reverse=True)

@function_tool
def schedule_flower_delivery(arrangement_name: str, delivery_address: str, delivery_date: str, 
                           personal_message: str = "", sender_name: str = "") -> Dict:
    """
    Schedule flower delivery for apology (simulated).
    Returns delivery confirmation and tracking information.
    """
    
    # Simulate delivery scheduling
    delivery_fee = 15 if "same_day" in arrangement_name.lower() else 8
    
    confirmation = {
        "status": "scheduled",
        "order_number": f"FL{random.randint(10000, 99999)}",
        "arrangement": arrangement_name,
        "delivery_address": delivery_address,
        "delivery_date": delivery_date,
        "delivery_window": "10am-6pm" if "same_day" in delivery_date else "9am-1pm",
        "delivery_fee": delivery_fee,
        "personal_message": personal_message,
        "sender_name": sender_name,
        "tracking_available": True,
        "special_instructions": {
            "leave_if_not_home": False,
            "call_before_delivery": True,
            "signature_required": True
        }
    }
    
    # Add apology-specific recommendations
    confirmation["apology_tips"] = [
        "Include a handwritten note for more personal touch",
        "Choose morning delivery for maximum impact", 
        "Follow up with a phone call after delivery",
        "Consider their favorite colors if you know them"
    ]
    
    return confirmation

@function_tool  
def get_flower_meanings_for_apology() -> Dict[str, Dict]:
    """
    Get comprehensive guide to flowers appropriate for apologies and their meanings.
    """
    
    return {
        "best_choices": {
            "white_roses": {
                "symbolism": "New beginnings, sincerity, humility",
                "why_good_for_apology": "Shows you want a fresh start and are humble about your mistake",
                "relationship_types": "Perfect for all relationships",
                "color_psychology": "White represents purity and new beginnings"
            },
            "purple_tulips": {
                "symbolism": "Forgiveness, nobility, rebirth", 
                "why_good_for_apology": "Directly associated with seeking and granting forgiveness",
                "relationship_types": "Great for romantic relationships and close friends",
                "color_psychology": "Purple represents nobility and seeking higher understanding"
            }
        },
        "good_choices": {
            "pink_roses": {
                "symbolism": "Gratitude, appreciation, admiration",
                "why_good_for_apology": "Shows you value the relationship and person",
                "relationship_types": "All relationships, especially family and friends",
                "color_psychology": "Pink is gentle and non-threatening"
            },
            "white_lilies": {
                "symbolism": "Rebirth, purity, commitment",
                "why_good_for_apology": "Represents your commitment to change and grow",
                "relationship_types": "Family members and close friends",
                "color_psychology": "White lilies suggest spiritual renewal"
            }
        },
        "avoid": {
            "red_roses": {
                "reason": "Too romantic for most apologies, might send wrong message",
                "exception": "Only for romantic partner apologies"
            },
            "yellow_flowers": {
                "reason": "Can symbolize friendship but also jealousy or infidelity in some cultures",
                "exception": "Okay for platonic friend apologies if they love yellow"
            }
        },
        "arrangement_tips": [
            "Odd numbers of flowers are more aesthetically pleasing",
            "Include a mix of textures with greenery or baby's breath",
            "Consider the recipient's favorite colors if known",
            "A nice vase makes the gesture more lasting",
            "Simpler arrangements often feel more sincere than overly elaborate ones"
        ]
    }