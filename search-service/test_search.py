import os
os.environ["DATABASE_URL"] = "sqlite:///./test_search.db"
os.environ["EMBEDDING_BACKEND"] = "sentence-transformer"  # the real one - it's actually installed

import pytest
from database import Base, engine, SessionLocal
import models  # noqa: F401
from embeddings import get_embedding_backend, TfidfBackend
from vectorstore import LocalVectorStore
from chunking import chunk_text


@pytest.fixture(scope="module")
def embedder():
    return get_embedding_backend()


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def get_session():
    return SessionLocal()


# --- chunking ------------------------------------------------------------

def test_short_text_is_a_single_chunk():
    chunks = chunk_text("short document text")
    assert chunks == ["short document text"]


def test_long_text_is_split_with_overlap():
    words = [f"word{i}" for i in range(500)]
    text = " ".join(words)
    chunks = chunk_text(text, max_words=200, overlap_words=30)
    assert len(chunks) > 1
    # the overlap region should appear in two consecutive chunks
    first_chunk_words = chunks[0].split()
    second_chunk_words = chunks[1].split()
    assert first_chunk_words[-1] in second_chunk_words


def test_empty_text_yields_no_chunks():
    assert chunk_text("") == []


# --- real Sentence-BERT embeddings -----------------------------------------
# This is the actual semantic-search claim: related concepts should score higher
# than unrelated ones, not just exact word overlap (that's what distinguishes this
# from the TF-IDF fallback below).

def test_sentence_transformer_semantic_similarity(embedder):
    from numpy import dot
    from numpy.linalg import norm

    def cos(a, b):
        return dot(a, b) / (norm(a) * norm(b))

    query = "the vehicle used in the robbery"
    related = "a car was seen near the crime scene"
    unrelated = "the annual budget report for the finance department"

    q_emb, rel_emb, unrel_emb = embedder.embed([query, related, unrelated])
    sim_related = cos(q_emb, rel_emb)
    sim_unrelated = cos(q_emb, unrel_emb)

    assert sim_related > sim_unrelated, (
        f"expected 'vehicle/robbery' to score closer to 'car/crime scene' ({sim_related:.3f}) "
        f"than to an unrelated budget sentence ({sim_unrelated:.3f})"
    )


def test_sentence_transformer_dimension_is_consistent(embedder):
    embs = embedder.embed(["one sentence", "another sentence"])
    assert len(embs[0]) == embedder.dimension
    assert len(embs[1]) == embedder.dimension


# --- TF-IDF fallback (no heavy deps) --------------------------------------

def test_tfidf_backend_produces_fixed_dimension_vectors():
    backend = TfidfBackend(dimension=64)
    embs = backend.embed(["hello world", "goodbye world"])
    assert len(embs[0]) == 64
    assert len(embs[1]) == 64


def test_tfidf_shared_words_score_higher_than_no_overlap():
    import numpy as np
    backend = TfidfBackend(dimension=128)
    query, related, unrelated = backend.embed([
        "stolen vehicle report",
        "vehicle theft case report",
        "quarterly financial statement",
    ])

    def cos(a, b):
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)

    assert cos(query, related) > cos(query, unrelated)


# --- vector store: end-to-end index + search with real embeddings ----------

def test_local_vector_store_finds_semantically_relevant_chunk(embedder):
    db = get_session()
    store = LocalVectorStore()

    store.add(db, document_id="doc-1", case_id="CASE-1", document_type="FIR",
              chunk_text="A white sedan was seen leaving the scene at 10 PM.",
              embedding=embedder.embed(["A white sedan was seen leaving the scene at 10 PM."])[0])
    store.add(db, document_id="doc-2", case_id="CASE-1", document_type="COURT_FILING",
              chunk_text="The quarterly budget review is scheduled for next month.",
              embedding=embedder.embed(["The quarterly budget review is scheduled for next month."])[0])

    query_embedding = embedder.embed(["what vehicle was involved"])[0]
    results = store.search(db, query_embedding, case_id="CASE-1", top_k=2)

    top_chunk, top_score = results[0]
    assert "sedan" in top_chunk.chunk_text
    db.close()


def test_local_vector_store_filters_by_case_id(embedder):
    db = get_session()
    store = LocalVectorStore()
    emb = embedder.embed(["evidence text"])[0]

    store.add(db, document_id="doc-1", case_id="CASE-A", document_type="FIR",
              chunk_text="evidence text for case A", embedding=emb)
    store.add(db, document_id="doc-2", case_id="CASE-B", document_type="FIR",
              chunk_text="evidence text for case B", embedding=emb)

    results = store.search(db, emb, case_id="CASE-A", top_k=10)
    assert len(results) == 1
    assert results[0][0].case_id == "CASE-A"
    db.close()
