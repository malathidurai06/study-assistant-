"""
main.py
--------
FastAPI backend for the AI Learning & Study Assistant.

Endpoints:
  POST /chat          -> Multi-mode RAG-grounded Q&A, with conversation memory
  POST /upload        -> Upload a .txt course material file
  POST /quiz          -> Generate an interactive quiz on a topic (Tool)
  POST /study-plan    -> Generate a personalized study roadmap (Tool)
  POST /flashcards    -> Generate active recall flashcards (Tool)
  GET  /materials     -> List uploaded material filenames
  GET  /topics/{sid}  -> Topics a session has asked about (learner memory)
  POST /clear/{sid}   -> Reset session memory

Run with:
  uvicorn main:app --reload --port 8000
"""

import os
import re
import shutil
from typing import Optional

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, UploadFile, File, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from rag_engine import RAGEngine
from memory_store import MemoryStore
from llm_client import call_llm
import tools

MATERIALS_DIR = os.path.join(os.path.dirname(__file__), "data", "sample_materials")
os.makedirs(MATERIALS_DIR, exist_ok=True)
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

app = FastAPI(title="AI Learning & Study Assistant Pro", version="2.0")

# Allow the frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = RAGEngine(MATERIALS_DIR)
memory = MemoryStore()

# Serve Frontend on Root URL
if os.path.exists(FRONTEND_DIR):
    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/style.css")
    def serve_css():
        return FileResponse(os.path.join(FRONTEND_DIR, "style.css"), media_type="text/css")

    @app.get("/script.js")
    def serve_js():
        return FileResponse(os.path.join(FRONTEND_DIR, "script.js"), media_type="application/javascript")



class ChatRequest(BaseModel):
    session_id: str
    message: str
    mode: Optional[str] = "general"  # "general", "concept", "code", "step_by_step", "flashcards"


class QuizRequest(BaseModel):
    session_id: str
    topic: str
    num_questions: int = 5


class StudyPlanRequest(BaseModel):
    session_id: str
    days: int = 5
    extra_topics: list[str] = []


class FlashcardsRequest(BaseModel):
    session_id: str
    topic: str
    count: int = 5


def _extract_topic(message: str) -> str:
    """Extract a concise topic keyword out of a question for memory tracking."""
    cleaned = re.sub(r"[^a-zA-Z0-9 ]", "", message).strip()
    words = [w for w in cleaned.split() if w.lower() not in {"what", "is", "how", "to", "explain", "the", "a", "an", "why", "in", "and", "or", "for", "please", "can", "you", "tell", "me", "about", "give", "solution"}]
    return " ".join(words[:4]) if words else cleaned[:30]


def _build_system_prompt(mode: str, context: str) -> str:
    base_instructions = (
        "You are an elite, encouraging AI Professor & Senior Technical Mentor. "
        "Your goal is to provide the most lucid, accurate, visually structured, and effective answers possible.\n\n"
        "Formatting Guidelines:\n"
        "- Format with rich GitHub Markdown (use `## Headers`, bullet points, bold key terms, tables where helpful).\n"
        "- If code is involved, ALWAYS specify the language in fenced code blocks (e.g. ```python, ```sql, ```cpp).\n"
        "- Include Time and Space Complexity ($O(1)$, $O(N)$) for algorithmic questions.\n"
        "- Use callout notes like `> 💡 **Key Insight:**` or `> ⚠️ **Common Mistake:**` to highlight crucial nuances.\n"
        "- If the course material context contains the answer, ground your response in it and reference it naturally.\n"
        "- If the context is missing or partial, seamlessly synthesize full solutions using state-of-the-art general knowledge.\n"
    )

    mode_instructions = {
        "concept": (
            "\nSpecial Mode: 💡 CONCEPT EXPLAINER\n"
            "- Start with an intuitive 1-sentence definition followed by a memorable real-world analogy.\n"
            "- Break down how it works under the hood with bullet points.\n"
            "- Add a comparison table or pros/cons if applicable.\n"
        ),
        "code": (
            "\nSpecial Mode: 💻 CODE & IMPLEMENTATION\n"
            "- Provide clean, production-grade, well-commented code.\n"
            "- Explain the step-by-step logic.\n"
            "- Clearly state Time Complexity and Space Complexity.\n"
            "- Mention edge cases and how the solution handles them.\n"
        ),
        "step_by_step": (
            "\nSpecial Mode: 🔢 STEP-BY-STEP SOLVER\n"
            "- Deconstruct the problem into clear, numbered logical steps.\n"
            "- Show all intermediate calculations or state transitions.\n"
            "- Conclude with a final boxed or bolded verification.\n"
        ),
        "flashcards": (
            "\nSpecial Mode: ⚡ FLASHCARD & REVISION SUMMARY\n"
            "- Provide high-yield summaries, key formulas, core terms, and fast recall bullets.\n"
        ),
    }

    prompt = base_instructions + mode_instructions.get(mode, "")
    if context:
        prompt += f"\n\n--- COURSE MATERIAL CONTEXT ---\n{context}\n---------------------------------\n"

    return prompt


