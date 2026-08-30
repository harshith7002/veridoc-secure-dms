import os
import sqlite3

os.environ["DATABASE_URL"] = "sqlite:///./test_audit_ledger.db"

import pytest
from database import Base, engine, SessionLocal
import models  # noqa: F401
import ledger


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def get_session():
    return SessionLocal()


def test_first_entry_chains_to_genesis():
    db = get_session()
    entry = ledger.append_entry(db, actor="a", action="UPLOAD", document_id="doc-1")
    assert entry.prev_hash == ledger.GENESIS_HASH
    assert len(entry.entry_hash) == 64
    db.close()


def test_chain_links_sequential_entries():
    db = get_session()
    e1 = ledger.append_entry(db, actor="a", action="UPLOAD", document_id="doc-1")
    e2 = ledger.append_entry(db, actor="b", action="VIEW", document_id="doc-1")
    assert e2.prev_hash == e1.entry_hash
    db.close()


def test_verify_passes_on_untouched_chain():
    db = get_session()
    for i in range(5):
        ledger.append_entry(db, actor="a", action="VIEW", document_id=f"doc-{i}")
    result = ledger.verify_chain(db)
    assert result["valid"] is True
    assert result["entries_checked"] == 5
    db.close()


def test_verify_detects_direct_row_edit():
    db = get_session()
    ledger.append_entry(db, actor="a", action="UPLOAD", document_id="doc-1")
    ledger.append_entry(db, actor="a", action="VIEW", document_id="doc-1")
    ledger.append_entry(db, actor="a", action="SHARE", document_id="doc-1")
    db.close()

    # Bypass the ORM entirely, like an attacker with raw DB access would.
    conn = sqlite3.connect("test_audit_ledger.db")
    conn.execute("UPDATE audit_entries SET action = 'DELETE_REQUEST' WHERE id = 2")
    conn.commit()
    conn.close()

    db = get_session()
    result = ledger.verify_chain(db)
    assert result["valid"] is False
    assert result["broken_at_id"] == 2
    db.close()


def test_verify_detects_deleted_row():
    db = get_session()
    ledger.append_entry(db, actor="a", action="UPLOAD", document_id="doc-1")
    ledger.append_entry(db, actor="a", action="VIEW", document_id="doc-1")
    ledger.append_entry(db, actor="a", action="SHARE", document_id="doc-1")
    db.close()

    conn = sqlite3.connect("test_audit_ledger.db")
    conn.execute("DELETE FROM audit_entries WHERE id = 2")
    conn.commit()
    conn.close()

    db = get_session()
    result = ledger.verify_chain(db)
    assert result["valid"] is False
    # entry 3's prev_hash now points to a hash that no longer precedes it in the sequence
    assert result["broken_at_id"] == 3
    db.close()
