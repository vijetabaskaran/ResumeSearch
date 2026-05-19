from fastapi import APIRouter

from qdrant import client, collection_name

router = APIRouter()

print("Resume Count Router Loaded")

@router.get("/resume_count")
def resume_count():

    try:

        print("\n===================================")
        print("RESUME COUNT API CALLED")
        print("===================================")

        print("Checking Total Resumes in Qdrant...")

        count_result = client.count(

            collection_name=collection_name,

            exact=True

        )

        print(f"Total Resumes Found: {count_result.count}")

        print("===================================\n")

        return {

            "total_resumes": count_result.count

        }

    except Exception as e:

        print("\nERROR IN RESUME COUNT API")
        print(str(e))
        print("===================================\n")

        return {

            "error": str(e)

        }