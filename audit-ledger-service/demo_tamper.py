"""
Judge-facing demo script: shows the ledger accepting a normal sequence of events,
verifying clean, then an attacker editing a row directly in the database
(bypassing the API entirely, as a real attacker with DB access would), and the
verify endpoint catching exactly which row was touched.

Run: python demo_tamper.py   (make sure the API server is NOT running against
the same audit_ledger.db at the same time, or stop it first, to avoid a lock)
"""
import os
import sqlite3
import requests

BASE_URL = os.environ.get("LEDGER_URL", "http://localhost:8010")


def call(method, path, **kwargs):
    resp = requests.request(method, BASE_URL + path, **kwargs)
    resp.raise_for_status()
    return resp.json()


def main():
    print("1. Logging a normal sequence of actions on a case file...\n")
    call("POST", "/audit/log", json={
        "actor": "officer_raj", "action": "UPLOAD", "document_id": "FIR-2026-0341",
        "case_id": "CASE-8891", "details": "Initial FIR filed"
    })
    call("POST", "/audit/log", json={
        "actor": "officer_raj", "action": "VIEW", "document_id": "FIR-2026-0341",
        "case_id": "CASE-8891"
    })
    entry3 = call("POST", "/audit/log", json={
        "actor": "clerk_meera", "action": "SHARE", "document_id": "FIR-2026-0341",
        "case_id": "CASE-8891", "details": "Shared with district court"
    })
    print(f"   Logged 3 entries. Latest entry_hash: {entry3['entry_hash'][:16]}...\n")

    result = call("GET", "/audit/verify")
    print(f"2. Verifying chain integrity -> valid={result['valid']}, entries_checked={result['entries_checked']}\n")

    print("3. Simulating an attacker with direct DB access editing entry #2's action")
    print("   from VIEW to DELETE_REQUEST, bypassing the API entirely...\n")
    conn = sqlite3.connect("audit_ledger.db")
    conn.execute("UPDATE audit_entries SET action = 'DELETE_REQUEST' WHERE id = 2")
    conn.commit()
    conn.close()

    result = call("GET", "/audit/verify")
    print(f"4. Re-verifying -> valid={result['valid']}")
    if not result["valid"]:
        print(f"   Tampering detected at entry id={result['broken_at_id']}")
        print(f"   Reason: {result['reason']}")


if __name__ == "__main__":
    main()
