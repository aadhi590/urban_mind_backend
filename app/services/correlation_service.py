# app/services/correlation_service.py
import os
import random
import google.generativeai as genai
from typing import Optional, Tuple
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app.data.dummy_correlation import dummy_correlation_data

# Load env variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Use correct Gemini model name
MODEL_NAME = "models/gemini-2.5-flash"

# Configure Gemini
if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        print(f"✅ Gemini configured with model {MODEL_NAME}")
    except Exception as e:
        print("⚠️ Gemini configuration failed:", e)
else:
    print("⚠️ GEMINI_API_KEY not set — running in mock mode.")

router = APIRouter(prefix="/correlation", tags=["Correlation Service"])

# Request schema
class CorrelationRequest(BaseModel):
    zone: Optional[str] = None
    environmental_data: Optional[str] = None
    sentiment_data: Optional[str] = None


# --- Core Gemini Call ---
def call_gemini(prompt: str) -> tuple[str, str]:
    """
    Calls Gemini safely.
    Returns (text, source) where source = 'gemini' or 'mock'
    """
    if not API_KEY:
        return ("[mock] No Gemini API key configured", "mock")

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)

        # Handle response shapes
        if hasattr(response, "text") and response.text:
            return (response.text.strip(), "gemini")

        if hasattr(response, "candidates") and response.candidates:
            try:
                text = response.candidates[0].content.parts[0].text
            except Exception:
                text = str(response.candidates[0])
            return (text.strip(), "gemini")

        return ("[mock] Gemini returned no usable text", "mock")

    except Exception as e:
        print("❌ Gemini call failed:", repr(e))
        return (f"[mock] Gemini error: {e}", "mock")


# --- POST: Analyze correlation ---
@router.post("/analyze")
async def analyze(request: CorrelationRequest):
    try:
        # Input priority: explicit data > zone lookup > random
        if request.environmental_data and request.sentiment_data:
            env = request.environmental_data
            sent = request.sentiment_data
            zone = request.zone or "custom"
        elif request.zone:
            rec = next((r for r in dummy_correlation_data if r["zone"].lower() == request.zone.lower()), None)
            if not rec:
                raise HTTPException(status_code=404, detail=f"Zone '{request.zone}' not found in dummy data")
            env, sent, zone = rec["environmental_data"], rec["sentiment_data"], rec["zone"]
        else:
            rec = random.choice(dummy_correlation_data)
            env, sent, zone = rec["environmental_data"], rec["sentiment_data"], rec["zone"]

        # Gemini prompt
        prompt = f"""
        You are CityMind AI. Analyze correlation between environment and citizen emotions.

        Zone: {zone}
        Environmental Data: {env}
        Sentiment Data: {sent}

        Return JSON with:
        - correlation
        - prediction (with probability %)
        - recommendation
        """

        text, source = call_gemini(prompt)

        return {
            "zone": zone,
            "environmental_data": env,
            "sentiment_data": sent,
            "insight_text": text,
            "source": source,
            "model": MODEL_NAME if source == "gemini" else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("Correlation analyze error:", repr(e))
        raise HTTPException(status_code=500, detail="Correlation analysis failed")


# --- GET: Analyze all dummy data ---
@router.get("/dummy")
async def analyze_all_dummy():
    results = []
    for rec in dummy_correlation_data:
        prompt = f"""
        Zone: {rec['zone']}
        Environmental Data: {rec['environmental_data']}
        Sentiment Data: {rec['sentiment_data']}

        Provide:
        1) correlation
        2) prediction (probability %)
        3) recommendation
        """
        text, source = call_gemini(prompt)
        results.append({
            "zone": rec["zone"],
            "environmental_data": rec["environmental_data"],
            "sentiment_data": rec["sentiment_data"],
            "insight_text": text,
            "source": source,
            "model": MODEL_NAME if source == "gemini" else None,
        })
    return {"results": results}
