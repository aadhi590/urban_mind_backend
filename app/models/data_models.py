from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


# -----------------------------
# Air Quality Models
# -----------------------------
class AQILevel(str, Enum):
    GOOD = "Good"
    MODERATE = "Moderate"
    UNHEALTHY_SENSITIVE = "Unhealthy for Sensitive Groups"
    UNHEALTHY = "Unhealthy"
    VERY_UNHEALTHY = "Very Unhealthy"
    HAZARDOUS = "Hazardous"


class AirQualityData(BaseModel):
    area: str
    aqi: int
    pm25: float
    pm10: float
    level: str
    color: str
    health_advisory: str
    timestamp: datetime


class WaterQualityData(BaseModel):
    lake_name: str
    ph: float
    contamination_level: str
    turbidity: float
    dissolved_oxygen: float
    color: str
    safe_for_use: bool
    timestamp: datetime


class HealthAlert(BaseModel):
    alert_type: str
    severity: str
    area: str
    message: str
    recommendations: List[str]
    timestamp: datetime


class EnvironmentalHeatmap(BaseModel):
    latitude: float
    longitude: float
    aqi: int
    pollution_level: str
    color: str


# -----------------------------
# Civic Report Models
# -----------------------------
class PriorityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class CivicCategory(str, Enum):
    WASTE_MANAGEMENT = "Waste Management"
    ROAD_DAMAGE = "Road Damage"
    WATER_LOGGING = "Water Logging"
    AIR_POLLUTION = "Air Pollution"
    NOISE_POLLUTION = "Noise Pollution"
    PUBLIC_SAFETY = "Public Safety"
    OTHER = "Other"


class CivicReportCreate(BaseModel):
    title: str
    description: str
    location: str
    reported_by: str
    category: CivicCategory
    priority: PriorityLevel = PriorityLevel.MEDIUM
    timestamp: datetime = datetime.utcnow()


class CivicReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    resolved: Optional[bool] = None
    priority: Optional[PriorityLevel] = None


class CivicReport(CivicReportCreate):
    id: int
    resolved: bool = False


class CivicReportResponse(BaseModel):
    id: int
    title: str
    description: str
    location: str
    reported_by: str
    category: CivicCategory
    priority: PriorityLevel
    resolved: bool
    timestamp: datetime


# -----------------------------
# Verification Models
# -----------------------------
class VerificationStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class VerificationRequest(BaseModel):
    user_id: str
    document_type: str   # e.g., "Aadhar", "Voter ID", "Driving License"
    document_number: str
    submitted_at: datetime = datetime.utcnow()
    status: VerificationStatus = VerificationStatus.PENDING
