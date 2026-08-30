"""
End-to-end walkthrough: register -> login (no MFA yet) -> hit a protected route ->
enroll MFA -> log in again (now MFA-gated) -> reject a wrong code -> accept the real one.
"""
import os
import pyotp
import requests

BASE_URL = os.environ.get("IDENTITY_URL", "http://localhost:8011")


def call(method, path, **kwargs):
    resp = requests.request(method, BASE_URL + path, **kwargs)
    if not resp.ok:
        print(f"   -> {resp.status_code} {resp.json()}")
    resp.raise_for_status()
    return resp.json()


def main():
    print("1. Registering an investigating officer...")
    call("POST", "/auth/register", json={
        "email": "officer.raj@police.gov.in", "password": "S3cure-Pass!23",
        "organization": "Delhi Police", "role": "INVESTIGATING_OFFICER",
    })
    print("   Registered.\n")

    print("2. Logging in (no MFA enrolled yet)...")
    login1 = call("POST", "/auth/login", json={"email": "officer.raj@police.gov.in", "password": "S3cure-Pass!23"})
    assert login1["mfa_required"] is False
    token = login1["access_token"]
    print(f"   Got access token: {token[:24]}...\n")

    print("3. Hitting a protected route (/auth/me) with the token...")
    me = call("GET", "/auth/me", headers={"Authorization": f"Bearer {token}"})
    print(f"   {me}\n")

    print("4. Enrolling MFA...")
    setup = call("POST", "/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"})
    secret = setup["secret"]
    print(f"   Secret issued, provisioning_uri: {setup['provisioning_uri'][:60]}...")
    code = pyotp.TOTP(secret).now()
    confirm = call("POST", "/auth/mfa/confirm", json={"code": code}, headers={"Authorization": f"Bearer {token}"})
    print(f"   {confirm}\n")

    print("5. Logging in again - should now require MFA...")
    login2 = call("POST", "/auth/login", json={"email": "officer.raj@police.gov.in", "password": "S3cure-Pass!23"})
    assert login2["mfa_required"] is True
    pending_token = login2["mfa_pending_token"]
    print("   mfa_required=True, got a short-lived mfa_pending_token.\n")

    print("6. Submitting a WRONG MFA code (should be rejected)...")
    try:
        call("POST", "/auth/login/verify-mfa", json={"mfa_pending_token": pending_token, "code": "000000"})
        print("   UNEXPECTED: wrong code was accepted!")
    except requests.HTTPError:
        print("   Correctly rejected.\n")

    print("7. Submitting the REAL current TOTP code...")
    real_code = pyotp.TOTP(secret).now()
    final = call("POST", "/auth/login/verify-mfa", json={"mfa_pending_token": pending_token, "code": real_code})
    print(f"   Got final access token: {final['access_token'][:24]}...")
    print("\nFull flow verified end to end.")


if __name__ == "__main__":
    main()
