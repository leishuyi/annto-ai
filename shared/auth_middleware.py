"""共享认证中间件 — 所有 annto 项目统一使用。"""
import os
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API Key 认证中间件。可从环境变量读取密钥，支持健康检查/文档路径白名单。"""

    def __init__(self, app, api_key: str = None, whitelist: list[str] = None):
        super().__init__(app)
        self.api_key = api_key or os.getenv("ANNTO_API_KEY", "")
        self.whitelist = whitelist or ["/api/v1/health", "/docs", "/openapi.json", "/redoc"]

    async def dispatch(self, request: Request, call_next):
        if not self.api_key:
            return await call_next(request)
        for prefix in self.whitelist:
            if request.url.path.startswith(prefix):
                return await call_next(request)
        key = request.headers.get("X-API-Key", "")
        if key != self.api_key:
            raise HTTPException(status_code=401, detail="无效或缺失 API Key")
        return await call_next(request)
