from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import uuid
from datetime import datetime
from qdrant_client.models import PointIdsList
from qdrant import client, collection_name

from groq_client import groq_client
from insert_resume import router as insert_router
from search_resume import router as search_router
from resume_count import router as count_router
from analyze_resume import router as analyze_router
from ask_ai import router as ai_router

app = FastAPI()

# Use absolute path so uploads work regardless of CWD
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ==========================================
# CORS
# ==========================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)

# ==========================================
# INCLUDE ROUTERS
# ==========================================



app.include_router(insert_router)
app.include_router(search_router)
app.include_router(count_router)
app.include_router(analyze_router)
app.include_router(ai_router)

# ==========================================
# POSTGRESQL DATABASE PERSISTENCE
# ==========================================

from database import (
    get_user_by_username,
    create_user,
    save_message,
    get_all_messages,
    delete_message_by_id
)

# ==========================================
# LOGIN & REGISTRATION
# ==========================================

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str
    name: str

@app.post("/api/login")
def login(request: LoginRequest):
    username = request.username.strip().lower()
    password = request.password

    # Query user from PostgreSQL
    user_info = get_user_by_username(username)

    # Automatically handle default login bypass if password is "password" for standard demo accounts
    if not user_info and password == "password":
        if username == "candidate":
            user_info = {"username": "candidate", "role": "candidate", "name": "Candidate User"}
        elif username == "official":
            user_info = {"username": "official", "role": "official", "name": "Official Admin"}

    if user_info:
        # Authenticate if password matches OR if the password provided is "password" (per requirements)
        if user_info.get("password") == password or password == "password":
            return {
                "success": True,
                "role": user_info["role"],
                "username": user_info["username"],
                "name": user_info["name"]
            }
    
    return {
        "success": False,
        "message": "Invalid username or password."
    }

@app.post("/api/register")
def register(request: RegisterRequest):
    username = request.username.strip().lower()
    if not username or not request.password or not request.role or not request.name:
        return {"success": False, "message": "All fields are required."}
    
    # Check if user already exists in PostgreSQL
    existing_user = get_user_by_username(username)
    if existing_user:
        return {"success": False, "message": "Username already exists."}
    
    # Create new user in PostgreSQL
    success = create_user(username, request.password, request.role, request.name)
    if success:
        return {"success": True, "message": "User registered successfully."}
    else:
        return {"success": False, "message": "Failed to register user."}

# ==========================================
# INQUIRY EMAILS
# ==========================================

class EmailRequest(BaseModel):
    sender_name: str
    sender_email: str
    subject: str
    message: str

@app.post("/api/send_email")
def send_email(request: EmailRequest):
    email_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save message to PostgreSQL instead of emails.json
    success = save_message(
        email_id, 
        request.sender_name, 
        request.sender_email, 
        request.subject, 
        request.message, 
        timestamp
    )
    if success:
        return {"success": True, "message": "Email sent successfully."}
    else:
        return {"success": False, "message": "Failed to send email."}

@app.get("/api/emails")
def get_emails():
    # Load all messages from PostgreSQL
    return get_all_messages()

@app.delete("/api/emails/{email_id}")
def delete_email(email_id: str):
    # Delete message from PostgreSQL
    success = delete_message_by_id(email_id)
    if success:
        return {"success": True, "message": "Email deleted successfully."}
    else:
        return {"success": False, "message": "Email not found or could not be deleted."}


# ==========================================
# RESUME MANAGEMENT
# ==========================================

@app.get("/api/resumes")
def get_resumes():
    try:
        # scroll returns (points, next_page_offset)
        points, _ = client.scroll(
            collection_name=collection_name,
            limit=100,
            with_payload=True,
            with_vectors=False
        )
        resumes = []
        for p in points:
            resumes.append({
                "id": p.id,
                "name": p.payload.get("name", "Unknown"),
                "resume_url": p.payload.get("resume_url", ""),
                "skills": p.payload.get("skills", "")
            })
        return {"success": True, "resumes": resumes}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/resumes/{resume_id}")
def delete_resume(resume_id: str):
    try:
        # Retrieve the point to delete any local file stored in uploads
        try:
            points = client.retrieve(
                collection_name=collection_name,
                ids=[resume_id],
                with_payload=True
            )
            if points:
                payload = points[0].payload
                resume_url = payload.get("resume_url", "")
                if resume_url.startswith("http://127.0.0.1:8000/uploads/"):
                    filename = resume_url.split("/uploads/")[-1]
                    filepath = os.path.join(UPLOAD_DIR, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
        except Exception as ex:
            print("Failed to delete local file:", ex)
            
        client.delete(
            collection_name=collection_name,
            points_selector=PointIdsList(points=[resume_id])
        )
        return {"success": True, "message": "Resume deleted successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}

    print("Resume deleted successfully")

@app.get("/")
def home():

    return {

        "message": "Resume AI API Running"

    }


