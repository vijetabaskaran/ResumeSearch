from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
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

# Import reusable services
from services.search_service import search_candidates, public_search_results
from services.upload_service import handle_upload

app = FastAPI()

# ==========================================
# ROLE GUARD — OFFICIAL-ONLY ROUTE PROTECTION
# ==========================================

def require_official(request: Request):
    """
    Dependency that enforces the caller is an authenticated official/admin.
    The frontend sends 'X-User-Role: official' in the request headers for all
    protected API calls after a successful admin login.

    NOTE: This header-based guard is appropriate for an internal/local tool.
    For production deployments, replace with JWT token verification.
    """
    role = request.headers.get("X-User-Role", "").strip().lower()
    if role != "official":
        raise HTTPException(
            status_code=403,
            detail="Access denied. Official role required."
        )

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
    delete_job_description_by_id,
    save_reply,
    get_replies_for_user,
    get_replies_for_message,
    get_faq_entries
)


# ==========================================
# LOGIN & REGISTRATION
# ==========================================

class LoginRequest(BaseModel):
    username: str
    password: str
    # NOTE: role is no longer accepted from frontend — it is enforced by the endpoint

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    email: str  # Candidate email collected during registration
    # NOTE: role is always hardcoded to "candidate" — not accepted from frontend

@app.post("/api/login")
def candidate_login(request: LoginRequest):
    """
    Candidate-only login endpoint.
    Rejects any account whose stored role is not 'candidate'.
    """
    username = request.username.strip().lower()
    password = request.password

    user_info = get_user_by_username(username)

    if user_info:
        stored_role = user_info.get("role", "").lower()
        # Enforce: this endpoint is for candidates only
        if stored_role != "candidate":
            return {
                "success": False,
                "message": "This account is not a candidate account. Please use the Official Login."
            }
        stored_hash = user_info.get("password", "")
        if verify_password(password, stored_hash):
            return {
                "success": True,
                "role": user_info["role"],
                "username": user_info["username"],
                "name": user_info["name"],
                "email": user_info.get("email", "")
            }

    return {
        "success": False,
        "message": "Invalid username or password."
    }

@app.post("/api/admin-login")
def official_login(request: LoginRequest):
    """
    Official/Admin-only login endpoint.
    Rejects any account whose stored role is not 'official'.
    Official accounts must be created directly in the database — no public registration.
    """
    username = request.username.strip().lower()
    password = request.password

    user_info = get_user_by_username(username)

    if user_info:
        stored_role = user_info.get("role", "").lower()
        # Enforce: this endpoint is for officials only
        if stored_role != "official":
            return {
                "success": False,
                "message": "Access denied. This account does not have official privileges."
            }
        stored_hash = user_info.get("password", "")
        if verify_password(password, stored_hash):
            return {
                "success": True,
                "role": user_info["role"],
                "username": user_info["username"],
                "name": user_info["name"],
                "email": user_info.get("email", "")
            }

    return {
        "success": False,
        "message": "Invalid credentials or insufficient privileges."
    }

@app.post("/api/register")
def register(request: RegisterRequest):
    """
    Candidate-only public registration.
    Role is always hardcoded to 'candidate' — the frontend cannot influence it.
    """
    username = request.username.strip().lower()
    if not username or not request.password or not request.name:
        return {"success": False, "message": "All fields are required."}

    if not request.email or not request.email.strip():
        return {"success": False, "message": "Email address is required."}

    # Check if user already exists
    existing_user = get_user_by_username(username)
    if existing_user:
        return {"success": False, "message": "Username already exists."}

    # Always register as candidate — role is not user-controlled
    success = create_user(username, request.password, "candidate", request.name, request.email.strip())
    if success:
        return {"success": True, "message": "Account registered successfully."}
    else:
        return {"success": False, "message": "Failed to register user."}



# ==========================================
# INQUIRY EMAILS / MESSAGES
# ==========================================

class EmailRequest(BaseModel):
    sender_name: str
    sender_email: str
    sender_username: str = ""  # Link message to the logged-in candidate
    subject: str
    message: str

@app.post("/api/send_email")
def send_email(request: EmailRequest):
    # Save message to PostgreSQL with sender_username linkage
    success = save_message(
        request.sender_name, 
        request.sender_email, 
        request.subject, 
        request.message,
        request.sender_username
    )
    if success:
        return {"success": True, "message": "Email sent successfully."}
    else:
        return {"success": False, "message": "Failed to send email."}

@app.get("/api/emails")
def get_emails(request: Request, _: None = None):
    """Official-only: retrieve all candidate messages."""
    require_official(request)
    # Load all messages from PostgreSQL
    return get_all_messages()

@app.delete("/api/emails/{email_id}")
def delete_email(email_id: str, request: Request):
    """Official-only: soft-delete a candidate message."""
    require_official(request)
    # Delete message from PostgreSQL
    success = delete_message_by_id(email_id)
    if success:
        return {"success": True, "message": "Email deleted successfully."}
    else:
        return {"success": False, "message": "Email not found or could not be deleted."}

# ==========================================
# REPLIES
# ==========================================

