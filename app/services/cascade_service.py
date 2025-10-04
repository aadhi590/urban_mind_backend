# app/services/cascade_service.py
import os
import random
import time
from typing import Optional, Tuple, List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Optional imports (ML & Gemini). We handle missing libs gracefully.
try:
    from sklearn.linear_model import LogisticRegression
    import numpy as np
    SKLEARN_OK = True
except Exception:
    SKLEARN_OK = False

try:
    import google.generativeai as genai
    GENAI_OK = True
except Exception:
    GENAI_OK = False

from app.data.dummy_cascade import dummy_cascade_data

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "models/gemini-2.5-flash"

if GENAI_OK and API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        print("Gemini configured for cascade service")
    except Exception as e:
        print("Gemini config failed:", e)
        GENAI_OK = False
else:
    if not GENAI_OK:
        print("google.generativeai not installed, will run without Gemini")
    else:
        print("GEMINI_API_KEY not set — running without Gemini")

router = APIRouter(prefix="/cascade", tags=["Cascade Service"])

# Request models
class CascadeRequest(BaseModel):
    trigger: Optional[str] = None
    features: Optional[Dict] = None
    method: Optional[str] = "auto"  # "rule", "ml", "gemini", or "auto"

# Utility: simple rule-based scorer
def rule_based_predict(trigger: str, features: Optional[dict]) -> Tuple[List[Dict], float]:
    """
    Deterministic rules mapping features -> cascade timeline.
    Returns (predicted_cascade, probability_score)
    """
    results = []
    base_prob = 0.5

    if "rain_mm" in (features or {}):
        rain = features.get("rain_mm", 0)
        blockage = features.get("drain_blockage", 0)
        # rules
        if rain >= 30 and blockage >= 0.6:
            results = [
                {"time": "t+15m", "impact": "Underpass waterlogging", "prob": 0.9},
                {"time": "t+30m", "impact": "ORR slowdown", "prob": 0.75},
                {"time": "t+45m", "impact": "Bus service delays", "prob": 0.6},
            ]
            base_prob = 0.8
        else:
            results = [{"time": "t+20m", "impact": "Localized puddles", "prob": 0.4}]
            base_prob = 0.35
    elif "accident_severity" in (features or {}):
        sev = features.get("accident_severity", 0)
        lane = features.get("lane_blocked", 0)
        peak = features.get("time_of_day_peak", 0)
        prob = min(0.95, 0.4 + sev * 0.5 + lane * 0.1 + peak * 0.2)
        results = [
            {"time": "t+10m", "impact": "Immediate lane blockage", "prob": min(1.0, prob)},
            {"time": "t+25m", "impact": "Feeder roads clogged", "prob": min(1.0, prob - 0.1)},
        ]
        base_prob = prob
    else:
        # fallback generic effect
        results = [{"time": "t+30m", "impact": "Possible ripple effects", "prob": 0.3}]
        base_prob = 0.3

    return results, round(base_prob, 2)

# Utility: lightweight ML predictor (train on dummy data at runtime)
ML_MODEL = None
def train_ml_model():
    global ML_MODEL
    if not SKLEARN_OK:
        return None
    # Create a tiny training set from dummy_cascade_data (features -> overall probability)
    X = []
    y = []
    for rec in dummy_cascade_data:
        f = rec.get("features", {})
        # simple vectorization: numeric values or aggregated sum
        vec = []
        for k, v in sorted(f.items()):
            try:
                vec.append(float(v))
            except Exception:
                vec.append(0.0)
        X.append(vec)
        # label: average of historical cascade probabilities (normalized)
        probs = [e["prob"] for e in rec.get("historical_cascade", [])]
        y.append(min(1.0, sum(probs) / max(1, len(probs))))
    # pad vectors to same length
    max_len = max(len(x) for x in X) if X else 0
    Xp = [xi + [0.0] * (max_len - len(xi)) for xi in X]
    try:
        clf = LogisticRegression()
        clf.fit(np.array(Xp), np.array(y))
        ML_MODEL = (clf, max_len)
        print("✅ ML model trained (cascade_service)")
        return ML_MODEL
    except Exception as e:
        print("ML training failed:", e)
        return None

