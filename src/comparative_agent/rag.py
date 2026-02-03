from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

import numpy as np

from comparative_agent.models import Document


@dataclass
class RetrievalResult:
    score: float
    document: Document


class EmbeddingBackend:
    def embed(self, texts: List[str]) -> np.ndarray:
        raise NotImplementedError


class SentenceTransformerBackend(EmbeddingBackend):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> np.ndarray:
        return np.asarray(self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True))


class TfidfBackend(EmbeddingBackend):
    def __init__(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._vectorizer = TfidfVectorizer(stop_words="english")

    def embed(self, texts: List[str]) -> np.ndarray:
        vectors = self._vectorizer.fit_transform(texts)
        return vectors.toarray()


class Retriever:
    def __init__(self, backend: EmbeddingBackend) -> None:
        self._backend = backend
        self._documents: List[Document] = []
        self._embeddings: np.ndarray | None = None

    def index(self, documents: Iterable[Document]) -> None:
        self._documents = list(documents)
        texts = [doc.text for doc in self._documents]
        if not texts:
            self._embeddings = np.zeros((0, 0))
            return
        self._embeddings = self._backend.embed(texts)

    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        if self._embeddings is None or not self._documents:
            return []
        query_vec = self._backend.embed([query])
        scores = _cosine_similarity(self._embeddings, query_vec[0])
        ranked = sorted(
            (RetrievalResult(score=float(score), document=doc) for score, doc in zip(scores, self._documents)),
            key=lambda item: item.score,
            reverse=True,
        )
        return ranked[:top_k]


def pick_backend(prefer_sentence_transformers: bool = True) -> EmbeddingBackend:
    if prefer_sentence_transformers:
        try:
            return SentenceTransformerBackend()
        except Exception:
            return TfidfBackend()
    return TfidfBackend()


def _cosine_similarity(matrix: np.ndarray, query: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return np.zeros((0,))
    norm_matrix = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
    norm_query = query / (np.linalg.norm(query) + 1e-10)
    return norm_matrix @ norm_query
