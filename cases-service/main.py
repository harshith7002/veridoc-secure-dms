from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Case, CaseStatus, CasePriority
from schemas import CaseCreate, CaseOut, CaseUpdateStatus, CaseStats
from auth import get_current_claims

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cases Service", description="Case records - the source of truth for case_number")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "cases"}


@app.post("/cases", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(req: CaseCreate, claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    if db.query(Case).filter(Case.case_number == req.case_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Case number already exists")

    case = Case(
        case_number=req.case_number,
        title=req.title,
        description=req.description,
        priority=req.priority,
        organization=claims["org"],
        created_by=claims["email"],
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@app.get("/cases", response_model=list[CaseOut])
def list_cases(status_filter: CaseStatus | None = None, claims: dict = Depends(get_current_claims),
               db: Session = Depends(get_db)):
    query = db.query(Case)
    if status_filter:
        query = query.filter(Case.status == status_filter)
    return query.order_by(Case.updated_at.desc()).all()


@app.get("/cases/stats", response_model=CaseStats)
def case_stats(claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    all_cases = db.query(Case).all()
    return CaseStats(
        total_cases=len(all_cases),
        active_cases=sum(1 for c in all_cases if c.status in (CaseStatus.OPEN, CaseStatus.UNDER_INVESTIGATION)),
        pending_review=sum(1 for c in all_cases if c.status == CaseStatus.PENDING_REVIEW),
        high_priority=sum(1 for c in all_cases if c.priority == CasePriority.HIGH and c.status != CaseStatus.CLOSED),
    )


@app.get("/cases/{case_number}", response_model=CaseOut)
def get_case(case_number: str, claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_number == case_number).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


@app.patch("/cases/{case_number}/status", response_model=CaseOut)
def update_case_status(case_number: str, req: CaseUpdateStatus, claims: dict = Depends(get_current_claims),
                        db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_number == case_number).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    case.status = req.status
    db.commit()
    db.refresh(case)
    return case
