from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from security import decode_token
from models import Role

bearer_scheme = HTTPBearer()


def get_current_claims(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    try:
        claims = decode_token(creds.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if claims.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an access token")
    return claims


def require_role(*allowed_roles: Role):
    """Dependency factory - other services embed this same pattern (with their own copy of
    security.py using the shared JWT_SECRET env var) to enforce which roles can hit which
    endpoints, without needing to call back into this service on every request."""
    allowed = {r.value for r in allowed_roles}

    def _check(claims: dict = Depends(get_current_claims)) -> dict:
        if claims.get("role") not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{claims.get('role')}' is not permitted for this action",
            )
        return claims

    return _check
