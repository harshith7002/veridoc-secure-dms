"""
Full-system demo: register -> login -> upload (encrypted) -> index for search ->
semantic search -> audit trail check -> chain integrity check. Every call goes through
the gateway only, exactly how the real frontend would use it - nothing here talks to
a backend service directly.

Requires all five services running:
  audit-ledger-service  :8010
  identity-service      :8011   (JWT_SECRET must match documents/search/gateway don't sign, only verify)
  documents-service     :8012   (JWT_SECRET + AUDIT_LEDGER_URL set)
  search-service        :8013   (JWT_SECRET set)
  gateway                :8000   (IDENTITY_URL/DOCUMENTS_URL/SEARCH_URL/AUDIT_LEDGER_URL set)
"""
import os
import requests

GW = os.environ.get("GATEWAY_URL", "http://localhost:8000")


def call(method, path, **kwargs):
    resp = requests.request(method, GW + path, **kwargs)
    if not resp.ok:
        print(f"   -> {resp.status_code} {resp.text}")
    resp.raise_for_status()
    return resp.json()


def main():
    print("1. Register + login through the gateway...")
    reg = requests.post(GW + "/api/auth/register", json={
        "email": "analyst.priya@ncrb.gov.in", "password": "N3crb-Pass!23",
        "organization": "NCRB", "role": "NCRB_ANALYST",
    })
    if reg.status_code not in (201, 409):  # 409 = already registered from a previous demo run
        reg.raise_for_status()
    token = call("POST", "/api/auth/login", json={
        "email": "analyst.priya@ncrb.gov.in", "password": "N3crb-Pass!23",
    })["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   OK\n")

    print("2. Create a case through the gateway...")
    case_resp = requests.post(GW + "/api/cases", json={
        "case_number": "CASE-8891", "title": "Ring Road hit-and-run", "priority": "HIGH",
    }, headers=headers)
    if case_resp.status_code not in (201, 409):
        case_resp.raise_for_status()
    print("   OK\n")

    print("3. Upload a document against that case through the gateway (encrypted at rest by Documents)...")
    text = "Witness reports a white sedan fled the scene northbound on Ring Road around 10 PM."
    files = {"file": ("witness_statement.txt", text.encode(), "text/plain")}
    data = {"case_id": "CASE-8891", "document_type": "WITNESS_STATEMENT"}
    doc = requests.post(GW + "/api/documents/upload", files=files, data=data, headers=headers).json()
    print(f"   doc_id={doc['id']}\n")

    print("4. Index it for semantic search...")
    idx = call("POST", "/api/search/index", json={
        "document_id": str(doc["id"]), "case_id": "CASE-8891",
        "document_type": "WITNESS_STATEMENT", "text": text,
    }, headers=headers)
    print(f"   {idx}\n")

    print("5. Semantic search for 'what vehicle was involved' (no shared words with the query)...")
    results = call("GET", "/api/search", params={"q": "what vehicle was involved", "case_id": "CASE-8891"},
                    headers=headers)
    top = results["results"][0]
    print(f"   top result (score={top['score']:.3f}): \"{top['chunk_text']}\"")
    assert "sedan" in top["chunk_text"], "expected the sedan chunk to rank first"
    print("   Confirmed: semantic match, not keyword overlap.\n")

    print("6. Audit trail for this case...")
    log = call("GET", "/api/audit/log", params={"case_id": "CASE-8891"})
    for entry in log:
        print(f"   {entry['action']} by {entry['actor']} at {entry['timestamp']}")

    print("\n7. Verifying the audit chain hasn't been tampered with...")
    v = call("GET", "/api/audit/verify")
    print(f"   {v}")
    assert v["valid"] is True

    print("\n8. Dashboard stats for this case (computed from real data, not hardcoded)...")
    stats = call("GET", "/api/cases/stats", headers=headers)
    print(f"   {stats}")
    assert stats["total_cases"] >= 1 and stats["high_priority"] >= 1

    print("\nFull system verified end to end through the gateway.")


if __name__ == "__main__":
    main()
