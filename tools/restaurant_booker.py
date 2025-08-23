import requests
from typing import List, Dict, Optional
from agents import function_tool
import random
from datetime import datetime, timedelta

@function_tool
def find_restaurants(location: str, cuisine: str = "", price_range: str = "moderate", party_size: int = 2) -> List[Dict]:
    """
    Find restaurants suitable for apology dinner/lunch.
    Focus on intimate, quiet places good for conversation.
    """
    # Simulate restaurant search with focus on apology-appropriate venues
    base_restaurants = [
        {
            "name": f"The Quiet Corner Bistro",
            "cuisine": "Contemporary American",
            "price_range": "moderate",
            "rating": 4.6,
            "atmosphere": "intimate and quiet",
            "features": ["private booths", "dim lighting", "quiet music"],
            "phone": "(555) 123-7890",
            "address": f"123 Quiet St, {location}",
            "good_for": "serious conversations"
        },
        {
            "name": f"Serenity Italian Kitchen",
            "cuisine": "Italian",
            "price_range": "upscale",
            "rating": 4.8,
            "atmosphere": "romantic and private",
            "features": ["candlelit tables", "soft music", "wine selection"],
            "phone": "(555) 234-8901", 
            "address": f"456 Romance Ave, {location}",
            "good_for": "making amends"
        },
        {
            "name": f"The Garden Room",
            "cuisine": "Farm-to-table",
            "price_range": "moderate",
            "rating": 4.5,
            "atmosphere": "peaceful and natural",
            "features": ["outdoor seating", "garden views", "organic menu"],
            "phone": "(555) 345-9012",
            "address": f"789 Garden Way, {location}",
            "good_for": "calm discussions"
        },
        {
            "name": f"Harbor View Café",
            "cuisine": "Seafood",
            "price_range": "moderate",
            "rating": 4.4,
            "atmosphere": "scenic and relaxed",
            "features": ["waterfront views", "outdoor deck", "fresh seafood"],
            "phone": "(555) 456-0123",
            "address": f"321 Harbor Dr, {location}",
            "good_for": "thoughtful conversations"
        },
        {
            "name": f"Memories French Cuisine",
            "cuisine": "French",
            "price_range": "upscale",
            "rating": 4.7,
            "atmosphere": "elegant and sophisticated",
            "features": ["private dining rooms", "extensive wine list", "classic ambiance"],
            "phone": "(555) 567-1234",
            "address": f"654 Elegance Blvd, {location}",
            "good_for": "special occasions and apologies"
        }
    ]
    
    # Filter by cuisine and price range
    filtered = []
    for restaurant in base_restaurants:
        cuisine_match = not cuisine or cuisine.lower() in restaurant["cuisine"].lower()
        price_match = not price_range or price_range.lower() in restaurant["price_range"].lower()
        
        if cuisine_match and price_match:
            # Add estimated wait times and availability
            restaurant["estimated_wait"] = random.choice(["15-30 minutes", "30-45 minutes", "45-60 minutes"])
            restaurant["availability"] = "Good" if random.random() > 0.3 else "Limited"
            filtered.append(restaurant)
    
    return sorted(filtered, key=lambda x: x["rating"], reverse=True)

@function_tool
def make_reservation(restaurant_name: str, date: str, time: str, party_size: int, special_requests: str = "") -> Dict:
    """
    Attempt to make a restaurant reservation (simulated).
    Returns reservation details or availability information.
    """
    # Simulate reservation system
    success_rate = 0.8  # 80% success rate
    
    if random.random() < success_rate:
        confirmation_number = f"AP{random.randint(1000, 9999)}"
        return {
            "status": "confirmed",
            "confirmation_number": confirmation_number,
            "restaurant": restaurant_name,
            "date": date,
            "time": time,
            "party_size": party_size,
            "special_requests": special_requests,
            "instructions": "Please arrive 10 minutes early. Call if you need to modify or cancel.",
            "cancellation_policy": "24-hour notice required for cancellations"
        }
    else:
        # Suggest alternative times
        alt_times = ["6:00 PM", "6:30 PM", "7:30 PM", "8:00 PM"]
        return {
            "status": "unavailable", 
            "restaurant": restaurant_name,
            "requested_date": date,
            "requested_time": time,
            "alternative_times": random.sample(alt_times, 2),
            "message": "Requested time not available, but we have openings at alternative times",
            "phone": "(555) 123-4567",
            "instructions": "Call directly to check for cancellations or book alternative times"
        }

@function_tool  
def get_restaurant_recommendations_for_apology(relationship_type: str, severity: int, location: str) -> List[Dict]:
    """
    Get specific restaurant recommendations tailored for apology situations.
    """
    if severity >= 8:  # Very serious situation
        recommendations = [
            {
                "type": "private_dining",
                "name": f"The Private Room at {location} Hotel",
                "reason": "Complete privacy for serious conversations",
                "atmosphere": "Exclusive and confidential",
                "estimated_cost": "$200-300 per person"
            }
        ]
    elif relationship_type == "romantic":
        recommendations = [
            {
                "type": "romantic_intimate",
                "name": f"{location} Candlelight Bistro", 
                "reason": "Romantic setting to reconnect emotionally",
                "atmosphere": "Intimate with soft lighting",
                "estimated_cost": "$100-150 per person"
            }
        ]
    elif relationship_type == "family":
        recommendations = [
            {
                "type": "comfort_casual",
                "name": f"Family Table Restaurant",
                "reason": "Comfortable, familiar environment for family discussions",
                "atmosphere": "Warm and welcoming",
                "estimated_cost": "$50-75 per person"
            }
        ]
    else:  # friends, colleagues
        recommendations = [
            {
                "type": "quiet_conversation",
                "name": f"{location} Quiet Corner Café",
                "reason": "Good for sincere conversation without distractions", 
                "atmosphere": "Calm and conducive to talking",
                "estimated_cost": "$75-100 per person"
            }
        ]
    
    # Add general tips
    for rec in recommendations:
        rec["booking_tips"] = [
            "Request a quiet table away from high-traffic areas",
            "Mention it's for an important personal conversation",
            "Avoid peak dining hours for more privacy",
            "Consider lunch if evening feels too formal"
        ]
    
    return recommendations