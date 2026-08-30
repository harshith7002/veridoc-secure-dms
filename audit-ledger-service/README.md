# Audit Ledger Service

Hash-chained, tamper-evident audit log for the document management system. Every action on a document (upload, view, share, delete-request) is appended as a record that cryptographically links to the one before it, so editing or removing any past record breaks the chain in a way `/audit/verify` can detect and pinpoint.

## Why a hash chain, not a "real" blockchain

A multi-node consensus network (Hyperledger Fabric, a private Ethereum chain) solves a problem this system doesn't have: multiple mutually-distrusting parties who all need to agree on history without a central authority. Here there's one organization operating the ledger — the actual risk is an insider or attacker with direct database access silently editing history, and a hash chain with an independent verification endpoint solves exactly that, in a fraction of the setup time and with far fewer moving parts to fail during a demo.

## How it works

Each entry stores `data_hash` (SHA-256 of that entry's own fields) and `entry_hash` (SHA-256 of `prev_hash + data_hash`), chaining it to the entry before it. `/audit/verify` walks every entry in order and recomputes both hashes from the stored fields — if anyone edits a row directly in the database (bypassing the API), the recomputed hash won't match the stored one, and verification reports exactly which entry and why.

The timestamp that goes into the hash is stored as the literal ISO-8601 string, not a native database datetime column — SQLite (and some other drivers) silently reformat/drop timezone info on a native datetime column when it round-trips through a fresh session, which would make every legitimate entry falsely appear tampered. This was an actual bug caught while building this, not a hypothetical.

## Running it

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --port 8010
```

API docs at `http://localhost:8010/docs` (adjust if you run it on a different port). Set `DATABASE_URL` to point at Postgres in production (e.g. `postgresql://...`); defaults to a local SQLite file with no setup needed for dev/demo.

## Endpoints

- `POST /audit/log` — append an action `{actor, action, document_id, case_id?, details?}`
- `GET /audit/log?document_id=&case_id=` — list entries, optionally filtered
- `GET /audit/verify` — walk the whole chain, returns `{valid, entries_checked}` or `{valid: false, broken_at_id, reason}`

## Tests

```bash
python -m pytest test_ledger.py -v
```

5 tests: chain linking, clean verification, and two tamper-detection cases (direct row edit, direct row deletion) — both simulate an attacker bypassing the API entirely via raw SQL, then confirm `/audit/verify`-equivalent logic catches it at the exact right entry.

## Judge demo

```bash
# terminal 1
uvicorn main:app --port 8010
# terminal 2
python demo_tamper.py
```

Logs 3 real actions on a case file, verifies clean, then directly edits row #2 in the SQLite file via raw SQL (exactly what an attacker with database access would do — not through the API), and re-verifies to show the exact entry that was tampered and why. This is the live moment worth building the pitch around: most competing "blockchain DMS" submissions will claim tamper-evidence, few will show it breaking on stage.
