from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class CivicCategory(str, Enum):
    POTHOLE = "Road Maintenance - Pothole"
    GARBAGE = "Waste Management - Garbage"
    STREETLIGHT = "Infrastructure - Street Light"
    WATER_LEAK = "Water Supply - Leak"
    DRAINAGE = "Drainage - Blockage"
    TRAFFIC_SIGNAL = "Traffic - Signal Issue"
    ENCROACHMENT = "Encroachment - Illegal"
    OTHER = "Other"

class PriorityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class VerificationStatus(str, Enum):
    PENDING = "Pending"
    VERIFIED = "Verified"
    REJECTED = "Rejected"
    ESCALATED = "Escalated"

class CivicReportCreate(BaseModel):
    """Request model for creating a civic report"""
    user_id: str
    latitude: float
    longitude: float
    description: Optional[str] = ""
    image_base64: str  # Base64 encoded image from Flutter

class CivicReport(BaseModel):
    """Complete civic report model"""
    id: str
    user_id: str
    latitude: float
    longitude: float
    location_name: str
    description: str
    image_url: str
    category: CivicCategory
    priority: PriorityLevel
    status: VerificationStatus
    verification_count: int = 0
    verified_by: List[str] = []
    created_at: datetime
    escalated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class VerificationRequest(BaseModel):
    """Request model for citizen verification"""
    report_id: str
    user_id: str
    is_valid: bool  # True = confirm, False = reject

class CivicReportResponse(BaseModel):
    """Response after creating/verifying report"""
    success: bool
    report_id: str
    category: str
    priority: str
    status: str
    verification_count: int
    message: str
    points_earned: Optional[int] = 0