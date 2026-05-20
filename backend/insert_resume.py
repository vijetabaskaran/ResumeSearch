from fastapi import APIRouter, UploadFile, File, Form
from qdrant_client.models import PointStruct
from qdrant import client, collection_name, embedding_model
from ai_model import groq_client

import requests
import fitz
import uuid

router = APIRouter()

print("Insert Resume Router Loaded")

# ==========================================
# INSERT RESUME
# ==========================================

@router.post("/insert_resume")
async def insert_resume(

    name: str = Form(...),

    resume_url: str = Form(None),

    file: UploadFile = File(None)

):

    try:

        print("\n===================================")
        print("INSERT RESUME API CALLED")
        print("===================================")

        print(f"Candidate Name: {name}")

        pdf_text = ""

        # ==========================================
        # URL PDF
        # ==========================================

        if resume_url:

            print("\nResume Upload Method: URL")
            print(f"Resume URL: {resume_url}")

            print("\nDownloading PDF from URL...")

            response = requests.get(resume_url)

            with open("temp.pdf", "wb") as f:
                f.write(response.content)

            print("PDF Downloaded Successfully")

            doc = fitz.open("temp.pdf")

        # ==========================================
        # FILE PDF
        # ==========================================

        else:

            print("\nResume Upload Method: File")

            print(f"Uploaded File Name: {file.filename}")

            contents = await file.read()

            with open("uploaded.pdf", "wb") as f:
                f.write(contents)

            print("PDF File Saved Successfully")

            doc = fitz.open("uploaded.pdf")

        # ==========================================
        # EXTRACT TEXT
        # ==========================================

        print("\nExtracting Text From PDF...")

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
                "resume_url": resume_url if resume_url else file.filename    
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
    
