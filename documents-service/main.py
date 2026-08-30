import base64
import uuid

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from cryptography.exceptions import InvalidTag

from database import Base, engine, get_db
from models import Document
import crypto
import storage
from auth import get_current_claims
from audit_client import log_action, AuditLogUnavailable
from schemas import DocumentOut, IntegrityCheckResult

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Documents Service", description="Encrypted document storage with audit-logged actions")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_storage = storage.get_storage()


@app.get("/health")
def health():
    return {"status": "ok", "service": "documents"}


@app.post("/documents/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db),
):
    plaintext = await file.read()
    sha256_hash = crypto.sha256_hex(plaintext)
    nonce, ciphertext = crypto.encrypt(plaintext)

    storage_key = str(uuid.uuid4())

    # Fail closed: log the action before committing the metadata row, so we never end up
    # with a document that exists but was never audited.
    try:
        log_action(actor=claims["email"], action="UPLOAD", document_id=storage_key,
                   case_id=case_id, details=f"filename={file.filename}")
    except AuditLogUnavailable as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                             detail=f"Upload rejected: audit ledger unavailable ({e})")

    _storage.put(storage_key, ciphertext)

    doc = Document(
        case_id=case_id,
        document_type=document_type,
        filename=file.filename,
        storage_key=storage_key,
        sha256_hash=sha256_hash,
        nonce=base64.b64encode(nonce).decode(),
        uploaded_by=claims["email"],
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@app.get("/documents", response_model=list[DocumentOut])
def list_documents(case_id: str | None = None, db: Session = Depends(get_db),
                    claims: dict = Depends(get_current_claims)):
    query = db.query(Document)
    if case_id:
        query = query.filter(Document.case_id == case_id)
    return query.order_by(Document.id.asc()).all()


@app.get("/documents/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_claims)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        log_action(actor=claims["email"], action="DOWNLOAD", document_id=doc.storage_key, case_id=doc.case_id)
    except AuditLogUnavailable as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                             detail=f"Download rejected: audit ledger unavailable ({e})")

    ciphertext = _storage.get(doc.storage_key)
    nonce = base64.b64decode(doc.nonce)
    try:
        plaintext = crypto.decrypt(nonce, ciphertext)
    except InvalidTag:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                             detail="Stored file failed integrity check on decrypt - possible tampering")

    return Response(content=plaintext, media_type="application/octet-stream",
                     headers={"Content-Disposition": f'attachment; filename="{doc.filename}"'})


@app.get("/documents/{doc_id}/verify-integrity", response_model=IntegrityCheckResult)
def verify_integrity(doc_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_claims)):
    """Decrypts and recomputes the SHA-256 of the plaintext, compares it against the hash
    recorded at upload time. This is the document-level integrity check; the audit-ledger
    service separately verifies that the ACTION HISTORY on this document hasn't been tampered."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    ciphertext = _storage.get(doc.storage_key)
    nonce = base64.b64decode(doc.nonce)
    try:
        plaintext = crypto.decrypt(nonce, ciphertext)
        recomputed = crypto.sha256_hex(plaintext)
        intact = recomputed == doc.sha256_hash
    except InvalidTag:
        recomputed = "DECRYPTION_FAILED"
        intact = False

    return IntegrityCheckResult(id=doc.id, intact=intact, stored_hash=doc.sha256_hash, recomputed_hash=recomputed)
