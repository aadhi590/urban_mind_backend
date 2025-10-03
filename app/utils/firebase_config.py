import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase Admin SDK
try:
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized")
    else:
        firebase_admin.initialize_app()
        print("✅ Firebase initialized (default)")
    
    db = firestore.client()
    print("✅ Firestore ready")
    
except Exception as e:
    print(f"⚠️ Firebase init failed: {e}")
    db = None

def get_firestore():
    return db