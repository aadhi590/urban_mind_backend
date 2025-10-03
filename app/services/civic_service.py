import base64
import uuid
from datetime import datetime, timedelta
from app.models.data_models import (
    CivicReportCreate, VerificationRequest,
    VerificationStatus, CivicReportResponse
)
from app.services.vision_service import categorize_civic_issue
from app.utils.firebase_config import get_firestore
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

POINTS_REPORT = 10
POINTS_VERIFY = 5
POINTS_ESCALATED = 20

db = get_firestore()


async def create_civic_report(report: CivicReportCreate) -> CivicReportResponse:
    try:
        report_id = str(uuid.uuid4())
        image_bytes = base64.b64decode(report.image_base64)
        
        vision_result = categorize_civic_issue(image_bytes)
        location_name = await generate_location_name(report.latitude, report.longitude)
        
        civic_report = {
            "id": report_id,
            "user_id": report.user_id,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "location_name": location_name,
            "description": report.description,
            "image_base64": report.image_base64,
            "category": vision_result["category"],
            "priority": vision_result["priority"],
            "status": VerificationStatus.PENDING,
            "verification_count": 0,
            "verified_by": [],
            "created_at": datetime.now(),
            "escalated_at": None,
            "vision_confidence": vision_result["confidence"],
            "vision_labels": vision_result["labels"]
        }
        
        if db:
            db.collection("civic_reports").document(report_id).set(civic_report)
        
        await update_user_points(report.user_id, POINTS_REPORT, "report_created")
        
        return CivicReportResponse(
            success=True,
            report_id=report_id,
            category=vision_result["category"],
            priority=vision_result["priority"],
            status=VerificationStatus.PENDING,
            verification_count=0,
            message=f"Report created! {vision_result['category']} - {vision_result['priority']}",
            points_earned=POINTS_REPORT
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        return CivicReportResponse(
            success=False, report_id="", category="", priority="",
            status=VerificationStatus.PENDING, verification_count=0,
            message=f"Failed: {str(e)}", points_earned=0
        )


async def verify_civic_report(verification: VerificationRequest) -> CivicReportResponse:
    try:
        if not db:
            return CivicReportResponse(
                success=False, report_id=verification.report_id,
                category="", priority="", status="", verification_count=0,
                message="Database unavailable", points_earned=0
            )
        
        report_ref = db.collection("civic_reports").document(verification.report_id)
        report = report_ref.get()
        
        if not report.exists:
            return CivicReportResponse(
                success=False, report_id=verification.report_id,
                category="", priority="", status="", verification_count=0,
                message="Report not found", points_earned=0
            )
        
        report_data = report.to_dict()
        
        if verification.user_id in report_data["verified_by"]:
            return CivicReportResponse(
                success=False, report_id=verification.report_id,
                category=report_data["category"], priority=report_data["priority"],
                status=report_data["status"], verification_count=report_data["verification_count"],
                message="Already verified", points_earned=0
            )
        
        if verification.is_valid:
            report_data["verification_count"] += 1
            report_data["verified_by"].append(verification.user_id)
            
            if report_data["verification_count"] >= 3:
                report_data["status"] = VerificationStatus.ESCALATED
                report_data["escalated_at"] = datetime.now()
                await escalate_to_authority(report_data)
                await update_user_points(report_data["user_id"], POINTS_ESCALATED, "report_escalated")
            
            report_ref.update(report_data)
            await update_user_points(verification.user_id, POINTS_VERIFY, "verification")
            
            msg = f"Verified! {report_data['verification_count']}/3"
            if report_data["verification_count"] >= 3:
                msg += " - ESCALATED TO BBMP"
            
            return CivicReportResponse(
                success=True, report_id=verification.report_id,
                category=report_data["category"], priority=report_data["priority"],
                status=report_data["status"], verification_count=report_data["verification_count"],
                message=msg, points_earned=POINTS_VERIFY
            )
        else:
            return CivicReportResponse(
                success=True, report_id=verification.report_id,
                category=report_data["category"], priority=report_data["priority"],
                status=report_data["status"], verification_count=report_data["verification_count"],
                message="Marked invalid", points_earned=0
            )
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return CivicReportResponse(
            success=False, report_id=verification.report_id,
            category="", priority="", status="", verification_count=0,
            message=f"Failed: {str(e)}", points_earned=0
        )


async def generate_location_name(lat: float, lng: float) -> str:
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash-exp")
        prompt = f"GPS {lat},{lng} in Bengaluru. Give location name in 5 words max. Format: Near [Landmark], [Area]"
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return f"Location ({lat:.4f}, {lng:.4f})"


async def escalate_to_authority(report_data: dict):
    try:
        if db:
            db.collection("escalated_reports").document(report_data["id"]).set({
                "report_id": report_data["id"],
                "category": report_data["category"],
                "priority": report_data["priority"],
                "location": report_data["location_name"],
                "coordinates": {"lat": report_data["latitude"], "lng": report_data["longitude"]},
                "description": report_data["description"],
                "escalated_at": datetime.now(),
                "department": assign_department(report_data["category"]),
                "deadline": datetime.now() + timedelta(days=3)
            })
        print(f"✅ Escalated: {report_data['id']}")
    except Exception as e:
        print(f"❌ Escalation error: {e}")


def assign_department(category: str) -> str:
    dept_map = {
        "Road": "BBMP Road Dept",
        "Waste": "BBMP Waste Mgmt",
        "Water": "BWSSB",
        "Drainage": "BWSSB",
        "Traffic": "Traffic Police"
    }
    for key, dept in dept_map.items():
        if key in category:
            return dept
    return "BBMP General"


async def update_user_points(user_id: str, points: int, action: str):
    try:
        if not db:
            return
        user_ref = db.collection("users").document(user_id)
        user = user_ref.get()
        
        if user.exists:
            user_data = user.to_dict()
            user_data["total_points"] = user_data.get("total_points", 0) + points
            user_data["last_action"] = action
            user_ref.update(user_data)
        else:
            user_ref.set({
                "user_id": user_id,
                "total_points": points,
                "last_action": action,
                "created_at": datetime.now()
            })
        print(f"✅ +{points} points for {user_id}")
    except Exception as e:
        print(f"⚠️ Points error: {e}")