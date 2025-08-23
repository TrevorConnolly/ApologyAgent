from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import json
import os
import base64
import io
import tempfile
import requests
import openai

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Peace Offering Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ApologyRequest(BaseModel):
    situation: str
    recipient_name: str
    relationship_type: str  # "friend", "family", "romantic", "colleague"
    severity: int  # 1-10 scale
    recipient_preferences: Optional[Dict] = None
    budget: Optional[float] = None
    location: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None

class ApologyReviewRequest(BaseModel):
    apology_text: str

class VapiCallRequest(BaseModel):
    phone_number: str
    message: str

class VapiVoiceAnalysisRequest(BaseModel):
    phone_number: str
    apology_context: str
    coaching_focus: Optional[str] = "general"

class VapiWebAssistantRequest(BaseModel):
    apology_context: str
    coaching_focus: Optional[str] = "general"

@app.post("/create-apology")
async def create_apology(request: ApologyRequest):
    try:
        # Initialize OpenAI client for generating apology strategy
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create a prompt for generating the apology strategy
        strategy_prompt = f"""
        Create a comprehensive apology strategy for this situation:
        
        Situation: {request.situation}
        Recipient: {request.recipient_name} ({request.relationship_type})
        Severity: {request.severity}/10
        Budget: ${request.budget}
        Location: {request.location}
        Preferences: {json.dumps(request.recipient_preferences)}
        
        Please provide:
        1. A personalized apology message
        2. Strategy explanation
        3. 3-5 recommended actions with priorities and estimated costs
        4. Success probability estimate
        5. Follow-up suggestions
        
        Format the response as a detailed plan.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert relationship counselor and communication specialist who creates personalized apology strategies."},
                {"role": "user", "content": strategy_prompt}
            ]
        )
        
        apology_strategy = response.choices[0].message.content
        
        # Format response as pretty printed text
        formatted_response = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                            🕊️  APOLOGY STRATEGY PLAN  🕊️                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝

{apology_strategy}

{'-' * 80}
"""
        
        return {"formatted_response": formatted_response}
    
    except Exception as e:
        print(f"Error in create_apology: {e}")
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

@app.post("/review-apology")
async def review_apology(request: ApologyReviewRequest):
    """Review an apology text and provide feedback"""
    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create a prompt for reviewing the apology
        review_prompt = f"""
        Please analyze this apology and provide constructive feedback:
        
        "{request.apology_text}"
        
        Evaluate the apology on these dimensions:
        1. Sincerity and authenticity (1-10)
        2. Taking responsibility (1-10)
        3. Specific acknowledgment of harm (1-10)
        4. Appropriate emotion and tone (1-10)
        5. Clear commitment to change (1-10)
        
        Provide:
        - Overall score (1-10)
        - Strengths of the apology
        - Areas for improvement
        - Specific suggestions for making it more effective
        - A rewritten version that incorporates your suggestions
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in interpersonal communication and conflict resolution. Provide helpful, constructive feedback on apologies."},
                {"role": "user", "content": review_prompt}
            ]
        )
        
        review_text = response.choices[0].message.content
        
        return {
            "success": True,
            "review": review_text,
            "apology_text": request.apology_text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to review apology: {str(e)}")

@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    """Analyze audio recording of apology and provide feedback"""
    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Read and save the uploaded audio file temporarily
        audio_data = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe the audio using Whisper
            with open(temp_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            apology_text = transcript.text
            
            # Now analyze the transcribed text along with audio characteristics
            analysis_prompt = f"""
            Analyze this spoken apology for both content and delivery:
            
            Transcription: "{apology_text}"
            
            Provide feedback on:
            1. Content quality (sincerity, responsibility, specificity)
            2. Likely vocal delivery aspects based on the text structure
            3. Overall effectiveness
            4. Suggestions for improvement in both wording and delivery
            5. Rate the apology 1-10 overall
            
            Format as a structured review with scores and specific recommendations.
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in communication, specializing in analyzing both verbal content and vocal delivery of apologies."},
                    {"role": "user", "content": analysis_prompt}
                ]
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "success": True,
                "transcript": apology_text,
                "analysis": analysis,
                "filename": file.filename
            }
            
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze audio: {str(e)}")

