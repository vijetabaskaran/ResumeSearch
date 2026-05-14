from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from sentence_transformers import SentenceTransformer

import requests
import uuid
import fitz   # pip install pymupdf

# ==========================================
# FASTAPI APP
# ==========================================

app = FastAPI(debug=True)

# ==========================================
# CORS CONFIGURATION
# ==========================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)

# ==========================================
# QDRANT CONNECTION
# ==========================================

client = QdrantClient(
    url="https://5da3fc0c-a55d-4bde-85ca-fd55b7d4acd6.sa-east-1-0.aws.cloud.qdrant.io",

    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6YTVhYjg1MDMtOGNlNC00M2ZkLWI4YjgtZTg2Njk1ZWM4NjgxIn0.zLY98pLjgc2LZOSQSEGMeHyqjcNQ57PX8VI8PJllkOM"
)

collection_name = "resumes"

# ==========================================
# CREATE COLLECTION
# ==========================================

if not client.collection_exists(collection_name):

    client.create_collection(
        collection_name=collection_name,

        vectors_config={
            "full_text": VectorParams(
                size=384,
                distance=Distance.COSINE
            ),

            "skills": VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        }
    )

# ==========================================
# LOAD MODEL
# ==========================================

model = SentenceTransformer("all-MiniLM-L6-v2")

# ==========================================
# REQUEST MODELS
# ==========================================

class ResumeInput(BaseModel):
    name: str
    resume_url: str


class SearchInput(BaseModel):
    skills: str


class EditResume(BaseModel):
    id: int
    updated_text: str

# ==========================================
# EXTRACT SKILLS SECTION
# ==========================================

def extract_skills_section(text: str):

    headers = [
        "experience",
        "work experience",
        "professional experience",
        "education",
        "projects",
        "certifications",
        "summary",
        "objective"
    ]

    skills_headers = [
        "skills",
        "technical skills",
        "core competencies",
        "it skills"
    ]

    lines = text.split("\n")

    skills_text = []

    in_skills = False

    for line in lines:

        clean_line = line.strip().lower()

        if clean_line.endswith(":"):
            clean_line = clean_line[:-1]

        if not in_skills:

            if clean_line in skills_headers:

                in_skills = True
                continue

        else:

            if clean_line in headers:
                break

            skills_text.append(line)

    return "\n".join(skills_text).strip()

# ==========================================
# EXTRACT TEXT FROM PDF URL
# ==========================================

def extract_text_from_url(url):

    try:

        response = requests.get(url, timeout=15)

        if response.status_code != 200:

            raise HTTPException(
                status_code=400,
                detail="Unable to fetch resume"
            )

        pdf_path = "temp_resume.pdf"

        with open(pdf_path, "wb") as file:
            file.write(response.content)

        doc = fitz.open(pdf_path)

        text = ""

        for page in doc:
            text += page.get_text()

        doc.close()

        return text.strip()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Resume Search API using Qdrant"
    }

# ==========================================
# GET COLLECTIONS
# ==========================================

@app.get("/collections")
def get_collections():

    return client.get_collections()

# ==========================================
# INSERT RESUME
# ==========================================

@app.post("/insert_resume")
def insert_resume(data: ResumeInput):

    try:

        print(f"Extracting resume from: {data.resume_url}")

        # Extract resume text
        resume_text = extract_text_from_url(data.resume_url)

        if not resume_text:

            raise HTTPException(
                status_code=400,
                detail="No text extracted"
            )

        print("Resume text extracted")

        # Extract skills section
        skills_text = extract_skills_section(resume_text)

        print(f"Skills extracted: {bool(skills_text)}")

        # Create vectors
        full_text_vector = model.encode(resume_text).tolist()

        if skills_text:
            skills_vector = model.encode(skills_text).tolist()
        else:
            skills_vector = full_text_vector

        print("Vectors created")

        # Unique ID
        point_id = int(uuid.uuid4().int % 1000000)

        # Create point
        point = PointStruct(
            id=point_id,

            vector={
                "full_text": full_text_vector,
                "skills": skills_vector
            },

            payload={
                "name": data.name,
                "resume_url": data.resume_url,
                "resume_text": resume_text,
                "skills_text": skills_text
            }
        )

        # Insert into Qdrant
        client.upsert(
            collection_name=collection_name,
            points=[point]
        )

        return {
            "message": "Resume inserted successfully",
            "id": point_id
        }

    except Exception as e:

        print("INSERT ERROR:", str(e))

        return {
            "error": str(e)
        }

# ==========================================
# SEARCH RESUME
# ==========================================

@app.post("/search")
def search_resume(data: SearchInput):

    try:

        print("Search started")

        # Convert query into vector
        query_vector = model.encode(data.skills).tolist()

        print("Query vector created")

        # Search Qdrant
        response = client.query_points(
            collection_name=collection_name,

            query=query_vector,

            using="skills",

            limit=3
        )

        print("Search completed")

        results = []

        for result in response.points:

            results.append({
                "id": result.id,
                "name": result.payload.get("name"),
                "resume_url": result.payload.get("resume_url"),
                "score": round(result.score, 4)
            })

        return results

    except Exception as e:

        print("SEARCH ERROR:", str(e))

        return {
            "error": str(e)
        }

# ==========================================
# EDIT RESUME
# ==========================================

@app.post("/edit_resume")
def edit_resume(data: EditResume):

    try:

        print(f"Updating resume ID: {data.id}")

        # Extract skills section
        skills_text = extract_skills_section(data.updated_text)

        # Create vectors
        full_text_vector = model.encode(data.updated_text).tolist()

        if skills_text:
            skills_vector = model.encode(skills_text).tolist()
        else:
            skills_vector = full_text_vector

        # Retrieve old point
        old_point = client.retrieve(
            collection_name=collection_name,
            ids=[data.id]
        )

        if not old_point:

            raise HTTPException(
                status_code=404,
                detail="Resume ID not found"
            )

        old_payload = old_point[0].payload

        # Update point
        client.upsert(
            collection_name=collection_name,

            points=[
                PointStruct(
                    id=data.id,

                    vector={
                        "full_text": full_text_vector,
                        "skills": skills_vector
                    },

                    payload={
                        "name": old_payload.get("name"),
                        "resume_url": old_payload.get("resume_url"),
                        "resume_text": data.updated_text,
                        "skills_text": skills_text
                    }
                )
            ]
        )

        return {
            "message": "Resume updated successfully"
        }

    except Exception as e:

        print("UPDATE ERROR:", str(e))

        return {
            "error": str(e)
        }