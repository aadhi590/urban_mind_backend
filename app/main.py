from fastapi import FastAPI
from app.services import fusion_service

app = FastAPI()

# Register routers
app.include_router(fusion_service.router)

@app.get("/")
def root():
    return {"message": "Urban AI Backend is running 🚀"}
