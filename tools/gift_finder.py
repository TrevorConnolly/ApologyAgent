import requests
from typing import List, Dict, Optional
from agents import function_tool
import re
import html

@function_tool
def search_gifts(recipient_type: str, interests: str, budget: float = 100.0) -> List[Dict]:
    """
    Search for thoughtful gift ideas based on recipient and interests.
    Returns gift suggestions with descriptions and estimated prices.
    """
    # Simulate gift search with curated suggestions
    gift_categories = {
        "friend": {
            "books": [
                {"name": "Personalized Photo Book", "price": 25, "description": "Custom photo book with shared memories"},
                {"name": "Bestselling Novel", "price": 15, "description": "Recent award-winning fiction"},
                {"name": "Coffee Table Book", "price": 35, "description": "Beautiful book on their favorite topic"}
            ],
            "experiences": [
                {"name": "Local Workshop", "price": 60, "description": "Art, cooking, or craft class together"},
                {"name": "Concert Tickets", "price": 80, "description": "For their favorite genre or artist"},
                {"name": "Spa Day", "price": 120, "description": "Relaxing spa treatment"}
            ],
            "personal": [
                {"name": "Custom Jewelry", "price": 50, "description": "Personalized necklace or bracelet"},
                {"name": "Gourmet Food Box", "price": 40, "description": "Curated selection of treats"},
                {"name": "Subscription Box", "price": 30, "description": "Monthly box for their hobby"}
            ]
        },
        "romantic": {
            "jewelry": [
                {"name": "Promise Ring", "price": 150, "description": "Symbol of commitment"},
                {"name": "Custom Necklace", "price": 75, "description": "With their initials or special date"},
                {"name": "Watch", "price": 200, "description": "Classic timepiece they've mentioned"}
            ],
            "experiences": [
                {"name": "Weekend Getaway", "price": 300, "description": "Romantic trip to nearby destination"},
                {"name": "Couples Massage", "price": 180, "description": "Relaxing spa experience together"},
                {"name": "Fine Dining", "price": 120, "description": "Special dinner at upscale restaurant"}
            ],
            "personal": [
                {"name": "Love Letters Book", "price": 25, "description": "Handwritten letters bound in book"},
                {"name": "Star Map", "price": 40, "description": "Custom star map of meaningful date"},
                {"name": "Memory Jar", "price": 20, "description": "Jar filled with shared memories"}
            ]
        },
        "family": {
            "practical": [
                {"name": "High-quality Blanket", "price": 60, "description": "Luxurious throw for comfort"},
                {"name": "Kitchen Gadget", "price": 45, "description": "Tool for their favorite cooking activity"},
                {"name": "Home Decor", "price": 55, "description": "Something beautiful for their space"}
            ],
            "experiential": [
                {"name": "Family Photos", "price": 200, "description": "Professional family photo session"},
                {"name": "Cooking Class", "price": 80, "description": "Learn to make their favorite cuisine"},
                {"name": "Theater Tickets", "price": 100, "description": "Show they've wanted to see"}
            ],
            "sentimental": [
                {"name": "Family Tree Art", "price": 70, "description": "Custom family tree artwork"},
                {"name": "Memory Book", "price": 35, "description": "Scrapbook of family memories"},
                {"name": "Custom Portrait", "price": 90, "description": "Commissioned artwork of the family"}
            ]
        }
    }
    
    suggestions = []
    categories = gift_categories.get(recipient_type, gift_categories["friend"])
    
    for category, items in categories.items():
        for item in items:
            if item["price"] <= budget:
                suggestions.append({
                    "category": category,
                    "name": item["name"],
                    "price": item["price"],
                    "description": item["description"],
                    "relevance_score": 0.8 if interests.lower() in item["description"].lower() else 0.6
                })
    
    # Sort by relevance and price
    suggestions.sort(key=lambda x: (-x["relevance_score"], x["price"]))
    return suggestions[:8]

@function_tool  
def search_amazon(query: str, max_price: float = 100.0) -> List[Dict]:
    """
    Search Amazon for specific gift items (simulated).
    Returns product suggestions with prices and ratings.
    """
    # Simulate Amazon search results
    sample_products = [
        {
            "title": f"Premium {query.title()} Gift Set",
            "price": min(max_price * 0.7, 75),
            "rating": 4.5,
            "reviews": 234,
            "description": f"High-quality {query} perfect for gift giving",
            "prime_eligible": True
        },
        {
            "title": f"Luxury {query.title()} Collection", 
            "price": min(max_price * 0.9, 95),
            "rating": 4.3,
            "reviews": 156,
            "description": f"Premium {query} with elegant packaging",
            "prime_eligible": True
        },
        {
            "title": f"Artisan {query.title()} Kit",
            "price": min(max_price * 0.5, 45),
            "rating": 4.7,
            "reviews": 89,
            "description": f"Handcrafted {query} from local artisans",
            "prime_eligible": False
        }
    ]
    
    return [p for p in sample_products if p["price"] <= max_price]

@function_tool
def find_local_gift_shops(location: str, specialty: str = "") -> List[Dict]:
    """
    Find local gift shops and specialty stores in the specified location.
    """
    # Simulate local business search
    shops = [
        {
            "name": f"{location} Artisan Gallery",
            "address": f"123 Main St, {location}",
            "phone": "(555) 123-4567",
            "specialty": "Local art and crafts",
            "rating": 4.6,
            "hours": "Mon-Sat 10am-7pm, Sun 12pm-5pm"
        },
        {
            "name": f"The Gift Corner - {location}",
            "address": f"456 Oak Ave, {location}",
            "phone": "(555) 234-5678", 
            "specialty": "Unique gifts and jewelry",
            "rating": 4.4,
            "hours": "Daily 9am-8pm"
        },
        {
            "name": f"{location} Flowers & More",
            "address": f"789 Pine St, {location}",
            "phone": "(555) 345-6789",
            "specialty": "Flowers, plants, and gift baskets",
            "rating": 4.7,
            "hours": "Mon-Fri 8am-6pm, Sat-Sun 9am-5pm"
        }
    ]
    
    if specialty:
        shops = [s for s in shops if specialty.lower() in s["specialty"].lower()]
    
    return shops