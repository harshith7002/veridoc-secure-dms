# Secure Digital Document Management System

Secure document management for legal and investigation case files — FIRs, investigation records, witness statements, charge sheets — built for SIH problem statement 26190 (Ministry of Home Affairs / NCRB, Women Safety Division).

## Architecture

The system is organized as six independently runnable services, each owning its own data, plus a React frontend that talks to a single gateway:

```
frontend/                 React + Tailwind, talks only to the gateway
gateway/                  routes /api/* by path prefix, no auth logic of its own
identity-service/         register, login, JWT issuance, RBAC, MFA (TOTP)
documents-service/        AES-256-GCM encryption, SHA-256 integrity hash, pluggable storage (local disk / S3-MinIO)
search-service/           Sentence-BERT embeddings, semantic search
audit-ledger-service/     hash-chained, tamper-evident action log
cases-service/            case records (status, priority), source of truth for case numbers; backs the dashboard's stats
```

Every document action (upload, download) is logged to the audit ledger over HTTP, and the write fails closed: if the ledger is unreachable, the action is rejected rather than allowed to proceed silently.

## Security design

Legal and investigation records need a verifiable history and confidentiality at rest, so those two properties drive the design rather than sitting on top of it:

- **Hash-chained audit ledger.** Each entry stores a hash of its own fields plus the hash of the entry before it. `/audit/verify` walks the chain and recomputes both hashes; editing or deleting any past row breaks the chain at that point, reported with the exact entry and reason. A single-writer hash chain was chosen over a distributed-consensus ledger because the trust model here is one organization operating the ledger, not multiple mutually distrusting parties.
- **AES-256-GCM for documents at rest.** GCM is authenticated encryption: a modified ciphertext fails to decrypt (`InvalidTag`) instead of silently returning corrupted data, so tampering with stored files is detectable, not just prevented.
- **RBAC + MFA on identity.** Roles (investigating officer, court clerk, judge, NCRB analyst, admin) are embedded in the JWT and enforced per route. MFA is TOTP-based and only activates once the user proves they can generate a valid code from the enrolled secret.

## What's verified and what isn't

| Component | Status |
|---|---|
| Identity: register/login/JWT/RBAC/MFA | Verified live — full flow, including a rejected wrong MFA code and an accepted correct one |
| Audit ledger: hash chain + tamper detection | Verified live — a row was edited directly in the database, `/audit/verify` caught it at the exact entry |
| Documents: AES-256-GCM encryption | Verified with tests — round-trip, tamper rejection, two encryptions of the same plaintext produce different ciphertext |
| Documents: fail-closed audit logging | Verified live — with the ledger stopped, an upload attempt returns 503 |
| Documents: S3/MinIO storage backend | Not tested against a live MinIO instance; the boto3 client code was tested against a mocked S3 API (`moto`), which exercises the request logic but doesn't confirm MinIO-specific behavior |
| Search: Sentence-BERT semantic embeddings | Verified with the real model — "the vehicle used in the robbery" scores closer to "a car was seen near the crime scene" than to an unrelated sentence |
| Search: pgvector backend | Written against the standard pgvector/SQLAlchemy API, not run against a live Postgres instance; the default backend (SQLite + cosine similarity in Python) is what's tested and runs out of the box |
| Search: Tesseract OCR | Written using standard pytesseract calls, not run — no tesseract binary was available to test against. Plain-text ingestion is the tested path |
| Cases: CRUD, status transitions, stats | Verified with tests, including one that creates cases with specific priorities/statuses and asserts the stats endpoint's counts match |
| Gateway routing | Verified live — full register → upload → search → audit flow through the gateway only |
| Frontend | Verified live in a browser — case creation, document upload/download, semantic search, audit trail, MFA enrollment and MFA-gated login |

MinIO, a pgvector-enabled Postgres, and a tesseract install are the concrete next steps before those three paths can be called demo-ready; the code for each is written but unexercised against real infrastructure.

## Running it

See `gateway/README.md` for the startup sequence and `gateway/demo_e2e.py` for a scripted walkthrough (register → create case → upload → index → search → audit verify) that exercises the whole system through the gateway.

## Not yet built

- Case assignment (multiple officers per case) — a case currently has one creator, no team concept.
- Cross-document consistency checking (flagging a witness statement whose date or name doesn't match the FIR) and automated PII redaction before external sharing — both scoped, neither implemented.
