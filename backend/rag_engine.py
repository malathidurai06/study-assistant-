"""
rag_engine.py
--------------
A lightweight RAG (Retrieval-Augmented Generation) engine.

Why TF-IDF instead of a neural embedding model?
- No internet download of a model is required (works fully offline).
- It's fast, explainable in a viva/demo, and good enough for course-material
  sized document sets (tens to low hundreds of chunks).
- You can swap this for sentence-transformers + FAISS later if you want to
  extend the project after the 5 days.

How it works:
1. Course material files (.txt) are split into overlapping chunks.
2. All chunks are vectorized with TF-IDF.
3. A user question is vectorized the same way, and we return the top-k
   chunks by cosine similarity.
"""

import os
import glob
from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Chunk:
    text: str
    source: str  # filename this chunk came from


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        start += chunk_size - overlap
    return chunks


class RAGEngine:
    def __init__(self, materials_dir: str):
        self.materials_dir = materials_dir
        self.chunks: List[Chunk] = []
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = None
        self.reload()

    def reload(self):
        """Re-scan the materials directory and rebuild the TF-IDF index.
        Call this after a new file is uploaded."""
        self.chunks = []
        for path in glob.glob(os.path.join(self.materials_dir, "*.txt")):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                raw = f.read()
            filename = os.path.basename(path)
            for c in _chunk_text(raw):
                if c.strip():
                    self.chunks.append(Chunk(text=c, source=filename))

        if self.chunks:
            corpus = [c.text for c in self.chunks]
            self.matrix = self.vectorizer.fit_transform(corpus)
        else:
            self.matrix = None

    def retrieve(self, query: str, top_k: int = 4) -> List[Chunk]:
        """Return the top_k most relevant chunks for a query."""
        if not self.chunks or self.matrix is None:
            return []
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.matrix).flatten()
        top_idx = sims.argsort()[::-1][:top_k]
        # Filter out zero-similarity matches (irrelevant / no overlap)
        return [self.chunks[i] for i in top_idx if sims[i] > 0]

    def all_sources(self) -> List[str]:
        return sorted({c.source for c in self.chunks})
