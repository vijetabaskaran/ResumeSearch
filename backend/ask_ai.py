from fastapi import APIRouter
from pydantic import BaseModel

from ai_model import groq_client

router = APIRouter()

print("AI Router Loaded Successfully")

# ==========================================
# REQUEST MODEL
# ==========================================

class AIRequest(BaseModel):

    question: str

print("AIRequest Model Ready")

# ==========================================
# AI CHAT API
# ==========================================

@router.post("/ask_ai")
async def ask_ai(data: AIRequest):

    try:

        print("\n==============================")
        print("AI REQUEST RECEIVED")
        print("==============================")

        print("User Question:")
        print(data.question)

        print("\nSending request to GROQ API...")

        response = groq_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[

                {
                    "role": "system",

                    "content": """

You are an AI recruitment assistant.

You help recruiters:
- analyze resumes
- identify candidate skills
- recommend suitable roles
- answer recruitment questions

Give professional and short responses.

"""
                },

                {
                    "role": "user",

                    "content": data.question
                }

            ]

        )

        print("Response received from GROQ")

        answer = response.choices[0].message.content

        print("\nAI ANSWER:")
        print(answer)

        print("==============================\n")

        return {

            "answer": answer

        }

    except Exception as e:

        print("\nERROR IN AI API")
        print(str(e))
        print("==============================\n")

        return {

            "answer": str(e)

        }