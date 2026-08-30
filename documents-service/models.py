from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, nullable=False, index=True)
    document_type = Column(String, nullable=False)   # FIR, CHARGE_SHEET, WITNESS_STATEMENT, EVIDENCE, FORENSIC_REPORT, COURT_FILING, LEGAL_NOTICE
    filename = Column(String, nullable=False)
    storage_key = Column(String, nullable=False, unique=True)  # where the encrypted blob lives
    sha256_hash = Column(String(64), nullable=False)            # of the ORIGINAL plaintext, for integrity verification
    nonce = Column(String, nullable=False)                       # AES-GCM nonce, base64, needed to decrypt
    uploaded_by = Column(String, nullable=False)                 # email/id from the JWT
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