@app.post("/vapi-voice-analysis")
async def create_vapi_voice_analysis(request: VapiVoiceAnalysisRequest):
    """Create a Vapi call for voice analysis and coaching"""
    try:
        vapi_api_key = os.getenv("VAPI_API_KEY")
        if not vapi_api_key:
            raise HTTPException(status_code=500, detail="VAPI_API_KEY not configured")
        
        # Create coaching prompt based on focus area
        focus_instructions = {
            "general": "Provide overall feedback on the apology including sincerity, responsibility, tone, and structure.",
            "sincerity": "Focus specifically on how sincere and authentic the apology sounds.",
            "responsibility": "Focus on how well the person takes responsibility without making excuses.",
            "tone": "Focus on the emotional tone, pace, and vocal delivery of the apology.",
            "structure": "Focus on the logical flow and completeness of the apology."
        }
        
        coaching_prompt = f"""You are an expert apology coach. The caller is practicing an apology for this situation: {request.apology_context}

Your coaching focus: {focus_instructions.get(request.coaching_focus, focus_instructions["general"])}

When the caller delivers their apology:
1. Listen carefully and ask them to deliver their apology
2. Provide specific, constructive feedback on their delivery
3. Rate their apology 1-10 overall
4. Give 2-3 specific suggestions for improvement
5. Ask if they'd like to try again with your feedback
6. Be encouraging but honest about areas needing work
7. Focus on vocal delivery, sincerity, emotional tone, and content

Keep your feedback conversational and supportive. Help them practice until they feel confident."""

        # Create Vapi assistant for this coaching session
        assistant_data = {
            "name": "Apology Coach",
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": coaching_prompt
                    }
                ]
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "21m00Tcm4TlvDq8ikWAM"  # Professional, warm voice
            },
            "firstMessage": f"Hi! I'm your apology coach. I understand you're working on an apology for: {request.apology_context}. When you're ready, please deliver your apology and I'll provide specific feedback to help you improve. Go ahead!"
        }
        
        # Create the assistant
        headers = {
            "Authorization": f"Bearer {vapi_api_key}",
            "Content-Type": "application/json"
        }
        
        assistant_response = requests.post(
            "https://api.vapi.ai/assistant",
            headers=headers,
            json=assistant_data
        )
        
        if assistant_response.status_code != 201:
            raise HTTPException(status_code=500, detail="Failed to create Vapi assistant")
            
        assistant = assistant_response.json()
        assistant_id = assistant.get("id")
        
        # Create the phone call
        call_data = {
            "phoneNumberId": None,  # Use default Vapi number
            "assistantId": assistant_id,
            "customer": {
                "number": request.phone_number
            }
        }
        
        call_response = requests.post(
            "https://api.vapi.ai/call",
            headers=headers,
            json=call_data
        )
        
        if call_response.status_code != 201:
            raise HTTPException(status_code=500, detail="Failed to create Vapi call")
            
        call_data = call_response.json()
        
        return {
            "success": True,
            "message": "Your AI apology coach will call you shortly! Be ready to practice your apology and receive real-time feedback.",
            "call_id": call_data.get("id"),
            "assistant_id": assistant_id,
            "phone_number": request.phone_number,
            "status": "initiated",
            "coaching_focus": request.coaching_focus
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to communicate with Vapi API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create voice analysis session: {str(e)}")

@app.post("/vapi-web-assistant")
async def create_vapi_web_assistant(request: VapiWebAssistantRequest):
    """Create a Vapi assistant for web-based voice analysis"""
    try:
        vapi_api_key = os.getenv("VAPI_API_KEY")
        if not vapi_api_key:
            raise HTTPException(status_code=500, detail="VAPI_API_KEY not configured")
        
        # Create coaching prompt based on focus area
        focus_instructions = {
            "general": "Provide overall feedback on the apology including sincerity, responsibility, tone, and structure.",
            "sincerity": "Focus specifically on how sincere and authentic the apology sounds.",
            "responsibility": "Focus on how well the person takes responsibility without making excuses.",
            "tone": "Focus on the emotional tone, pace, and vocal delivery of the apology.",
            "structure": "Focus on the logical flow and completeness of the apology."
        }
        
        coaching_prompt = f"""You are an expert apology coach conducting a web-based voice coaching session. The user is practicing an apology for this situation: {request.apology_context}

Your coaching focus: {focus_instructions.get(request.coaching_focus, focus_instructions["general"])}

Session Instructions:
1. Greet the user warmly and ask them to deliver their apology when ready
2. Listen carefully to their complete apology delivery
3. Provide specific, constructive feedback covering:
   - Overall sincerity and authenticity (1-10 rating)
   - How well they take responsibility
   - Vocal tone, pace, and emotional delivery
   - Content structure and completeness
   - Areas for improvement with specific suggestions
4. Ask if they'd like to practice again with your feedback
5. Be encouraging but provide honest, helpful guidance
6. Keep responses concise but thorough (2-3 sentences per point)
7. End each feedback session by asking if they want to try again or if they have questions

Remember: This is voice-based coaching, so focus on delivery, tone, and how the apology sounds, not just the words."""

        # Create Vapi assistant for web interaction
        assistant_data = {
            "name": "Web Apology Coach",
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system", 
                        "content": coaching_prompt
                    }
                ]
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "21m00Tcm4TlvDq8ikWAM"  # Professional, warm voice
            },
            "firstMessage": f"Hi! I'm your apology coach. I understand you're working on an apology for: {request.apology_context}. I'll focus on {request.coaching_focus} feedback. When you're ready, please deliver your apology and I'll provide specific coaching to help you improve!"
        }
        
        # Create the assistant
        headers = {
            "Authorization": f"Bearer {vapi_api_key}",
            "Content-Type": "application/json"
        }
        
        assistant_response = requests.post(
            "https://api.vapi.ai/assistant",
            headers=headers,
            json=assistant_data
        )
        
        if assistant_response.status_code != 201:
            error_msg = "Failed to create Vapi assistant"
            if assistant_response.text:
                error_msg += f": {assistant_response.text}"
            raise HTTPException(status_code=500, detail=error_msg)
            
        assistant = assistant_response.json()
        assistant_id = assistant.get("id")
        
        # Note: For web SDK, we need to return the public key and assistant ID
        # The actual public key should be configured in your Vapi dashboard
        return {
            "success": True,
            "message": "Voice coaching assistant created successfully!",
            "assistant_id": assistant_id,
            "public_key": vapi_api_key,  # In production, use a public key instead
            "coaching_focus": request.coaching_focus,
            "context": request.apology_context
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to communicate with Vapi API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create web assistant: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "Peace Offering Agent"}

@app.get("/test")
async def test_endpoint():
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return {"status": "ok", "openai_available": True, "api_key_set": bool(os.getenv("OPENAI_API_KEY"))}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)