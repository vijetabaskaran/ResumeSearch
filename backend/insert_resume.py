from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from qdrant_client.models import PointStruct
from qdrant import client, collection_name, embedding_model
from ai_model import groq_client

import fitz
import uuid
import os
import requests
import urllib.parse

router = APIRouter()

# Absolute path to uploads directory (same as what app.py mounts)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

print("Insert Resume Router Loaded")

# ==========================================
# INSERT RESUME (File and URL upload supported)
# ==========================================

@router.post("/insert_resume")
async def insert_resume(
    name: str = Form(...),
    file: UploadFile = File(None),
    resume_url: str = Form(None)
):

    try:

        print("\n===================================")
        print("INSERT RESUME API CALLED")
        print("===================================")

        print(f"Candidate Name: {name}")

        if not file and not resume_url:
            return {"error": "Please provide either a PDF file or a PDF URL."}

        if file:
            print(f"Uploaded File Name: {file.filename}")
            if not file.filename.lower().endswith(".pdf"):
                return {"error": "Only PDF files are supported."}

            contents = await file.read()

            file_uuid = str(uuid.uuid4())
            safe_filename = f"{file_uuid}_{file.filename}"
            filepath = os.path.join(UPLOAD_DIR, safe_filename)

            with open(filepath, "wb") as f:
                f.write(contents)

            print("PDF File Saved Successfully at:", filepath)
        else:
            # Download PDF from URL
            resume_url_str = resume_url.strip()
            print(f"Uploaded PDF URL: {resume_url_str}")
            if not (resume_url_str.startswith("http://") or resume_url_str.startswith("https://")):
                return {"error": "Invalid URL. Must start with http:// or https://"}

            try:
                response = requests.get(resume_url_str, timeout=20)
                if response.status_code != 200:
                    return {"error": f"Failed to download PDF from URL (Status code: {response.status_code})"}
                contents = response.content
            except Exception as e:
                return {"error": f"Error downloading PDF from URL: {str(e)}"}

            parsed_url = urllib.parse.urlparse(resume_url_str)
            url_filename = os.path.basename(parsed_url.path)
            if not url_filename.lower().endswith(".pdf"):
                url_filename = "resume.pdf"

            file_uuid = str(uuid.uuid4())
            safe_filename = f"{file_uuid}_{url_filename}"
            filepath = os.path.join(UPLOAD_DIR, safe_filename)

            with open(filepath, "wb") as f:
                f.write(contents)

            print("PDF URL Saved Successfully at:", filepath)

        resume_url = f"http://127.0.0.1:8000/uploads/{safe_filename}"

        doc = fitz.open(filepath)

        # ==========================================
        # EXTRACT TEXT
        # ==========================================

        print("\nExtracting Text From PDF...")

        pdf_text = ""
        for page in doc:

            pdf_text += page.get_text()

        doc.close()

        print("PDF Text Extraction Completed")

        print(f"\nTotal Characters Extracted: {len(pdf_text)}")

        # ==========================================
        # AI SKILL EXTRACTION
        # ==========================================

        print("\nSending Resume to GROQ AI For Skill Extraction...")

        prompt = f"""

Extract ONLY skills from this resume.

STRICT RULES:
- Return ONLY comma separated skills
- No headings
- No categories
- No explanations
- No sentences
- No numbering
- No duplicate skills

Example:
Python, FastAPI, SQL, Communication, Leadership

Resume:

{pdf_text}

"""

        response = groq_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[

                {
                    "role": "user",
                    "content": prompt
                }

            ]

        )

        print("Skills Extracted Successfully")

        extracted_skills = response.choices[0].message.content

        print("\nEXTRACTED SKILLS:")
        print(extracted_skills)

        skills_list = extracted_skills.split(",")

        clean_skills = []

        for skill in skills_list:

            s = skill.strip().lower()

            if s and s not in clean_skills:

                clean_skills.append(s)
                skill_vectors = []

        for skill in clean_skills:

            vector = embedding_model.encode(skill).tolist()

            skill_vectors.append({

                "skill": skill,
                "vector": vector

            })

        final_skills = ", ".join(clean_skills)

        print("\nFINAL CLEAN SKILLS:")
        print(final_skills)

        # ==========================================
        # EMBEDDINGS
        # ==========================================

        print("\nGenerating Embeddings...")

        skills_vector = embedding_model.encode(
            extracted_skills
        ).tolist()

        print("Embeddings Generated Successully")

        # ==========================================
        # STORE IN QDRANT
        # ==========================================

        print("\nPreparing Qdrant Point...")

        point = PointStruct(

            id=str(uuid.uuid4()),

            vector={

                "skills": skills_vector

            },

            payload={

                "name": name,

                "skills": extracted_skills,
                "resume_url": resume_url
            }

        )

        print("Uploading Resume to Qdrant...")

        client.upsert(

            collection_name=collection_name,

            points=[point]

        )

        print("Resume Stored Successfully")

        print("===================================\n")

        return {

            "message": "Resume inserted successfully",

            "skills": extracted_skills

        }

    except Exception as e:

        print("\nERROR IN INSERT RESUME API")
        print(str(e))
        print("===================================\n")

        return {
            "error": str(e)
        }
    