def _format_error(e: Exception) -> str:
    err_str = str(e)
    if "503" in err_str or "UNAVAILABLE" in err_str:
        return "The AI model is experiencing a temporary spike in traffic. Please retry in a few seconds."
    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
        return "API rate limit reached. Please wait a few seconds and try again."
    return f"{err_str}. Please check your API key in backend/.env"


@app.post("/chat")
def chat(req: ChatRequest):
    chunks = rag.retrieve(req.message, top_k=4)
    context = "\n---\n".join(f"[{c.source}] {c.text}" for c in chunks)

    history = memory.get_history(req.session_id)
    system_prompt = _build_system_prompt(req.mode or "general", context)

    messages = history + [{"role": "user", "content": req.message}]
    try:
        answer = call_llm(system_prompt, messages, max_tokens=1500)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM Error: {_format_error(e)}"
        )

    memory.add_message(req.session_id, "user", req.message)
    memory.add_message(req.session_id, "assistant", answer)
    extracted_topic = _extract_topic(req.message)
    if extracted_topic:
        memory.note_topic(req.session_id, extracted_topic)

    return {
        "answer": answer,
        "sources_used": sorted({c.source for c in chunks}),
        "mode": req.mode or "general",
    }


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        return {"error": "Only .txt files are supported in this version."}
    dest = os.path.join(MATERIALS_DIR, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    rag.reload()
    return {"status": "uploaded", "filename": file.filename, "materials": rag.all_sources()}


@app.get("/materials")
def materials():
    return {"materials": rag.all_sources()}


@app.post("/quiz")
def quiz(req: QuizRequest):
    chunks = rag.retrieve(req.topic, top_k=6)
    context = "\n---\n".join(c.text for c in chunks) if chunks else ""
    try:
        quiz_text = tools.generate_quiz(req.topic, context, req.num_questions)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Quiz Generation Error: {_format_error(e)}"
        )
    memory.note_topic(req.session_id, req.topic)
    return {"quiz": quiz_text}


@app.post("/study-plan")
def study_plan(req: StudyPlanRequest):
    topics = memory.get_topics(req.session_id) + req.extra_topics
    try:
        plan_text = tools.generate_study_plan(topics, req.days)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Study Plan Error: {_format_error(e)}"
        )
    return {"plan": plan_text, "topics_used": topics}


@app.post("/flashcards")
def flashcards(req: FlashcardsRequest):
    chunks = rag.retrieve(req.topic, top_k=6)
    context = "\n---\n".join(c.text for c in chunks) if chunks else ""
    try:
        cards_text = tools.generate_flashcards(req.topic, context, req.count)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Flashcard Error: {_format_error(e)}"
        )
    memory.note_topic(req.session_id, req.topic)
    return {"flashcards": cards_text}


@app.get("/topics/{session_id}")
def topics(session_id: str):
    return {"topics": memory.get_topics(session_id)}


@app.post("/clear/{session_id}")
def clear_session(session_id: str):
    if session_id in memory._history:
        memory._history[session_id] = []
    if session_id in memory._topics:
        memory._topics[session_id] = []
    return {"status": "cleared", "session_id": session_id}
