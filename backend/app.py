from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq_client import groq_client
from insert_resume import router as insert_router
from search_resume import router as search_router
from resume_count import router as count_router
from analyze_resume import router as analyze_router
from ask_ai import router as ai_router

app = FastAPI()

# ==========================================
# CORS
# ==========================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)

# ==========================================
# INCLUDE ROUTERS
# ==========================================

app.include_router(insert_router)
app.include_router(search_router)
app.include_router(count_router)
app.include_router(analyze_router)
app.include_router(ai_router)
# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {

        "message": "Resume AI API Running"

    }
