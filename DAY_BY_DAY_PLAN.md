# 5-Day Build Plan — AI Learning & Study Assistant

## Day 1 — Use case selection + setup
- Finalize use case 5 (done).
- Set up the project folder (this scaffold).
- Get an Anthropic API key, confirm `uvicorn main:app --reload` runs and
  `/materials` returns the two sample files.
- Understand `rag_engine.py`: read it end to end, run it in a Python shell
  on a sample question to see what chunks come back.

## Day 2 — RAG
- Replace the sample materials with your actual course notes (or keep both).
- Test retrieval quality: ask 5–10 questions, check the `sources_used` in
  the response actually match the right file.
- If retrieval feels weak, tune `chunk_size`/`overlap` in `rag_engine.py`,
  or increase `top_k`.

## Day 3 — Memory
- Verify conversation memory: ask a question, then a follow-up like
  "explain that more simply" — confirm the assistant remembers context.
- Verify topic memory: check `GET /topics/{session_id}` accumulates topics
  as you ask questions.
- Optional stretch: persist memory to a `sessions.json` file or SQLite so
  it survives a server restart.

## Day 4 — Tools
- Test `/quiz` with a few topics — check questions are grounded in your
  actual materials, not hallucinated.
- Test `/study-plan` after asking several questions — confirm it picks up
  topics from memory automatically.
- Polish the frontend: materials list, topics list, and tool buttons should
  all update live.

## Day 5 — Polish + demo prep
- Write 3–4 sample questions you'll ask live during the demo (pick ones you
  know retrieve well).
- Prepare a 1-minute explanation of the architecture using the table in
  README.md ("this box is RAG, this box is memory, this box is tools").
- Test the whole flow once from a clean browser tab, start to finish.
- Take a couple of screenshots of the UI for your slides/report.
