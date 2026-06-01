import os

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct
)

from sentence_transformers import SentenceTransformer

from groq import Groq

import requests
import uuid
import fitz
from dotenv import load_dotenv
load_dotenv()
# ==========================================
# FASTAPI
# ==========================================

app = FastAPI(debug=True)

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
# GROQ CLIENT
# ==========================================

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Resume API Running"
    }

# ==========================================
# RESUME COUNT
# ==========================================

@app.get("/resume_count")
def resume_count():

    try:

        count_result = client.count(
            collection_name=collection_name,
            exact=True
        )

        return {
            "total_resumes": count_result.count
        }

    except Exception as e:

        return {
            "error": str(e)
        }

# ==========================================
# INSERT RESUME
# ==========================================

@app.post("/insert_resume")
async def insert_resume(
    name: str = Form(...),
    resume_url: str = Form(None),
    file: UploadFile = File(None)
):

    try:

        pdf_text = ""

        # ==========================================
        # READ PDF FROM URL
        # ==========================================

        if resume_url:

            response = requests.get(resume_url)

            with open("temp.pdf", "wb") as f:
                f.write(response.content)

            doc = fitz.open("temp.pdf")

        # ==========================================
        # READ PDF FROM FILE
        # ==========================================

        else:

            print("Reading PDF from uploaded file...")

            contents = await file.read()

            with open("uploaded.pdf", "wb") as f:
                f.write(contents)

            doc = fitz.open("uploaded.pdf")

        # ==========================================
        # EXTRACT TEXT
        # ==========================================

        for page in doc:

            pdf_text += page.get_text()

        doc.close()

        # ==========================================
        # SKILL EXTRACTION USING GROQ
        # ==========================================

        skill_prompt = f"""

Extract only technical , non technical , communication skills from this resume.

Return only comma separated skills.

Resume:

{pdf_text}

"""

        skill_response = groq_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[

                {
                    "role": "user",
                    "content": skill_prompt
                }

            ]

        )

        extracted_skills = skill_response.choices[0].message.content

        # ==========================================
        # CREATE EMBEDDINGS
        # ==========================================

        full_text_vector = embedding_model.encode(
            pdf_text
        ).tolist()

        skills_vector = embedding_model.encode(
            extracted_skills
        ).tolist()

        # ==========================================
        # STORE IN QDRANT
        # ==========================================

        point = PointStruct(

            id=str(uuid.uuid4()),

            vector={

                "full_text": full_text_vector,

                "skills": skills_vector

            },

            payload={

                "name": name,

                "text": pdf_text,

                "skills": extracted_skills,

                "resume_url": resume_url if resume_url else file.filename

            }

            print("Point Struct Created")

        )

        client.upsert(

            collection_name=collection_name,

            points=[point]

        )

        print("Resume Inserted Successfully")

        return {

            "message": "Resume inserted successfully",

            "skills": extracted_skills

        }

    except Exception as e:

        return {

            "error": str(e)

        }

# ==========================================
# SEARCH RESUME
# ==========================================

@app.get("/search_resume")
def search_resume(skill: str):

    try:

        query_embedding = embedding_model.encode(
            skill
        ).tolist()

        search_result = client.query_points(

            collection_name=collection_name,

            query=query_embedding,

            using="skills",

            limit=5

        )

        resumes = []

        for point in search_result.points:

            resumes.append({

                "name": point.payload.get("name"),

                "resume_url": point.payload.get("resume_url"),

                "skills": point.payload.get("skills")

            })

        return {

            "results": resumes

        }

    except Exception as e:

        return {

            "error": str(e)

        }

# ==========================================
# ANALYZE RESUME
# ==========================================

@app.get("/analyze_resume")
def analyze_resume(skill: str):

    try:

        query_embedding = embedding_model.encode(
            skill
        ).tolist()

        search_result = client.query_points(

            collection_name=collection_name,

            query=query_embedding,

            using="skills",

            limit=1

        )

        if len(search_result.points) == 0:

            return {

                "error": "No matching resume found"

            }

        point = search_result.points[0]

        resume_text = point.payload.get(
            "text",
            ""
        )

        candidate_name = point.payload.get(
            "name",
            "Unknown"
        )

        prompt = f"""

Analyze this resume.

Candidate Name:
{candidate_name}

Resume:
{resume_text}

Give:

1. Candidate Summary
2. Technical Skills
3. Experience Level
4. Best Suitable Role
5. Strengths
6. Weaknesses
7. Candidate Score out of 10

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

        analysis = response.choices[0].message.content

        return {

            "candidate_name": candidate_name,

            "analysis": analysis

        }

    except Exception as e:

        return {

            "error": str(e)

        }

# ==========================================
# REQUEST MODEL
# ==========================================

class AIRequest(BaseModel):
    question: str

# ==========================================
# AI CHAT
# ==========================================

@app.post("/ask_ai")
async def chat_with_ai(data: AIRequest):

    try:

        response = groq_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[

                {
                    "role": "user",
                    "content": data.question
                }

            ]

        )

        answer = response.choices[0].message.content

        return {
            "answer": answer
        }

    except Exception as e:

        return {
            "answer": str(e)
        }