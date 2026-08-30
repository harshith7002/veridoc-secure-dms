from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models  # noqa: F401 - registers the table with Base before create_all
import ledger
from schemas import AuditEntryCreate, AuditEntryOut, VerifyResult

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Audit Ledger Service", description="Hash-chained, tamper-evident audit log")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "audit-ledger"}


@app.post("/audit/log", response_model=AuditEntryOut)
def log_action(entry: AuditEntryCreate, db: Session = Depends(get_db)):
    return ledger.append_entry(
        db,
        actor=entry.actor,
        action=entry.action,
        document_id=entry.document_id,
        case_id=entry.case_id,
        details=entry.details,
    )


@app.get("/audit/log", response_model=list[AuditEntryOut])
def list_log(document_id: str | None = None, case_id: str | None = None,
             limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(models.AuditEntry)
    if document_id:
        query = query.filter(models.AuditEntry.document_id == document_id)
    if case_id:
        query = query.filter(models.AuditEntry.case_id == case_id)
    return query.order_by(models.AuditEntry.id.asc()).limit(limit).all()


@app.get("/audit/verify", response_model=VerifyResult)
def verify(db: Session = Depends(get_db)):
    return ledger.verify_chain(db)
