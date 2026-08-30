from pydantic import BaseModel, EmailStr
from models import Role


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    organization: str
    role: Role


class UserOut(BaseModel):
    id: int
    email: str
    organization: str
    role: Role
    mfa_enabled: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    mfa_required: bool
    access_token: str | None = None
    mfa_pending_token: str | None = None
    token_type: str = "bearer"


class MfaVerifyLoginRequest(BaseModel):
    mfa_pending_token: str
    code: str


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class MfaConfirmRequest(BaseModel):
    code: str
