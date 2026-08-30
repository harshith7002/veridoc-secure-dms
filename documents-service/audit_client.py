"""
Client for the audit-ledger-service. This system's compliance story depends on every
document action being logged, so a failure to log is treated as a failure to act:
if the ledger is unreachable or rejects the write, the caller raises rather than
silently proceeding - fail closed, not fail open, for anything touching legal evidence.
"""
import os
import requests

AUDIT_LEDGER_URL = os.environ.get("AUDIT_LEDGER_URL", "http://localhost:8010")
AUDIT_TIMEOUT_SECONDS = 3


class AuditLogUnavailable(Exception):
    pass


def log_action(actor: str, action: str, document_id: str, case_id: str | None = None,
               details: str | None = None) -> None:
    try:
        resp = requests.post(
            f"{AUDIT_LEDGER_URL}/audit/log",
            json={"actor": actor, "action": action, "document_id": document_id,
                  "case_id": case_id, "details": details},
            timeout=AUDIT_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise AuditLogUnavailable(f"Could not write to audit ledger: {e}") from e
