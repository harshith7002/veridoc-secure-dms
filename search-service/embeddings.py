import os
from abc import ABC, abstractmethod


class EmbeddingBackend(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...


class SentenceTransformerBackend(EmbeddingBackend):
    """Real semantic embeddings via Sentence-BERT. Loads the model once and reuses it -
    loading is the slow part (seconds), encoding individual batches is fast after that."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)
        self._dim = self._model.get_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, convert_to_numpy=True).tolist()

    @property
    def dimension(self) -> int:
        return self._dim


class TfidfBackend(EmbeddingBackend):
    """Zero-heavy-dependency fallback: TF-IDF vectors instead of learned semantic embeddings.
    Genuinely functional keyword-weighted search, not a stub - but it matches word overlap,
    it doesn't understand that 'vehicle' and 'car' are related the way Sentence-BERT does.
    Use this when SentenceTransformerBackend can't be installed/loaded (e.g. no internet
    access to pull the model, or disk/memory constrained deployment)."""

    def __init__(self, dimension: int = 256):
        from sklearn.feature_extraction.text import HashingVectorizer
        self._dim = dimension
        self._vectorizer = HashingVectorizer(n_features=dimension, alternate_sign=False, norm="l2")

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._vectorizer.transform(texts).toarray().tolist()

    @property
    def dimension(self) -> int:
        return self._dim


def get_embedding_backend() -> EmbeddingBackend:
    backend = os.environ.get("EMBEDDING_BACKEND", "sentence-transformer")
    if backend == "tfidf":
        return TfidfBackend()
    return SentenceTransformerBackend(os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
