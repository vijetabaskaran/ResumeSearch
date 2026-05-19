from fastapi import APIRouter
from qdrant import client, collection_name, embedding_model

router = APIRouter()

@router.get("/search_resume")
def search_resume(skill: str):

    try:

        print("\n========== SEARCH RESUME API ==========")

        print("Skill Received:")
        print(skill)

        # ==========================================
        # CREATE QUERY EMBEDDING
        # ==========================================

        print("\nCreating embedding for search skill...")

        query_embedding = embedding_model.encode(
            skill
        ).tolist()

        print("Embedding Created Successfully")

        # ==========================================
        # SEARCH ALL MATCHING RESUMES
        # ==========================================

        print("\nSearching resumes from Qdrant...")

        search_result = client.query_points(

            collection_name=collection_name,

            query=query_embedding,

            using="skills",

            limit=20

        )

        print("Search Completed")

        # ==========================================
        # SCORE THRESHOLD
        # ==========================================

        THRESHOLD_SCORE = 0.0  # lowered to include all matches

        print(f"\nThreshold Score: {THRESHOLD_SCORE}")

        matched_resumes = []

        # ==========================================
        # FILTER USING SCORE
        # ==========================================

        print("\n========== SEARCH RESULTS ==========")

        for point in search_result.points:

            print("\nFULL POINT:")
            print(point)

            print("\nCandidate Name:")
            print(point.payload.get("name"))

            print("\nStored Skills:")
            print(point.payload.get("skills"))

            print("\n========== STORED PAYLOAD ==========")
            print(point.payload)

            print("\nSimilarity Score:")
            print(point.score)

            score = point.score

            matched_resumes.append({
                "name": point.payload.get("name"),
                "resume_url": point.payload.get("resume_url"),
                "skills": point.payload.get("skills"),
                "score": round(score, 4)
            })

        # ==========================================
        # NO MATCH FOUND (handled after sorting)
        # ==========================================

        # If no resumes meet the threshold, we still want to return an empty list after sorting.
        # Sorting will be performed below regardless of count.

        # ==========================================
        # SORT BY SCORE DESCENDING
        # ==========================================

        matched_resumes = sorted(
            matched_resumes,
            key=lambda x: x["score"],
            reverse=True
        )

        print("\nFinal Matching Candidates:")
        print(matched_resumes)

        print("\n========== SEARCH FINISHED ==========\n")

        return {
            "results": matched_resumes
        }

    except Exception as e:

        print("\nSEARCH ERROR:")
        print(str(e))

        return {

            "error": str(e)

        }
    