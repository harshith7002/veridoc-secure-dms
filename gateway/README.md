# API Gateway

Single entry point for the frontend. Routes by path prefix (`/api/auth`, `/api/documents`, `/api/search`, `/api/audit`, `/api/cases`) to the corresponding backend service, then forwards the response back.

Deliberately thin: it does **not** re-implement auth. Each backend service independently verifies the JWT it receives (see each service's `auth.py`). That's intentional — a service is still just as protected if something calls it directly, bypassing the gateway (in tests, from another service, from a misconfigured client). The gateway is a routing convenience, not a security boundary that everything else silently depends on.

## Running the whole system

Six processes, in this order (each needs the ones before it to actually do anything useful). `python ../start_backend.py` starts the five backend services in one command if you don't want six terminals — the gateway still needs to come up after them.

```bash
# terminal 1
cd audit-ledger-service && uvicorn main:app --port 8010

# terminal 2 - JWT_SECRET must match across identity/documents/search/cases/gateway
cd identity-service && JWT_SECRET="<pick one, 32+ bytes>" uvicorn main:app --port 8011

# terminal 3
cd documents-service && JWT_SECRET="<same>" AUDIT_LEDGER_URL="http://localhost:8010" uvicorn main:app --port 8012

# terminal 4
cd search-service && JWT_SECRET="<same>" uvicorn main:app --port 8013

# terminal 5
cd cases-service && JWT_SECRET="<same>" uvicorn main:app --port 8014

# terminal 6
cd gateway && IDENTITY_URL="http://localhost:8011" DOCUMENTS_URL="http://localhost:8012" \
  SEARCH_URL="http://localhost:8013" AUDIT_LEDGER_URL="http://localhost:8010" \
  CASES_URL="http://localhost:8014" uvicorn main:app --port 8000
```

Frontend talks only to `http://localhost:8000/api/...`.

## Full-system demo

```bash
python demo_e2e.py
```

Register → login → create a case → upload a document against it (encrypted at rest) → index it → semantic search for it using words that don't appear in the text → check the audit trail recorded the action → verify the audit chain is intact. Every step goes through the gateway, none of it talks to a backend service directly — this is what actually proves the system is wired together, not six services that each work in isolation.
