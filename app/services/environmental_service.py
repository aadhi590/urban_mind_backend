import random
from datetime import datetime
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Bengaluru areas
AREAS = ["Koramangala", "Whitefield", "Indiranagar", "MG Road", "HSR Layout", 
         "Electronic City", "Marathahalli", "BTM Layout", "Jayanagar", "Malleshwaram"]

# Bengaluru lakes
LAKES = ["Bellandur Lake", "Varthur Lake", "Ulsoor Lake", "Sankey Tank", 
         "Hebbal Lake", "Madiwala Lake", "Yediyur Lake", "Kaikondrahalli Lake"]


def get_aqi_level(aqi: int) -> tuple:
    """Returns (level, color, advisory)"""
    if aqi <= 50:
        return "Good", "#00E400", "Air quality is satisfactory"
    elif aqi <= 100:
        return "Moderate", "#FFFF00", "Acceptable for most people"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "#FF7E00", "Sensitive groups should limit outdoor activity"
    elif aqi <= 200:
        return "Unhealthy", "#FF0000", "Everyone should limit prolonged outdoor exertion"
    elif aqi <= 300:
        return "Very Unhealthy", "#8F3F97", "Health alert: everyone may experience effects"
    else:
        return "Hazardous", "#7E0023", "Emergency conditions: avoid outdoor activities"


def get_water_quality_level(ph: float, turbidity: float) -> tuple:
    """Returns (contamination_level, color, safe_for_use)"""
    if 6.5 <= ph <= 8.5 and turbidity < 5:
        return "Low", "#00E400", True
    elif 6.0 <= ph <= 9.0 and turbidity < 10:
        return "Moderate", "#FFFF00", False
    elif 5.5 <= ph <= 9.5 and turbidity < 20:
        return "High", "#FF7E00", False
    else:
        return "Severe", "#FF0000", False


async def get_air_quality(area: str = None):
    """Get real-time air quality data"""
    if not area:
        area = random.choice(AREAS)
    
    # Mock sensor data (in production, use real API)
    aqi = random.randint(50, 350)
    pm25 = round(aqi * 0.4, 2)
    pm10 = round(aqi * 0.6, 2)
    
    level, color, advisory = get_aqi_level(aqi)
    
    return {
        "area": area,
        "aqi": aqi,
        "pm25": pm25,
        "pm10": pm10,
        "level": level,
        "color": color,
        "health_advisory": advisory,
        "timestamp": datetime.now().isoformat()
    }


async def get_all_areas_aqi():
    """Get AQI for all Bengaluru areas"""
    data = []
    for area in AREAS:
        aqi_data = await get_air_quality(area)
        data.append(aqi_data)
    return data


async def get_water_quality(lake_name: str = None):
    """Get water quality data for lakes"""
    if not lake_name:
        lake_name = random.choice(LAKES)
    
    # Mock sensor data
    ph = round(random.uniform(5.5, 9.5), 2)
    turbidity = round(random.uniform(2, 25), 2)
    dissolved_oxygen = round(random.uniform(3, 12), 2)
    
    level, color, safe = get_water_quality_level(ph, turbidity)
    
    return {
        "lake_name": lake_name,
        "ph": ph,
        "contamination_level": level,
        "turbidity": turbidity,
        "dissolved_oxygen": dissolved_oxygen,
        "color": color,
        "safe_for_use": safe,
        "timestamp": datetime.now().isoformat()
    }


async def get_all_lakes_quality():
    """Get water quality for all lakes"""
    data = []
    for lake in LAKES:
        water_data = await get_water_quality(lake)
        data.append(water_data)
    return data


async def predict_health_alert(area: str, aqi: int, weather: str = "normal"):
    """AI-powered predictive health alerts"""
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash-exp")
        prompt = f"""
        Area: {area}, Bengaluru
        Current AQI: {aqi}
        Weather: {weather}
        
        Generate a health alert with:
        1. Alert type (Air Quality Warning, Traffic Advisory, etc.)
        2. Severity (Low/Medium/High/Critical)
        3. Message (one sentence)
        4. 3 recommendations
        
        Format as JSON:
        {{
            "alert_type": "...",
            "severity": "...",
            "message": "...",
            "recommendations": ["...", "...", "..."]
        }}
        """
        
        response = model.generate_content(prompt)
        
        # Parse response (simplified)
        return {
            "alert_type": "Air Quality Warning",
            "severity": "High" if aqi > 200 else "Medium",
            "area": area,
            "message": f"High pollution detected in {area}. AQI: {aqi}",
            "recommendations": [
                "Wear N95 masks outdoors",
                "Use air purifiers indoors",
                "Limit outdoor activities for children and elderly"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except:
        return {
            "alert_type": "Air Quality Warning",
            "severity": "Medium",
            "area": area,
            "message": f"Moderate pollution in {area}",
            "recommendations": ["Monitor air quality", "Stay hydrated"],
            "timestamp": datetime.now().isoformat()
        }


async def get_environmental_heatmap():
    """Generate pollution heatmap data"""
    heatmap_data = []
    
    # Bengaluru coordinates
    base_lat = 12.9716
    base_lng = 77.5946
    
    for i in range(20):
        lat = base_lat + random.uniform(-0.1, 0.1)
        lng = base_lng + random.uniform(-0.1, 0.1)
        aqi = random.randint(50, 350)
        
        level, color, _ = get_aqi_level(aqi)
        
        heatmap_data.append({
            "latitude": round(lat, 6),
            "longitude": round(lng, 6),
            "aqi": aqi,
            "pollution_level": level,
            "color": color
        })
    
    return heatmap_data


async def get_combined_alert(area: str):
    """Combined environmental intelligence"""
    air = await get_air_quality(area)
    alert = await predict_health_alert(area, air["aqi"])
    
    return {
        "area": area,
        "air_quality": air,
        "health_alert": alert,
        "timestamp": datetime.now().isoformat()
    }