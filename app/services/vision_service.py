import os
from google.cloud import vision
from app.models.data_models import CivicCategory, PriorityLevel
from dotenv import load_dotenv

load_dotenv()

# Initialize Google Vision client
try:
    # Set credentials from environment variable
    vision_key = os.getenv("GOOGLE_CLOUD_VISION_API_KEY")
    if vision_key:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = vision_key
    
    vision_client = vision.ImageAnnotatorClient()
    print("✅ Google Vision AI initialized")
except Exception as e:
    print(f"⚠️ Google Vision init failed: {e}")
    vision_client = None


def categorize_civic_issue(image_bytes: bytes) -> dict:
    """
    Analyze image using Google Vision AI and categorize civic issue
    
    Args:
        image_bytes: Image file as bytes
    
    Returns:
        dict with 'category' and 'priority'
    """
    
    if not vision_client:
        # Mock mode for testing
        return {
            "category": CivicCategory.POTHOLE,
            "priority": PriorityLevel.MEDIUM,
            "confidence": 0.75,
            "labels": ["road", "damage", "asphalt"]
        }
    
    try:
        # Prepare image for Vision API
        image = vision.Image(content=image_bytes)
        
        # Detect labels
        response = vision_client.label_detection(image=image)
        labels = [label.description.lower() for label in response.label_annotations]
        
        # Detect objects
        objects_response = vision_client.object_localization(image=image)
        objects = [obj.name.lower() for obj in objects_response.localized_object_annotations]
        
        # Detect text (for signs, notices)
        text_response = vision_client.text_detection(image=image)
        texts = text_response.text_annotations[0].description.lower() if text_response.text_annotations else ""
        
        # Combine all detected features
        all_features = labels + objects + texts.split()
        
        # Category classification logic
        category, priority = classify_issue(all_features)
        
        return {
            "category": category,
            "priority": priority,
            "confidence": response.label_annotations[0].score if response.label_annotations else 0.5,
            "labels": labels[:5]  # Top 5 labels
        }
        
    except Exception as e:
        print(f"❌ Vision API error: {e}")
        # Fallback to default
        return {
            "category": CivicCategory.OTHER,
            "priority": PriorityLevel.MEDIUM,
            "confidence": 0.3,
            "labels": []
        }


def classify_issue(features: list) -> tuple:
    """
    Classify civic issue based on detected features
    
    Returns:
        (CivicCategory, PriorityLevel)
    """
    
    # Define keyword mappings
    category_keywords = {
        CivicCategory.POTHOLE: ["pothole", "road", "damage", "hole", "asphalt", "crack", "pavement"],
        CivicCategory.GARBAGE: ["garbage", "trash", "waste", "litter", "dump", "rubbish", "bin"],
        CivicCategory.STREETLIGHT: ["light", "lamp", "pole", "streetlight", "broken", "dark"],
        CivicCategory.WATER_LEAK: ["water", "leak", "pipe", "burst", "overflow", "flooding"],
        CivicCategory.DRAINAGE: ["drain", "sewage", "clog", "overflow", "manhole", "gutter"],
        CivicCategory.TRAFFIC_SIGNAL: ["signal", "traffic", "light", "crossing", "junction"],
        CivicCategory.ENCROACHMENT: ["encroachment", "illegal", "blocking", "occupied"]
    }
    
    # Priority keywords
    high_priority_keywords = ["dangerous", "blocked", "major", "severe", "critical", "accident"]
    low_priority_keywords = ["minor", "small", "cosmetic"]
    
    # Find matching category
    category = CivicCategory.OTHER
    max_matches = 0
    
    for cat, keywords in category_keywords.items():
        matches = sum(1 for feature in features if any(kw in feature for kw in keywords))
        if matches > max_matches:
            max_matches = matches
            category = cat
    
    # Determine priority
    if any(kw in ' '.join(features) for kw in high_priority_keywords):
        priority = PriorityLevel.HIGH
    elif any(kw in ' '.join(features) for kw in low_priority_keywords):
        priority = PriorityLevel.LOW
    else:
        priority = PriorityLevel.MEDIUM
    
    # Special rules
    if category == CivicCategory.WATER_LEAK:
        priority = PriorityLevel.HIGH
    elif category == CivicCategory.POTHOLE and priority == PriorityLevel.MEDIUM:
        priority = PriorityLevel.HIGH
    
    return category, priority