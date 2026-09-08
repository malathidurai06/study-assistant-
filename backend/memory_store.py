"""
memory_store.py
-----------------
A simple in-memory conversation + learner-profile store, keyed by session_id.

This is intentionally simple (a Python dict, not a database) so it's easy to
explain in a demo: "Memory" here means two things, matching the brief's
"RAG + Memory + Tools":

1. Conversation memory: the running chat history for a session, so follow-up
   questions like "explain that more simply" work.
2. Learner memory: topics the student has asked about / struggled with, used
   to personalize the study plan tool.

For a real deployment you'd swap this dict for SQLite or Redis, keeping the
same interface (get_session / add_message / note_topic).
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SessionMemory:
    history: List[dict] = field(default_factory=list)  # [{"role": "user"/"assistant", "content": str}]
    topics_asked: List[str] = field(default_factory=list)


class MemoryStore:
    def __init__(self):
        self._sessions: Dict[str, SessionMemory] = {}

    def get_session(self, session_id: str) -> SessionMemory:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory()
        return self._sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        session = self.get_session(session_id)
        session.history.append({"role": role, "content": content})
        # Keep only the last 20 turns so prompts don't grow unbounded
        session.history = session.history[-20:]

    def note_topic(self, session_id: str, topic: str):
        session = self.get_session(session_id)
        if topic and topic not in session.topics_asked:
            session.topics_asked.append(topic)

    def get_history(self, session_id: str) -> List[dict]:
        return self.get_session(session_id).history

    def get_topics(self, session_id: str) -> List[str]:
        return self.get_session(session_id).topics_asked
