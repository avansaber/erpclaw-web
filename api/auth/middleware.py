"""JWT auth middleware for FastAPI."""

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from auth.jwt_utils import verify_access_token

# Routes that don't require authentication
PUBLIC_ROUTES = {
    "/api/auth/login",
    "/api/auth/setup",
    "/api/auth/check-setup",
    "/api/auth/refresh",
    "/api/health",
    "/api/layout/verticals",
    "/ws",
}

# Docs routes — only public in development
if os.environ.get("ERPCLAW_ENV", "development") != "production":
    PUBLIC_ROUTES.update({"/docs", "/openapi.json", "/redoc"})

# Route prefixes that don't require auth
PUBLIC_PREFIXES = ("/api/layout/",)


class AuthMiddleware(BaseHTTPMiddleware):
    """Verify JWT access token on protected routes."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth for public routes
        if path in PUBLIC_ROUTES or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            response = await call_next(request)
            return response

        # OPTIONS requests pass through (CORS preflight)
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response

        # Extract token from Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid authorization header"},
            )

        token = auth_header[7:]  # Remove "Bearer " prefix
        payload = verify_access_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or expired access token"},
            )

        # Attach user info to request state
        request.state.user = {
            "id": payload["sub"],
            "username": payload["username"],
            "roles": payload.get("roles", []),
        }

        response = await call_next(request)
        return response
