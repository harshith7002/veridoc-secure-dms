import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models import AuditEntry

GENESIS_HASH = "0" * 64


def _canonical_fields(actor: str, action: str, document_id: str, case_id: str | None,
                       details: str | None, timestamp_str: str) -> dict:
    # Fixed key order + separators so the same logical entry always hashes to the same bytes,
    # regardless of dict ordering or whitespace. timestamp_str is the exact string that gets
    # persisted - never a native datetime object - so there's no DB round-trip to drift from.
    return {
        "actor": actor,
        "action": action,
        "document_id": document_id,
        "case_id": case_id,
        "details": details,
        "timestamp": timestamp_str,
    }


def compute_data_hash(actor: str, action: str, document_id: str, case_id: str | None,
                       details: str | None, timestamp_str: str) -> str:
    payload = _canonical_fields(actor, action, document_id, case_id, details, timestamp_str)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_entry_hash(prev_hash: str, data_hash: str) -> str:
    return hashlib.sha256((prev_hash + data_hash).encode("utf-8")).hexdigest()


def append_entry(db: Session, actor: str, action: str, document_id: str,
                  case_id: str | None = None, details: str | None = None) -> AuditEntry:
    last = db.query(AuditEntry).order_by(AuditEntry.id.desc()).first()
    prev_hash = last.entry_hash if last else GENESIS_HASH

    timestamp_str = datetime.now(timezone.utc).isoformat()
    data_hash = compute_data_hash(actor, action, document_id, case_id, details, timestamp_str)
    entry_hash = compute_entry_hash(prev_hash, data_hash)

    entry = AuditEntry(
        timestamp=timestamp_str,
        actor=actor,
        action=action,
        document_id=document_id,
        case_id=case_id,
        details=details,
        data_hash=data_hash,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def verify_chain(db: Session) -> dict:
    """Walk every entry in id order and re-derive its hash from its stored fields.
    Returns the first point of divergence, if any - either the row's own data_hash/entry_hash
    doesn't match what's stored (row was edited directly), or prev_hash doesn't match the
    previous row's entry_hash (a row was deleted/inserted/reordered)."""
    entries = db.query(AuditEntry).order_by(AuditEntry.id.asc()).all()
    expected_prev = GENESIS_HASH

    for entry in entries:
        recomputed_data_hash = compute_data_hash(
            entry.actor, entry.action, entry.document_id, entry.case_id, entry.details, entry.timestamp
        )
        recomputed_entry_hash = compute_entry_hash(entry.prev_hash, recomputed_data_hash)

        if entry.prev_hash != expected_prev:
            return {
                "valid": False,
                "broken_at_id": entry.id,
                "reason": "prev_hash does not match the previous entry's hash - a row was inserted, deleted, or reordered.",
            }
        if recomputed_data_hash != entry.data_hash:
            return {
                "valid": False,
                "broken_at_id": entry.id,
                "reason": "stored fields do not match the recorded data_hash - this row's content was edited after being written.",
            }
        if recomputed_entry_hash != entry.entry_hash:
            return {
                "valid": False,
                "broken_at_id": entry.id,
                "reason": "entry_hash does not match - the stored hash itself was edited.",
            }
        expected_prev = entry.entry_hash

    return {"valid": True, "entries_checked": len(entries)}
