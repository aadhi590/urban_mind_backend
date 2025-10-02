import os
import random
import google.generativeai as genai
from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env and configure Gemini
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print("⚠️ Gemini init failed:", e)
else:
    print("⚠️ GEMINI_API_KEY not set. Running in mock mode.")

router = APIRouter(prefix="/fusion", tags=["Fusion Service"])

# Dummy dataset
dummy_data_sources = [
    {"traffic_data": "Heavy congestion on ORR near Marathahalli",
     "civic_data": "Construction blocking 2 lanes near Ecospace"},
    {"traffic_data": "Accident reported at Silk Board junction",
     "civic_data": "Waterlogging reported near Madiwala underpass"},
    {"traffic_data": "Smooth traffic at MG Road",
     "civic_data": "Ongoing BBMP footpath repair at Brigade Road"}
]

class FusionRequest(BaseModel):
    traffic_data: str
    civic_data: str


def generate_insight(traffic, civic):
    prompt = f"""
    Fuse the following Bengaluru real-time data into an actionable traffic insight:

    Traffic Data: {traffic}
    Civic Data: {civic}

    Respond in 3 sentences max.
    """
    try:
        if api_key:
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            response = model.generate_content(prompt)

            if hasattr(response, "text") and response.text:
                return response.text.strip()
            elif hasattr(response, "candidates") and response.candidates:
                return response.candidates[0].content.parts[0].text.strip()

        # If Gemini not available or fails → return mock
        return f"[Mock] Traffic '{traffic}' with civic issue '{civic}' → Expect congestion. Use alternate routes."
    except Exception as e:
        print("❌ Gemini error:", repr(e))
        return f"[Fallback] Traffic '{traffic}' + Civic '{civic}' → Please use alternate routes."


@router.post("/process")
async def process_fusion(request: FusionRequest):
    try:
        insight = generate_insight(request.traffic_data, request.civic_data)
        return {
            "traffic_data": request.traffic_data,
            "civic_data": request.civic_data,
            "insight": insight
        }
    except Exception as e:
        return {"error": f"Fusion failed: {str(e)}"}


@router.get("/process")
async def process_dummy_fusion():
    try:
        source = random.choice(dummy_data_sources)
        traffic = source["traffic_data"]
        civic = source["civic_data"]

        insight = generate_insight(traffic, civic)
        return {
            "traffic_data": traffic,
            "civic_data": civic,
            "insight": insight
        }
    except Exception as e:
        return {"error": f"Dummy fusion failed: {str(e)}"}
