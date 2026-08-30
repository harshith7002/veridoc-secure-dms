# Identity Service

Auth, JWT issuance, RBAC, and MFA for the document management system. Every other service trusts the JWT this issues rather than re-implementing login — they just need `JWT_SECRET` and can verify tokens locally without calling back here.

## Auth flow

- `POST /auth/register` — email, password, organization, role (`ADMIN`, `INVESTIGATING_OFFICER`, `COURT_CLERK`, `JUDGE`, `NCRB_ANALYST`)
- `POST /auth/login` — if the user hasn't enrolled MFA, returns an access token directly. If they have, returns `mfa_required: true` and a short-lived (5 min) `mfa_pending_token` instead — no access token is issued until the TOTP code is verified.
- `POST /auth/login/verify-mfa` — exchange the `mfa_pending_token` + a 6-digit TOTP code for the real access token.
- `POST /auth/mfa/setup` (authenticated) — issues a TOTP secret + `otpauth://` provisioning URI (scan with Google Authenticator / Authy). MFA is **not** enabled yet at this point.
- `POST /auth/mfa/confirm` (authenticated) — submit a code generated from that secret; only on success does `mfa_enabled` flip to true. This proves the user actually has the authenticator set up before it becomes mandatory on login.
- `GET /auth/me` — current user from the JWT.

## RBAC

`deps.require_role(*roles)` is a FastAPI dependency factory — protect any route with `Depends(require_role(Role.ADMIN))`. Other services (Documents, Search) copy this same pattern with their own `security.py` reading the shared `JWT_SECRET` env var, so they can verify tokens and enforce roles without a network call back to this service on every request. See `/auth/admin-only-example` for the pattern.

## Passwords & tokens

- Passwords hashed with bcrypt (`bcrypt.hashpw`, not passlib — passlib's bcrypt backend has known compatibility issues with recent bcrypt releases).
- JWTs signed HS256 with a shared secret (set `JWT_SECRET` — the default in code is a dev-only placeholder that says so explicitly). A shared-secret setup is a reasonable hackathon-scope simplification; a production deployment across truly independent services would use RS256 with a public/private keypair so services can verify without holding the signing secret at all — noted here rather than silently pretended away.
- Access tokens expire in 30 minutes; the MFA-pending token in 5.

## Running it

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --port 8011
```

`DATABASE_URL` defaults to a local SQLite file; point it at Postgres for anything beyond a demo. Docs at `http://localhost:8011/docs` (adjust if you run it on a different port).

## Tests

```bash
python -m pytest test_identity.py -v
```

8 tests: password hashing (including a fresh-session round-trip, not just an in-memory check), JWT issuance/expiry/tamper-rejection, and TOTP verification (correct code, wrong code, code generated from a *different* secret rejected).

## Demo

```bash
# terminal 1
uvicorn main:app --port 8011
# terminal 2
python demo_flow.py
```

Registers a user, logs in without MFA, hits a protected route, enrolls MFA, logs in again (now MFA-gated), shows a wrong code rejected and the real code accepted. Every step actually calls the running server — this isn't a mocked walkthrough.