def ml_predict(features: dict) -> Tuple[List[Dict], float]:
    """
    Use trained ML_MODEL to predict a single probability and then map to impacts.
    """
    if not SKLEARN_OK or ML_MODEL is None:
        # fallback to rule-based if ML not available
        return rule_based_predict("ml_fallback", features)
    clf, max_len = ML_MODEL
    vec = []
    for k, v in sorted((features or {}).items()):
        try:
            vec.append(float(v))
        except Exception:
            vec.append(0.0)
    vec = vec + [0.0] * (max_len - len(vec))
    try:
        prob = float(clf.predict_proba([vec])[0].max())  # predicted class probability (approx)
        # map probability to simple timeline
        timeline = []
        if prob >= 0.7:
            timeline = [
                {"time": "t+10m", "impact": "Immediate cascade start", "prob": round(prob, 2)},
                {"time": "t+30m", "impact": "Secondary congestion", "prob": round(max(0.5, prob - 0.15), 2)},
            ]
        else:
            timeline = [{"time": "t+30m", "impact": "Low-probability ripple", "prob": round(prob, 2)}]
        return timeline, round(prob, 2)
    except Exception as e:
        print("ml_predict error:", e)
        return rule_based_predict("ml_error_fallback", features)

# Gemini refinement (narrative & recommendations)
def gemini_refine(trigger: str, timeline: List[Dict], prob: float) -> Tuple[str, str]:
    """
    Ask Gemini to produce a compact narrative + authoritative recommendation.
    Returns (narrative_text, 'gemini' or 'mock')
    """
    if not GENAI_OK or not API_KEY:
        # create a readable JSON-like narrative
        narrative = {
            "summary": f"Trigger: {trigger}. Predicted cascade probability: {prob}",
            "timeline": timeline,
            "recommendation": "Local emergency mitigation (pumps, diversions) and public advisory."
        }
        return str(narrative), "mock"
    try:
        prompt = f"""
        You are CityMind AI Cascade Predictor. Input trigger: {trigger}.
        Current timeline predictions: {timeline}
        Overall cascade probability: {prob}

        Provide a concise JSON with keys:
         - summary (one sentence)
         - critical_actions (list of 2 short actionable items for city authorities)
         - urgency_level (low/medium/high)
        """
        model = genai.GenerativeModel(MODEL_NAME)
        resp = model.generate_content(prompt)
        # Best-effort parse
        text = getattr(resp, "text", None)
        if not text and getattr(resp, "candidates", None):
            try:
                text = resp.candidates[0].content.parts[0].text
            except Exception:
                text = str(resp)
        return (text.strip() if text else "[gemini empty]", "gemini")
    except Exception as e:
        print("Gemini refine failed:", e)
        return (f"[mock] Gemini error: {e}", "mock")

# Endpoint: predict cascade
@router.post("/predict")
async def predict(request: CascadeRequest):
    try:
        # choose method
        method = (request.method or "auto").lower()
        # if features provided directly, use them; else try to match trigger in dummy dataset
        features = request.features
        trigger = request.trigger

        if not features and trigger:
            rec = next((r for r in dummy_cascade_data if r["trigger"].lower() == trigger.lower()), None)
            if rec:
                features = rec.get("features", {})
            else:
                # if not found, use random sample
                rec = random.choice(dummy_cascade_data)
                features = rec.get("features", {})
                trigger = trigger or rec.get("trigger")
        if not trigger:
            rec = random.choice(dummy_cascade_data)
            trigger = rec.get("trigger")
            if not features:
                features = rec.get("features", {})

        # auto: prefer ml if available, else rule, then gemini refine
        if method == "auto":
            if SKLEARN_OK:
                if ML_MODEL is None:
                    train_ml_model()
                timeline, prob = ml_predict(features)
            else:
                timeline, prob = rule_based_predict(trigger, features)
        elif method == "ml":
            if ML_MODEL is None:
                train_ml_model()
            timeline, prob = ml_predict(features)
        elif method == "rule":
            timeline, prob = rule_based_predict(trigger, features)
        elif method == "gemini":
            # use rule to propose timeline then refine
            timeline, prob = rule_based_predict(trigger, features)
        else:
            raise HTTPException(status_code=400, detail="Unknown method")

        # Gemini refine / narrative
        narrative, source = gemini_refine(trigger, timeline, prob)

        response = {
            "trigger_event": trigger,
            "predicted_cascade": timeline,
            "probability": prob,
            "narrative": narrative,
            "source": source,
            "method_used": method
        }
        return response

    except HTTPException:
        raise
    except Exception as e:
        print("cascade predict error:", e)
        raise HTTPException(status_code=500, detail="Cascade prediction failed")

# Endpoint: list dummy scenarios
@router.get("/dummy")
async def get_dummy():
    return {"scenarios": dummy_cascade_data}
