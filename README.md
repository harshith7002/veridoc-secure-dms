# Secure Digital Document Management System

Prototype for SIH problem statement 26190 (Ministry of Home Affairs / NCRB / Women Safety Division) — secure document management for FIRs, investigation records, witness statements, charge sheets, and related case documents.

## Architecture

Six independently-runnable services, each owning its own data — genuine microservices, not a monolith with service-shaped folder names:

```
frontend/                 React + Tailwind, talks only to the gateway
gateway/                  routes /api/* by path prefix, no auth logic of its own
identity-service/         register, login, JWT issuance, RBAC, MFA (TOTP)
documents-service/        AES-256-GCM encryption, SHA-256 integrity hash, pluggable storage (local disk / S3-MinIO)
search-service/           OCR-ready ingestion, Sentence-BERT embeddings, semantic search
audit-ledger-service/     hash-chained, tamper-evident action log every other service writes to
cases-service/            case records (status, priority) - source of truth for the case_number every other service keys against; drives the dashboard's stat cards from real data
```

Every document action (upload, download) is logged to the audit ledger over a real HTTP call, and **fails closed**: if the ledger is unreachable, the action is rejected, not silently allowed. This was tested by stopping the ledger and confirming uploads return `503`, not `200`.

## Why this, not a generic DMS

The screening note on this problem statement called it a "generic enterprise application with essentially no novelty." What's actually built to answer that:

1. **A hash-chain audit ledger you can watch break.** Not "we used blockchain" as a slide bullet — `audit-ledger-service/demo_tamper.py` tampers a row directly in the database (bypassing the API, like a real attacker with DB access) and shows `/audit/verify` catch exactly which entry and why.
2. **Real semantic search, proven, not asserted.** `search-service/test_search.py` embeds "the vehicle used in the robbery" and confirms it scores closer to "a car was seen near the crime scene" than to an unrelated sentence — actual Sentence-BERT cosine similarity, not keyword matching.
3. **Encryption that actually detects tampering.** AES-256-GCM, not AES-CBC — a modified ciphertext fails to decrypt (`InvalidTag`) instead of silently returning corrupted data.

## Honesty about what's verified vs. what isn't

Every claim below was actually run, not assumed:

| Component | Status |
|---|---|
| Identity: register/login/JWT/RBAC/MFA | Verified live — full flow including a rejected wrong MFA code and an accepted real one |
| Audit ledger: hash chain + tamper detection | Verified live — tampered a row, caught it at the exact entry |
| Documents: AES-256-GCM encryption | Verified — round-trip, tamper rejection, two encryptions of same plaintext differ |
| Documents: fail-closed audit logging | Verified live — stopped the ledger, confirmed upload returns 503 |
| Documents: S3/MinIO storage backend | Code written correctly against the standard boto3 API, tested against a **mocked** S3 (`moto`) — no live MinIO instance was available in this build environment (no Docker). Point `S3_ENDPOINT_URL` at a real MinIO and re-run the tests before relying on this path. |
| Search: Sentence-BERT semantic embeddings | Verified live with the real model, not mocked |
| Search: pgvector backend | Code written against the standard pgvector/SQLAlchemy API, **not run against a live Postgres+pgvector instance** — same reason (no Docker). Local (SQLite + numpy cosine similarity) is what's actually tested and what runs by default. |
| Search: Tesseract OCR | Code written using standard pytesseract usage, **not run** — no `tesseract` binary was present in this environment. Plain-text ingestion (no OCR needed) is what's tested. |
| Gateway routing | Verified live — full 7-piece system (6 services + frontend) proven end to end through the gateway only |
| Cases: CRUD, status transitions, stats endpoint | Verified — 9 tests including one that asserts dashboard stats match real created/updated data, not hardcoded numbers |
| Frontend | Verified live in a real browser — full user journey including case creation, status updates reflected live on the dashboard, MFA enrollment, and MFA-gated re-login |

Bringing MinIO, a real pgvector-enabled Postgres, and a tesseract binary into the environment and re-running each service's test suite is the concrete next step before a live demo — the code for all three is written and reviewed, just not exercised against real infrastructure here.

## Running the full system

See `gateway/README.md` for the exact multi-terminal startup sequence, and `gateway/demo_e2e.py` for a scripted full-system walkthrough (register → upload → search → audit verify) that exercises everything through the gateway.

## Not yet built

- Case assignment (multiple officers per case) — currently a case has one creator, no assigned-team concept.
- The two features that would make this stand out further in judging, discussed but not implemented: cross-document consistency checking (flagging when a witness statement's date/name doesn't match the FIR) and automated PII redaction before external sharing.
