"""annto A2A 智能客服平台 — 应用入口"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from app.config import settings
from app.core.log import setup_logging
from app.core.auth import AuthMiddleware
from app.core.tracing import RequestIDMiddleware
from app.core.response import ApiResponse, BizError
from app.database.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("应用启动", app_name=settings.app_name, env=settings.app_env)

    # 静态文件目录
    os.makedirs(settings.upload_dir, exist_ok=True)

    # 只创建缺失的表，不修改已有表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表初始化完成")

    yield
    logger.info("应用关闭")


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan,
              docs_url=None if settings.app_env == "production" else "/docs",
              redoc_url=None if settings.app_env == "production" else "/redoc",
              openapi_url=None if settings.app_env == "production" else "/openapi.json")

app.add_middleware(RequestIDMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(CORSMiddleware,
                   allow_origins=settings.cors_origins,
                   allow_credentials=True,
                   allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                   allow_headers=["Content-Type", "Authorization", "X-API-Key"])

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError):
    return JSONResponse(status_code=200, content=ApiResponse(code=exc.code, message=exc.message, data=exc.data).model_dump())


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.opt(exception=exc).error("未捕获异常", url=str(request.url), trace_id=trace_id)
    return JSONResponse(status_code=200, content=ApiResponse(code=50000, message="服务器内部错误", data={"trace_id": trace_id}).model_dump())


from app.routers import cases, agents, human_gate, documents
app.include_router(cases.router, prefix=f"{settings.api_prefix}/cases", tags=["cases"])
app.include_router(agents.router, prefix=f"{settings.api_prefix}/cases", tags=["agents"])
app.include_router(human_gate.router, prefix=f"{settings.api_prefix}/cases", tags=["human_gate"])
app.include_router(documents.router, prefix=f"{settings.api_prefix}/cases", tags=["documents"])


@app.get(f"{settings.api_prefix}/health")
def health():
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}
