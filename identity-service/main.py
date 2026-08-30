from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import jwt

from database import Base, engine, get_db
import models
from models import User, Role
import security
import mfa
from schemas import (
    RegisterRequest, UserOut, LoginRequest, LoginResponse,
    MfaVerifyLoginRequest, MfaSetupResponse, MfaConfirmRequest,
)
from deps import get_current_claims, require_role

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Identity Service", description="Auth, JWT issuance, RBAC, MFA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "identity"}


@app.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=req.email,
        hashed_password=security.hash_password(req.password),
        organization=req.organization,
        role=req.role,
        mfa_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not security.verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if user.mfa_enabled:
        return LoginResponse(mfa_required=True, mfa_pending_token=security.create_mfa_pending_token(user.id))

    token = security.create_access_token(user.id, user.email, user.role.value, user.organization)
    return LoginResponse(mfa_required=False, access_token=token)


@app.post("/auth/login/verify-mfa", response_model=LoginResponse)
def verify_mfa_login(req: MfaVerifyLoginRequest, db: Session = Depends(get_db)):
    try:
        claims = security.decode_token(req.mfa_pending_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA challenge expired, log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA challenge")

    if claims.get("type") != "mfa_pending":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA challenge")

    user = db.query(User).filter(User.id == int(claims["sub"])).first()
    if not user or not user.mfa_enabled or not mfa.verify_code(user.mfa_secret, req.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")

    token = security.create_access_token(user.id, user.email, user.role.value, user.organization)
    return LoginResponse(mfa_required=False, access_token=token)


@app.get("/auth/me", response_model=UserOut)
def me(claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(claims["sub"])).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.post("/auth/mfa/setup", response_model=MfaSetupResponse)
def mfa_setup(claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(claims["sub"])).first()
    secret = mfa.generate_secret()
    user.mfa_secret = secret          # not yet enabled - stays off until /auth/mfa/confirm succeeds
    db.commit()
    return MfaSetupResponse(secret=secret, provisioning_uri=mfa.provisioning_uri(secret, user.email))


@app.post("/auth/mfa/confirm")
def mfa_confirm(req: MfaConfirmRequest, claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(claims["sub"])).first()
    if not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Call /auth/mfa/setup first")
    if not mfa.verify_code(user.mfa_secret, req.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid code")

    user.mfa_enabled = True
    db.commit()
    return {"mfa_enabled": True}


@app.get("/auth/admin-only-example")
def admin_only_example(claims: dict = Depends(require_role(Role.ADMIN))):
    return {"message": f"Hello admin {claims['email']}"}
