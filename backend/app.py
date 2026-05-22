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
# JSON PERSISTENCE HELPERS
# ==========================================

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
EMAILS_FILE = os.path.join(os.path.dirname(__file__), "emails.json")

def load_users():
    if not os.path.exists(USERS_FILE):
        # Seed with initial demo users
        initial_users = {
            "candidate": {
                "username": "candidate",
                "password": "password",
                "role": "candidate",
                "name": "Candidate User"
            },
            "official": {
                "username": "official",
                "password": "password",
                "role": "official",
                "name": "Official Admin"
            }
        }
        save_users(initial_users)
        return initial_users
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except Exception as e:
        print("Error saving users:", e)

def load_emails():
    if not os.path.exists(EMAILS_FILE):
        return []
    try:
        with open(EMAILS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_emails(emails):
    try:
        with open(EMAILS_FILE, "w") as f:
            json.dump(emails, f, indent=4)
    except Exception as e:
        print("Error saving emails:", e)

# Initialize files
load_users()
load_emails()

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

    users = load_users()
    if username in users and users[username]["password"] == password:
        user_info = users[username]
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

    print("Login successful")

@app.post("/api/register")
def register(request: RegisterRequest):
    username = request.username.strip().lower()
    if not username or not request.password or not request.role or not request.name:
        return {"success": False, "message": "All fields are required."}
    
    users = load_users()
    if username in users:
        return {"success": False, "message": "Username already exists."}
    
    users[username] = {
        "username": username,
        "password": request.password,
        "role": request.role,
        "name": request.name
    }
    save_users(users)
    return {"success": True, "message": "User registered successfully."}
    print("Registration successful")

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
    emails = load_emails()
    email_id = str(uuid.uuid4())
    new_email = {
        "id": email_id,
        "sender_name": request.sender_name,
        "sender_email": request.sender_email,
        "subject": request.subject,
        "message": request.message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    emails.append(new_email)
    save_emails(emails)
    return {"success": True, "message": "Email sent successfully."}

@app.get("/api/emails")
def get_emails():
    return load_emails()

@app.delete("/api/emails/{email_id}")
def delete_email(email_id: str):
    emails = load_emails()
    filtered_emails = [e for e in emails if e["id"] != email_id]
    if len(filtered_emails) == len(emails):
        return {"success": False, "message": "Email not found."}
    save_emails(filtered_emails)
    return {"success": True, "message": "Email deleted successfully."}

    print("Email deleted successfully")

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


