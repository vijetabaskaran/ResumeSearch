from fastapi import APIRouter
from qdrant import client, collection_name, embedding_model
from ai_model import groq_client

router = APIRouter()

print("Analyze Resume Router Loaded")

@router.get("/analyze_resume")
def analyze_resume(skill: str):

    try:

        print("\n===================================")
        print("ANALYZE RESUME API CALLED")
        print("===================================")

        print("Skill Received:")
        print(skill)

        # ==========================================
        # CREATE QUERY EMBEDDING
        # ==========================================

        print("\nGenerating Embedding...")

        query_embedding = embedding_model.encode(
            skill
        ).tolist()

        print("Embedding Generated Successfully")

        # ==========================================
        # SEARCH IN QDRANT
        # ==========================================

        print("\nSearching Resume in Qdrant Database...")

        search_result = client.query_points(

            collection_name=collection_name,

            query=query_embedding,

            using="skills",

            limit=1
        )

        print("Search Completed")

        # ==========================================
        # CHECK RESULTS
        # ==========================================

        if len(search_result.points) == 0:

            print("No Matching Resume Found")

            return {

                "error": "No matching resume found"

            }

        print("Matching Resume Found")

        # ==========================================
        # GET RESUME DATA
        # ==========================================

        point = search_result.points[0]

        resume_text = point.payload.get(
            "text",
            ""
        )

        candidate_name = point.payload.get(
            "name",
            "Unknown"
        )

        print("\nCandidate Name:")
        print(candidate_name)

        print("\nResume Text Extracted")

        # ==========================================
        # CREATE PROMPT
        # ==========================================

        # Optimize prompt token usage by truncating extremely long resumes
        optimized_resume_text = resume_text[:12000]

        prompt = f"""

Analyze this resume.

Candidate Name:
{candidate_name}

Resume:
{optimized_resume_text}

Give:
1. Candidate Summary
2. Technical Skills
3. Experience Level
4. Best Suitable Role
5. Strengths
6. Weaknesses
7. Candidate Score out of 10

"""

        print("\nSending Resume to GROQ LLM...")

        # ==========================================
        # CALL LLM
        # ==========================================

        response = groq_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            max_tokens=800,

            messages=[

                {
                    "role": "user",
                    "content": prompt
                }

            ]

        )

        print("Response Received From GROQ")

        usage = response.usage
        print(f"Token Usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")

        analysis = response.choices[0].message.content

        print("\nAI ANALYSIS:")
        print(analysis)

        print("===================================\n")

        return {

            "candidate_name": candidate_name,

            "analysis": analysis,
            "token_usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens
            }

        }

    except Exception as e:

        print("\nERROR IN ANALYZE RESUME API")
        print(str(e))
        print("===================================\n")

        return {

            "error": str(e)

        }