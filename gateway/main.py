"""
Thin reverse proxy: single entry point for the frontend, routes by path prefix to the
right backend service. Each service still independently verifies the JWT on every
request (see each service's auth.py) - the gateway does NOT become a trust boundary
that, if bypassed, leaves services unprotected. That's deliberate: services callable
directly (e.g. from another service, or in tests) stay just as secure as requests that
went through the gateway.
"""
import os
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICE_ROUTES = {
    "/api/auth": os.environ.get("IDENTITY_URL", "http://localhost:8011"),
    "/api/documents": os.environ.get("DOCUMENTS_URL", "http://localhost:8012"),
    "/api/search": os.environ.get("SEARCH_URL", "http://localhost:8013"),
    "/api/audit": os.environ.get("AUDIT_LEDGER_URL", "http://localhost:8010"),
    "/api/cases": os.environ.get("CASES_URL", "http://localhost:8014"),
}

_client = httpx.AsyncClient(timeout=30.0)


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway", "routes": list(SERVICE_ROUTES.keys())}


def _resolve_target(path: str) -> tuple[str, str] | None:
    """Returns (upstream_base_url, remaining_path) for the longest matching prefix."""
    for prefix, base_url in sorted(SERVICE_ROUTES.items(), key=lambda kv: -len(kv[0])):
        if path.startswith(prefix):
            # /api/auth/login -> strip "/api/auth", forward "/auth/login" to Identity
            # (each service's own routes are still prefixed with their own domain word)
            service_prefix = prefix.rsplit("/", 1)[-1]  # "auth", "documents", "search", "audit"
            remaining = path[len(prefix):]  # e.g. "/login"
            return base_url, f"/{service_prefix}{remaining}"
    return None


@app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(full_path: str, request: Request):
    target = _resolve_target(f"/api/{full_path}")
    if target is None:
        return Response(content=b'{"detail":"No route for this path"}', status_code=404,
                         media_type="application/json")

    base_url, upstream_path = target
    body = await request.body()

    upstream_request = _client.build_request(
        method=request.method,
        url=base_url + upstream_path,
        params=request.query_params,
        headers={k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")},
        content=body,
    )
    upstream_response = await _client.send(upstream_request)

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        media_type=upstream_response.headers.get("content-type"),
    )