class ReplyRequest(BaseModel):
    message_id: str
    sender_username: str  # The official/admin sending the reply
    reply_text: str
    is_faq: bool = False  # If True, publish this Q&A pair to the public FAQ section

@app.post("/api/replies")
def create_reply(request: ReplyRequest, http_request: Request):
    """Official-only: store a reply from an official to a candidate's message."""
    require_official(http_request)
    if not request.reply_text.strip():
        return {"success": False, "message": "Reply text cannot be empty."}

    reply_id = save_reply(
        request.message_id,
        request.sender_username,
        request.reply_text.strip(),
        request.is_faq
    )
    if reply_id:
        return {"success": True, "message": "Reply sent successfully.", "id": reply_id, "is_faq": request.is_faq}
    else:
        return {"success": False, "message": "Failed to send reply."}

@app.get("/api/replies/{username}")
def get_user_replies(username: str):
    """Get all replies directed to messages sent by a specific candidate."""
    replies = get_replies_for_user(username)
    return {"success": True, "replies": replies}

@app.get("/api/faq")
def get_faq():
    """Public: retrieve all Q&A pairs approved for FAQ display.
    
    No authentication required — any visitor (logged-in or not) can read the FAQ.
    Returns only entries where is_faq=TRUE and neither the reply nor the original
    message has been soft-deleted.
    """
    faqs = get_faq_entries()
    return {"success": True, "faqs": faqs}

# ==========================================
# JOB DESCRIPTIONS
# ==========================================

class JobDescriptionRequest(BaseModel):
    title: str
    department: str
    description: str

@app.post("/api/job_descriptions")
async def add_job_description(
    request: Request,
    title: str = Form(...),
    department: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(None)
):
    """Official-only: create a new job description."""
    require_official(request)
    try:
        if not file and not description:
            return {"success": False, "message": "Please provide either description text or a file."}

        # Use the reusable upload service for file-based JD creation
        if file:
            try:
                upload = await handle_upload(
                    file=file,
                    allowed_extensions=(".pdf", ".txt"),
                    prefix="jd_",
                    default_url_filename="job_description.pdf"
                )
            except ValueError as error:
                return {"success": False, "message": str(error)}

            description = upload.text

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
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "message": f"Error saving job description: {str(e)}"}

@app.get("/api/job_descriptions")
def get_job_descriptions():
    """Public: candidates and officials can view job descriptions."""
    try:
        jds = get_all_job_descriptions()
        return {"success": True, "job_descriptions": jds}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/job_descriptions/{jd_id}")
def delete_job_description(jd_id: str, request: Request):
    """Official-only: delete a job description."""
    require_official(request)
    success = delete_job_description_by_id(jd_id)
    if success:
        return {"success": True, "message": "Job description deleted successfully."}
    else:
        return {"success": False, "message": "Failed to delete job description."}

@app.get("/api/job_descriptions/{jd_id}/match")
def match_job_description(jd_id: str, request: Request):
    """Official-only: match candidates against a job description."""
    require_official(request)
    print(f"\n[API GET] /api/job_descriptions/{jd_id}/match called")
    try:
        jds = get_all_job_descriptions()
        jd = None
        for item in jds:
            if str(item["id"]) == jd_id:
                jd = item
                break

        if not jd:
            print(f"[API GET ERROR] Job description {jd_id} not found.")
            return {"success": False, "error": "Job description not found."}

        # Build query text from JD title + description
        query_text = f"{jd['title']} {jd['description']}"
        print(f"[API GET] Matching candidates for Job Description: '{jd['title']}'")

        # Use the reusable search function (same as resume search)
        matches = search_candidates(
            query_text=query_text,
            limit=20,
            required_skill=None  # No specific skill filter for JD matching
        )

        # Strip internal scoring fields for client response
        results = public_search_results(matches)
        print(f"[API GET] /api/job_descriptions/{jd_id}/match succeeded. Returning {len(results)} matches.")

        return {"success": True, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API GET ERROR] /api/job_descriptions/{jd_id}/match failed: {e}")
        return {"success": False, "error": str(e)}


# ==========================================
# RESUME MANAGEMENT
# ==========================================

@app.get("/api/resumes")
def get_resumes(request: Request):
    """Official-only: list all resumes in the system."""
    require_official(request)
    try:
        points = []
        next_page_offset = None

        while True:
            batch, next_page_offset = client.scroll(
                collection_name=collection_name,
                limit=100,
                offset=next_page_offset,
                with_payload=True,
                with_vectors=False
            )
            points.extend(batch)
            if next_page_offset is None:
                break

        resumes = []
        for p in points:
            resumes.append({
                "id": str(p.id),
                "name": p.payload.get("name", "Unknown"),
                "resume_url": p.payload.get("resume_url", ""),
                "skills": p.payload.get("skills", "")
            })
        return {"success": True, "resumes": resumes}
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/resumes/{resume_id}")
def delete_resume(resume_id: str, request: Request):
    """Official-only: delete a resume from the vector store."""
    require_official(request)
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
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/")
def home():

    return {

        "message": "Resume AI API Running"

    }
