"""API Key 认证中间件"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

WHITELIST = ["/api/v1/health", "/docs", "/openapi.json", "/redoc"]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if settings.app_env != "production":
            return await call_next(request)
        for prefix in WHITELIST:
            if request.url.path.startswith(prefix):
                return await call_next(request)
        api_key = request.headers.get("X-API-Key", "")
        if api_key != settings.api_key:
            return JSONResponse(status_code=401, content={"code": 30002, "message": "未授权访问"})
        return await call_next(request)
