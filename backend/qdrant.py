from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import os

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

collection_name = os.getenv("QDRANT_COLLECTION_NAME", "resumes2")

print(f"\nCollection Name: {collection_name}")

# ==========================================
# CREATE COLLECTION
# ==========================================

print("\nChecking Collection...")

print("Current Collection:", collection_name)


def _get_vector_size():
    try:
        info = client.get_collection(collection_name)
        vectors = info.config.params.vectors
        if isinstance(vectors, dict):
            return vectors["skills"].size
        return vectors.size
    except Exception as error:
        print(f"Could not detect vector size for {collection_name}: {error}")
        return int(os.getenv("QDRANT_VECTOR_SIZE", "384"))


if not client.collection_exists(collection_name):

    print("Collection Not Found")
    print("Creating New Collection...")
    vector_size = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))

    client.create_collection(

        collection_name=collection_name,

        vectors_config={

            "skills": VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )

        }

    )

    print("Collection Created Successfully")

else:

    print("Collection Already Exists")
    vector_size = _get_vector_size()

# ==========================================
# EMBEDDING MODEL
# ==========================================

class PurePythonEmbeddingVector(list):
    def tolist(self):
        return list(self)

class PurePythonEmbeddingModel:
    def __init__(self, dimension):
        self.dimension = dimension

    def encode(self, text):
        if isinstance(text, list):
            return [PurePythonEmbeddingVector(self._embed(t)) for t in text]
        return PurePythonEmbeddingVector(self._embed(text))

    def _embed(self, text):
        import hashlib
        import math
        words = (str(text) or "").lower().split()
        if not words:
            return [0.0] * self.dimension

        vector = [0.0] * self.dimension
        for word in words:
            h = hashlib.md5(word.encode('utf-8')).hexdigest()
            index = int(h, 16) % self.dimension
            vector[index] += 1.0

        l2_norm = math.sqrt(sum(v * v for v in vector))
        if l2_norm > 0:
            vector = [v / l2_norm for v in vector]
        
        return vector

def _load_embedding_model(dimension):
    if dimension == 768:
        try:
            from sentence_transformers import SentenceTransformer
            print("Loading SentenceTransformer BAAI/bge-base-en-v1.5 for 768-dim collection...")
            return SentenceTransformer("BAAI/bge-base-en-v1.5")
        except Exception as error:
            print(f"SentenceTransformer unavailable, using {dimension}-dim fallback embedding: {error}")

    return PurePythonEmbeddingModel(dimension)


embedding_model = _load_embedding_model(vector_size)
print(f"Embedding Vector Size: {vector_size}")

print("Embedding Model Loaded Successfully")

print("\n===================================")
print("QDRANT SETUP COMPLETED")
print("===================================\n")

