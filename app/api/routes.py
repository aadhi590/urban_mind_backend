from fastapi import APIRouter, HTTPException
from app.services.civic_service import (
    create_civic_report, 
    verify_civic_report,
)
from app.models.data_models import (
    CivicReportCreate, 
    VerificationRequest
)
from app.utils.firebase_config import get_firestore

router = APIRouter()

# =========================================================
# OBJECTIVE 2: CIVIC INTELLIGENCE
# =========================================================

@router.post("/civic/report")
async def create_report(report: CivicReportCreate):
    """
    📸 Create a new civic report.
    """
    try:
        response = await create_civic_report(report)
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report creation failed: {str(e)}")


@router.post("/civic/verify")
async def verify_report(verification: VerificationRequest):
    """
    ✅ Community verification for a civic report.
    """
    try:
        response = await verify_civic_report(verification)
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.get("/civic/reports")
async def get_all_reports(status: str = None, category: str = None, limit: int = 50):
    """
    📋 Get all civic reports with optional filters.
    """
    try:
        db = get_firestore()
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
            
        query = db.collection("civic_reports")
        
        if status:
            query = query.where("status", "==", status)
        if category:
            query = query.where("category", "==", category)
        
        docs = query.limit(limit).stream()
        
        reports_list = []
        for doc in docs:
            report_data = doc.to_dict()
            report_data["id"] = doc.id
            if "created_at" in report_data:
                report_data["created_at"] = str(report_data["created_at"])
            if "escalated_at" in report_data and report_data.get("escalated_at"):
                report_data["escalated_at"] = str(report_data["escalated_at"])
            reports_list.append(report_data)
            
        return {
            "success": True,
            "count": len(reports_list),
            "reports": reports_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {str(e)}")


@router.get("/civic/report/{report_id}")
async def get_report_details(report_id: str):
    """
    🔍 Get specific report details by its ID.
    """
    try:
        db = get_firestore()
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
            
        report_ref = db.collection("civic_reports").document(report_id)
        report = report_ref.get()

        if not report.exists:
            raise HTTPException(status_code=404, detail="Report not found")

        report_data = report.to_dict()
        report_data["id"] = report.id
        if "created_at" in report_data:
            report_data["created_at"] = str(report_data["created_at"])
        if "escalated_at" in report_data and report_data.get("escalated_at"):
            report_data["escalated_at"] = str(report_data["escalated_at"])
        
        return {
            "success": True,
            "report": report_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch report details: {str(e)}")


@router.get("/civic/user/{user_id}/stats")
async def get_user_statistics(user_id: str):
    """
    🏆 Get a user's CityMind points and reporting stats.
    """
    try:
        db = get_firestore()
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
            
        user = db.collection("users").document(user_id).get()
        
        if not user.exists:
            return {
                "success": True,
                "user_id": user_id,
                "total_points": 0,
                "reports_created": 0,
                "verifications_done": 0
            }
        
        user_data = user.to_dict()
        
        return {
            "success": True,
            "user_id": user_id,
            "total_points": user_data.get("total_points", 0),
            "last_action": user_data.get("last_action", "None")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user stats: {str(e)}")


# =========================================================
# OBJECTIVE 3: ENVIRONMENTAL INTELLIGENCE
# =========================================================

@router.get("/environment/air-quality")
async def get_air_quality_endpoint(area: str = None):
    """Get real-time air quality for an area"""
    from app.services.environmental_service import get_air_quality
    try:
        data = await get_air_quality(area)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environment/air-quality/all")
async def get_all_air_quality():
    """Get AQI for all Bengaluru areas"""
    from app.services.environmental_service import get_all_areas_aqi
    try:
        data = await get_all_areas_aqi()
        return {"success": True, "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environment/water-quality")
async def get_water_quality_endpoint(lake_name: str = None):
    """Get water quality for a lake"""
    from app.services.environmental_service import get_water_quality
    try:
        data = await get_water_quality(lake_name)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environment/water-quality/all")
async def get_all_water_quality():
    """Get water quality for all lakes"""
    from app.services.environmental_service import get_all_lakes_quality
    try:
        data = await get_all_lakes_quality()
        return {"success": True, "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environment/health-alert/{area}")
async def get_health_alert(area: str):
    """Get AI-powered health alert for an area"""
    from app.services.environmental_service import get_combined_alert
    try:
        data = await get_combined_alert(area)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environment/heatmap")
async def get_heatmap():
    """Get environmental pollution heatmap"""
    from app.services.environmental_service import get_environmental_heatmap
    try:
        data = await get_environmental_heatmap()
        return {"success": True, "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))