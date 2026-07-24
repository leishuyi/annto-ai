"""请求 ID 追踪中间件 — 每个请求生成唯一 trace_id，串联日志与响应。"""
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """为每个请求注入 X-Request-ID，日志上下文携带 trace_id。"""

    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        request.state.trace_id = trace_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = trace_id
        return response
