from fastapi import FastAPI
from app.services.correlation_service import router as correlation_router
from app.services.fusion_service import router as fusion_router
from app.services.cascade_service import router as cascade_router

app = FastAPI()

# Register routers
app.include_router(fusion_router)
app.include_router(correlation_router)
app.include_router(cascade_router)


@app.get("/")
def root():
    return {"message": "Urban AI Backend is running 🚀"}
