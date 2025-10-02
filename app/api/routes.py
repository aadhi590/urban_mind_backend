from fastapi import APIRouter
from app.services.fusion_service import fuse_data

router = APIRouter()

@router.post("/fuse")
async def fuse_endpoint(payload: dict):
    """
    Accepts multiple datasets from different sources and returns fused intelligence.
    Example payload:
    {
        "traffic": [{"id": 1, "location": "MG Road", "status": "jam"}],
        "public_reports": [{"id": "r1", "text": "Traffic jam at MG Road"}]
    }
    """
    result = fuse_data(payload)
    return {"fused_insight": result}
