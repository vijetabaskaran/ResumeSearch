from fastapi import APIRouter
from services.search_service import public_search_results, search_candidates
from database import log_activity


router = APIRouter()


@router.get("/search_resume")
def search_resume(skill: str):
    print(f"\n[API GET] /search_resume called with skill query: '{skill}'")
    try:
        matches = search_candidates(
            query_text=skill,
            limit=20,
            required_skill=skill
        )
        print(f"[API GET] /search_resume succeeded. Returning {len(matches)} results.")
        # Log recruitment activity (non-blocking)
        log_activity("resume_search", f"Resume search performed for: \"{skill}\"", "official")
        return {"results": public_search_results(matches)}
    except Exception as e:
        print("[API GET ERROR] /search_resume failed:", str(e))
        return {"error": str(e)}
