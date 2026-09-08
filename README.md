# Study Desk — AI Learning & Study Assistant

Use case 5: an AI agent that creates learning plans, answers questions from
course materials, and generates quizzes. Built with **RAG + Memory + Tools**.

## How the three capabilities map to code

| Capability | Where it lives | What it does |
|---|---|---|
| RAG | `backend/rag_engine.py` | TF-IDF retrieval over `.txt` course material, no internet/model download needed |
| Memory | `backend/memory_store.py` | Per-session chat history + topics the student has asked about |
| Tools | `backend/tools.py` | `generate_quiz()` and `generate_study_plan()`, called by the API based on which endpoint is hit |

`backend/main.py` is the FastAPI app that wires all three together.
`frontend/` is a plain HTML/CSS/JS chat UI — no build step needed.

## Setup

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then paste your Anthropic API key into .env
uvicorn main:app --reload --port 8000
```

Get a key from https://console.anthropic.com/ (free credits available for
students in many cases — check current offers). If you'd rather use OpenAI,
only `backend/llm_client.py` needs to change.

### 2. Frontend
Just open `frontend/index.html` in your browser (double-click it, or use
VS Code's "Live Server" extension). It talks to the backend at
`http://localhost:8000`.

### 3. Try it
- Ask: "What is a binary search tree?" → answered from the sample materials
  in `backend/data/sample_materials/`.
- Upload your own `.txt` notes with the "+ Add a .txt file" button.
- Type a topic and click "Generate quiz".
- Click "Build my study plan" after asking a few questions — it personalizes
  the plan using topics from memory.

## Project folder structure
```
study-assistant/
├── backend/
│   ├── main.py              FastAPI app / API endpoints
│   ├── rag_engine.py        TF-IDF retrieval over course materials
│   ├── memory_store.py      Session memory (chat history + topics)
│   ├── tools.py             Quiz + study-plan generator tools
│   ├── llm_client.py        Anthropic API wrapper
│   ├── requirements.txt
│   ├── .env.example
│   └── data/sample_materials/   Sample .txt notes (DS, DBMS)
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── DAY_BY_DAY_PLAN.md
└── README.md   (this file)
```

## Extending it later
- Swap TF-IDF for `sentence-transformers` + FAISS for semantic (not just
  keyword) retrieval.
- Swap the in-memory dict in `memory_store.py` for SQLite so memory survives
  a server restart.
- Add a `.pdf` upload path (extract text with `pypdf`, then reuse the same
  chunking/indexing code).
