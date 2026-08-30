# Documents Service

Encrypted document storage. Verifies JWTs issued by Identity (no network call back to it - see `auth.py`), encrypts every file with AES-256-GCM before it touches storage, and calls the Audit Ledger service on every action - if that call fails, the action is rejected, not silently allowed.

## What's real here

- **AES-256-GCM encryption at rest** (`crypto.py`) - authenticated encryption, so a tampered ciphertext fails to decrypt (`InvalidTag`) rather than silently returning garbage. Verified: encrypt/decrypt round-trip, tampered-byte rejection, wrong-nonce rejection, and that two encryptions of the same plaintext produce different ciphertext (random nonce per call).
- **SHA-256 integrity hash** recorded at upload time; `/documents/{id}/verify-integrity` decrypts and recomputes it on demand.
- **Fail-closed audit logging** (`audit_client.py`) - proven, not just claimed: with the Audit Ledger service stopped, a real upload attempt against a running Documents service returns `503` and nothing is written to storage.
- **Pluggable storage** (`storage.py`) - `LocalDiskStorage` for zero-setup dev/demo, `S3Storage` (boto3) for MinIO or AWS S3 via `STORAGE_BACKEND=s3` + `S3_ENDPOINT_URL`/`S3_BUCKET`/`S3_ACCESS_KEY`/`S3_SECRET_KEY`.

## Honest limitation

No MinIO or AWS instance was available to test against in the environment this was built in (no Docker). `S3Storage`'s boto3 calls are tested against a mocked S3 API (`moto`), which genuinely exercises the client code (bucket operations, put/get/head) but doesn't prove MinIO matches AWS S3 behavior in every edge case. Point `S3_ENDPOINT_URL` at a running MinIO instance and re-run `test_documents.py` before treating that path as demo-ready — the code should work as-is, but it hasn't been run against a live MinIO server.

## Running it

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Needs Identity and Audit Ledger services running (or at least reachable — the ledger must be up or uploads/downloads will be rejected by design):

```bash
JWT_SECRET="<same secret as identity-service>" AUDIT_LEDGER_URL="http://localhost:8010" uvicorn main:app --port 8012
```

`DOCUMENT_ENCRYPTION_KEY` should be a base64-encoded 32-byte key in any real deployment — the default is an obvious dev placeholder.

## Endpoints

- `POST /documents/upload` — multipart form: `case_id`, `document_type`, `file`. Requires a Bearer JWT.
- `GET /documents?case_id=` — list metadata for a case.
- `GET /documents/{id}/download` — decrypts and streams the original file back.
- `GET /documents/{id}/verify-integrity` — recomputes the SHA-256 from the decrypted content and compares against what was recorded at upload.

## Tests

```bash
python -m pytest test_documents.py -v
```

12 tests: encryption round-trip and tamper rejection, hash correctness against Python's own `hashlib`, both storage backends (local disk with real file I/O, S3 via `moto`).
