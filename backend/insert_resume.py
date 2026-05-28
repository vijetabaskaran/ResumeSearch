from fastapi import APIRouter, UploadFile, File, Form
from qdrant_client.models import PointStruct
from qdrant import client, collection_name, embedding_model
from ai_model import groq_client
from services.upload_service import handle_upload

import uuid

router = APIRouter()

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

        try:
            upload = await handle_upload(
                file=file,
                source_url=resume_url,
                allowed_extensions=(".pdf",),
                default_url_filename="resume.pdf"
            )
        except ValueError as error:
            return {"error": str(error)}

        resume_url = upload.url
        pdf_text = upload.text

        print("PDF Text Extraction Completed")

        print(f"\nTotal Characters Extracted: {len(pdf_text)}")

        # ==========================================
        # AI SKILL EXTRACTION
        # ==========================================

        # Optimize prompt token usage by truncating extremely long resumes
        optimized_pdf_text = pdf_text[:12000]

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

{optimized_pdf_text}

"""

        response = groq_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            max_tokens=250,

            messages=[

                {
                    "role": "user",
                    "content": prompt
                }

            ]

        )

        print("Skills Extracted Successfully")

        usage = response.usage
        print(f"Token Usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")

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

            "skills": extracted_skills,
            "token_usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens
            }

        }

    except Exception as e:

        print("\nERROR IN INSERT RESUME API")
        print(str(e))
        print("===================================\n")

        return {
            "error": str(e)
        }
    
