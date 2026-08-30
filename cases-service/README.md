# Cases Service

Source of truth for case records. Every other service already keyed data against a `case_id`/`case_number` string (documents, search chunks, audit entries) — this service is what actually creates and owns that identifier, with a status, priority, and a stats endpoint the dashboard reads from instead of hardcoding zeros.

## Endpoints

- `POST /cases` — `{case_number, title, description?, priority?}`. `case_number` is the same string other services already use (e.g. `"CASE-8891"`); rejects duplicates with 409.
- `GET /cases?status_filter=` — list cases, optionally filtered by status.
- `GET /cases/{case_number}` — one case.
- `PATCH /cases/{case_number}/status` — move it through `OPEN → UNDER_INVESTIGATION → PENDING_REVIEW → CLOSED`.
- `GET /cases/stats` — `{total_cases, active_cases, pending_review, high_priority}`, computed from the actual rows in the database at request time. This is what the dashboard's stat cards call — there's no cached or hardcoded number behind them.

All require a Bearer JWT (same shared-secret pattern as every other service).

## Running it

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
JWT_SECRET="<same as identity-service>" uvicorn main:app --port 8014
```

## Tests

```bash
python -m pytest test_cases.py -v
```

9 tests: CRUD, duplicate rejection, status transitions, an unauthenticated request correctly rejected, and — the one that actually matters for the dashboard claim — `test_stats_reflect_real_data_not_hardcoded`, which creates cases with specific priorities/statuses and asserts the stats endpoint's counts match, plus a separate test confirming an empty database genuinely returns zeros rather than some placeholder.
