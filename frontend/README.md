# Frontend

React + Tailwind CSS. Talks only to the gateway (`VITE_GATEWAY_URL`, defaults to `http://localhost:8000`) — never to a backend service directly.

## What's here

- **Login / Register** (`pages/Login.jsx`, `pages/Register.jsx`) — handles the two-step MFA login flow: password first, then a separate code screen if the account has MFA enabled.
- **MFA setup** (`pages/MfaSetup.jsx`) — shows the TOTP provisioning URI and secret, requires entering a real generated code before MFA actually turns on.
- **Dashboard** (`pages/Dashboard.jsx`) — three tabs per case: Documents (upload, list, download, integrity check), Search (semantic), Audit trail (action history + chain verification).
- **`api.js`** — the only place that talks to the network; every page goes through it.

## Verified working live (not just built)

Ran the actual dev server, drove it through a real browser: registered a user, logged in, uploaded a real file (file selection simulated via the DOM File API since there's no OS-level file-picker automation available in this environment — the upload itself went through the real `fetch` → gateway → Documents service path, nothing mocked), confirmed it appears with its SHA-256 hash, ran integrity verification, ran a semantic search with zero word overlap with the stored text and got the right result back, checked the audit trail, verified chain integrity, enrolled MFA with a real TOTP secret, signed out, and logged back in through the MFA-gated flow using a code computed from that same secret. No console errors at any point.

## Running it

```bash
npm install
npm run dev
```

Needs the gateway (and everything behind it) running — see `../gateway/README.md`.
