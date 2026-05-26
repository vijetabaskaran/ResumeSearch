from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import uuid
import fitz
from datetime import datetime
from qdrant_client.models import PointIdsList
from qdrant import client, collection_name, embedding_model

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
    verify_password,
    save_message,
    get_all_messages,
    delete_message_by_id,
    save_job_description,
    get_all_job_descriptions,
    delete_job_description_by_id
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

    if user_info:
        # Authenticate using bcrypt verification
        stored_hash = user_info.get("password", "")
        if verify_password(password, stored_hash):
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
    # Save message to PostgreSQL — ID and timestamps handled by DB
    success = save_message(
        request.sender_name, 
        request.sender_email, 
        request.subject, 
        request.message
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
# JOB DESCRIPTIONS
# ==========================================

class JobDescriptionRequest(BaseModel):
    title: str
    department: str
    description: str

@app.post("/api/job_descriptions")
async def add_job_description(
    title: str = Form(...),
    department: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(None)
):
    try:
        if not file and not description:
            return {"success": False, "message": "Please provide either description text or a file."}

        if file:
            filename = file.filename.lower()
            if not (filename.endswith(".pdf") or filename.endswith(".txt")):
                return {"success": False, "message": "Only PDF and TXT files are supported for job description upload."}
            
            contents = await file.read()
            file_uuid = str(uuid.uuid4())
            safe_filename = f"jd_{file_uuid}_{file.filename}"
            filepath = os.path.join(UPLOAD_DIR, safe_filename)
            
            with open(filepath, "wb") as f:
                f.write(contents)
            
            extracted_text = ""
            if filename.endswith(".pdf"):
                doc = fitz.open(filepath)
                pdf_text = ""
                for page in doc:
                    pdf_text += page.get_text()
                doc.close()
                extracted_text = pdf_text.strip()
            elif filename.endswith(".txt"):
                try:
                    extracted_text = contents.decode("utf-8").strip()
                except UnicodeDecodeError:
                    extracted_text = contents.decode("latin-1").strip()
            
            if not extracted_text:
                return {"success": False, "message": "Could not extract any text content from the uploaded file."}
            
            description = extracted_text

        # ID and timestamps handled by the DB
        jd_id = save_job_description(
            title,
            department,
            description
        )
        if jd_id:
            return {"success": True, "message": "Job description saved successfully.", "id": jd_id}
        else:
            return {"success": False, "message": "Failed to save job description."}
    except Exception as e:
        return {"success": False, "message": f"Error saving job description: {str(e)}"}

@app.get("/api/job_descriptions")
def get_job_descriptions():
    try:
        jds = get_all_job_descriptions()
        return {"success": True, "job_descriptions": jds}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/job_descriptions/{jd_id}")
def delete_job_description(jd_id: str):
    success = delete_job_description_by_id(jd_id)
    if success:
        return {"success": True, "message": "Job description deleted successfully."}
    else:
        return {"success": False, "message": "Failed to delete job description."}

@app.get("/api/job_descriptions/{jd_id}/match")
def match_job_description(jd_id: str):
    try:
        jds = get_all_job_descriptions()
        jd = None
        for item in jds:
            if str(item["id"]) == jd_id:
                jd = item
                break
        
        if not jd:
            return {"success": False, "error": "Job description not found."}
        
        # Build query embedding
        query_text = f"{jd['title']} {jd['description']}"
        query_embedding = embedding_model.encode(query_text).tolist()
        
        # Query Qdrant
        search_result = client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            using="skills",
            limit=20
        )
        
        results = []
        for point in search_result.points:
            score = point.score
            if score >= 0.5:
                match_percentage = max(0.0, min(100.0, round(score * 100, 1)))
                results.append({
                    "name": point.payload.get("name", "Unknown"),
                    "skills": point.payload.get("skills", ""),
                    "resume_url": point.payload.get("resume_url", ""),
                    "match_percentage": f"{match_percentage}%",
                    "score": score
                })
            
        # Sort results
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Clean score out
        for r in results:
            r.pop("score", None)
            
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


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


