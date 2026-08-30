import pyotp


def generate_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, email: str, issuer: str = "SecureDocSystem") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def verify_code(secret: str, code: str) -> bool:
    # valid_window=1 allows the previous/next 30s step, to tolerate clock drift between
    # the server and the user's authenticator app - standard practice for TOTP.
    return pyotp.totp.TOTP(secret).verify(code, valid_window=1)
