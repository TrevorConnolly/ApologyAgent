#!/usr/bin/env python3
"""
Peace Offering Agent - Startup Script
Run this to start the sophisticated apology assistant server
"""

import uvicorn
import sys
import os

# Add current directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🕊️  Starting Peace Offering Agent - The World's Most Sophisticated Apology Assistant")
    print("━" * 80)
    print("🎯 Features:")
    print("   • AI-powered situation analysis and relationship understanding")
    print("   • Personalized apology message crafting")
    print("   • Real-world action recommendations (gifts, flowers, reservations)")
    print("   • Multi-step reconciliation strategies")
    print("   • Context-aware approach based on relationship type and severity")
    print("━" * 80)
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/health")
    print("━" * 80)
    
    try:
        uvicorn.run(
            "app:app", 
            host="0.0.0.0", 
            port=8001, 
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Peace Offering Agent stopped. Thank you for using our service!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")

if __name__ == "__main__":
    main()