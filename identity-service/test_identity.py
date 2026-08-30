import os
os.environ["DATABASE_URL"] = "sqlite:///./test_identity.db"
os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-bytes-long-for-hs256"

import time
import jwt as pyjwt
import pytest

from database import Base, engine, SessionLocal
from models import User, Role
import security
import mfa


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def get_session():
    return SessionLocal()


# --- password hashing -------------------------------------------------

def test_password_hash_roundtrip_on_fresh_session():
    db = get_session()
    user = User(
        email="officer@example.gov", hashed_password=security.hash_password("correct-horse-battery-staple"),
        organization="Delhi Police", role=Role.INVESTIGATING_OFFICER, mfa_enabled=False,
    )
    db.add(user)
    db.commit()
    db.close()

    # fresh session - forces a real read from disk, not an in-memory identity-mapped object
    db2 = get_session()
    fetched = db2.query(User).filter(User.email == "officer@example.gov").first()
    assert security.verify_password("correct-horse-battery-staple", fetched.hashed_password) is True
    assert security.verify_password("wrong-password", fetched.hashed_password) is False
    db2.close()


def test_password_hash_is_not_stored_in_plaintext():
    hashed = security.hash_password("mysecret")
    assert hashed != "mysecret"
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


# --- JWT ---------------------------------------------------------------

def test_access_token_roundtrip_and_claims():
    token = security.create_access_token(user_id=7, email="a@b.com", role="JUDGE", organization="Delhi HC")
    claims = security.decode_token(token)
    assert claims["sub"] == "7"
    assert claims["email"] == "a@b.com"
    assert claims["role"] == "JUDGE"
    assert claims["type"] == "access"


def test_expired_token_is_rejected():
    now = time.time()
    payload = {"sub": "1", "email": "a@b.com", "role": "ADMIN", "org": "x",
               "type": "access", "iat": now - 3600, "exp": now - 1800}
    expired_token = pyjwt.encode(payload, security.JWT_SECRET, algorithm=security.JWT_ALGORITHM)
    with pytest.raises(pyjwt.ExpiredSignatureError):
        security.decode_token(expired_token)


def test_tampered_token_is_rejected():
    token = security.create_access_token(user_id=1, email="a@b.com", role="ADMIN", organization="x")
    tampered = token[:-4] + "abcd"  # corrupt the signature
    with pytest.raises(pyjwt.InvalidTokenError):
        security.decode_token(tampered)


# --- MFA (TOTP) ----------------------------------------------------------

def test_totp_valid_code_verifies():
    secret = mfa.generate_secret()
    import pyotp
    current_code = pyotp.TOTP(secret).now()
    assert mfa.verify_code(secret, current_code) is True


def test_totp_wrong_code_rejected():
    secret = mfa.generate_secret()
    assert mfa.verify_code(secret, "000000") is False


def test_totp_code_from_different_secret_rejected():
    secret_a = mfa.generate_secret()
    secret_b = mfa.generate_secret()
    import pyotp
    code_for_b = pyotp.TOTP(secret_b).now()
    assert mfa.verify_code(secret_a, code_for_b) is False
