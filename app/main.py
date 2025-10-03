from fastapi import FastAPI
from app.services import fusion_service
from app.api import routes
from app.utils import firebase_config

app = FastAPI()

# Register routers
app.include_router(fusion_service.router)
app.include_router(routes.router)

@app.get("/")
def root():
    return {"message": "Urban AI Backend is running 🚀"}