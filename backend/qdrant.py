from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from sentence_transformers import SentenceTransformer

print("Loading Qdrant Configuration...")

# ==========================================
# QDRANT CLIENT
# ==========================================

print("\nConnecting to Qdrant Cloud...")

client = QdrantClient(

    url="https://5da3fc0c-a55d-4bde-85ca-fd55b7d4acd6.sa-east-1-0.aws.cloud.qdrant.io",

    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6YTVhYjg1MDMtOGNlNC00M2ZkLWI4YjgtZTg2Njk1ZWM4NjgxIn0.zLY98pLjgc2LZOSQSEGMeHyqjcNQ57PX8VI8PJllkOM"

)

print("Qdrant Connected Successfully")

collection_name = "resumes2"

print(f"\nCollection Name: {collection_name}")

# ==========================================
# CREATE COLLECTION
# ==========================================

print("\nChecking Collection...")

print("Current Collection:", collection_name)


if not client.collection_exists(collection_name):

    print("Collection Not Found")
    print("Creating New Collection...")

    client.create_collection(

        collection_name=collection_name,

        vectors_config={

            "skills": VectorParams(
                size=768,
                distance=Distance.COSINE
            )

        }

    )

    print("Collection Created Successfully")

else:

    print("Collection Already Exists")

# ==========================================
# EMBEDDING MODEL
# ==========================================

print("\nLoading Embedding Model...")

embedding_model = SentenceTransformer(
    "BAAI/bge-base-en-v1.5"
)

print("Embedding Model Loaded Successfully")

print("\n===================================")
print("QDRANT SETUP COMPLETED")
print("===================================\n")

