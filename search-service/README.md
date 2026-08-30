# Search Service

OCR + semantic search over case documents. Chunks text, embeds it with Sentence-BERT, stores vectors, and does cosine-similarity search - genuinely semantic, not keyword matching, and that's proven by a test, not just asserted.

## What's actually proven

`test_sentence_transformer_semantic_similarity` embeds three sentences with the real `all-MiniLM-L6-v2` model (no mock) and checks that "the vehicle used in the robbery" scores closer to "a car was seen near the crime scene" than to an unrelated budget sentence - i.e. it understands *car* relates to *vehicle* without sharing a word. That's the actual claim behind "semantic search," verified, not assumed.

`test_local_vector_store_finds_semantically_relevant_chunk` goes further: indexes two real chunks into the vector store, searches for "what vehicle was involved," and confirms the sedan chunk - not the unrelated budget chunk - comes back on top.

## Pluggable backends, and what's honestly untested

Same pattern as the other services - pick via env var, default is the one that's actually verified:

| | Default (tested) | Alternative (honest status) |
|---|---|---|
| Embeddings | `sentence-transformer` (`all-MiniLM-L6-v2`, real, tested above) | `tfidf` - zero heavy deps, keyword-overlap only, also tested |
| Vector store | `local` (SQLite + numpy cosine similarity, tested) | `pgvector` - written against the standard pgvector/SQLAlchemy API, **not run against a live Postgres+pgvector instance** in this build (none was available - no Docker in this environment). Should work as written; verify before treating as demo-ready. |
| OCR | `plaintext` (decodes already-text documents, tested) | `tesseract` - standard pytesseract usage, **not run** - no `tesseract` binary was present in this environment. Install `tesseract-ocr` and test against a real scanned document first. |

`local`/`plaintext`/`sentence-transformer` is what actually runs by default with zero extra setup.

## Running it

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
JWT_SECRET="<same as identity-service>" uvicorn main:app --port 8013
```

First startup downloads the `all-MiniLM-L6-v2` model (~80MB) from Hugging Face - needs internet access once, then it's cached locally.

## Endpoints

- `POST /search/index` — `{document_id, case_id, document_type?, text}`. Chunks the text (200 words, 30-word overlap so facts near a chunk boundary aren't lost) and indexes each chunk.
- `GET /search?q=&case_id=&top_k=` — embeds the query, returns the top-k most similar chunks with scores.

Both require a Bearer JWT (same shared secret pattern as the other services).

## Tests

```bash
python -m pytest test_search.py -v
```

9 tests, ~15-45s (loading the embedding model is the slow part; first run also downloads it).
