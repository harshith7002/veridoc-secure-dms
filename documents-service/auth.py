"""
JWT verification only - this service never issues tokens, Identity does. Same shared
JWT_SECRET pattern documented in identity-service/README.md: each service carries its own
copy of this file rather than importing across service boundaries.
"""
import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-secret-change-in-production")
JWT_ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()


def get_current_claims(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    try:
        claims = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if claims.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an access token")
    return claims
