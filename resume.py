from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader

# API:
# GET /collections
# POST /insert
# POST /search
# POST /edit

client = QdrantClient(
    url="https://5da3fc0c-a55d-4bde-85ca-fd55b7d4acd6.sa-east-1-0.aws.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6YTVhYjg1MDMtOGNlNC00M2ZkLWI4YjgtZTg2Njk1ZWM4NjgxIn0.zLY98pLjgc2LZOSQSEGMeHyqjcNQ57PX8VI8PJllkOM"
)



model = SentenceTransformer("all-MiniLM-L6-v2")



collection_name = "resumes"

if not client.collection_exists(collection_name):

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )

    print("Collection created!")

else:
    print("Collection already exists!")



def extract_text_from_pdf(pdf_path):

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:

        extracted = page.extract_text()

        if extracted:
            text += extracted + " "

    return text



resume_files = [
    "resume1.pdf",
    "resume2.pdf"
]



points = []

for idx, file in enumerate(resume_files):

    # Extract resume text
    resume_text = extract_text_from_pdf(file)

    print(f"\nExtracted Text From {file}:\n")
    print(resume_text[:300])

    # Convert text to vector
    vector = model.encode(resume_text).tolist()

    # Create point
    point = PointStruct(
        id=idx + 1, # uuid
        vector=vector,
        payload={
            "file_name": file,
            "resume_text": resume_text
        }
    )

    points.append(point)

client.upsert(
    collection_name=collection_name,
    points=points
)

print("\nAll resumes stored successfully!")



job_description = """
Looking for a Python developer with FastAPI,
Machine Learning, SQL and API development skills
"""

# Convert JD to vector
job_vector = model.encode(job_description).tolist()



response = client.query_points(
    collection_name=collection_name,
    query=job_vector,
    limit=3
)

results = response.points



print("\nTOP MATCHING RESUMES:\n")

for result in results:

    print("File:", result.payload["file_name"])

    print("Similarity Score:", round(result.score, 4))

    print("-" * 50)