import os, uuid
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from app.config import settings
from app.core.response import ApiResponse, BizError
from app.core.auth import AuthMiddleware
from app.schemas.document import DocumentType, DOC_TYPE_LABELS
from app.parser.pipeline import ParsePipeline

pipeline = ParsePipeline()
os.makedirs(settings.upload_dir, exist_ok=True)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(AuthMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff", "tif", "pdf"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


@app.exception_handler(Exception)
async def global_handler(request, exc):
    logger.opt(exception=exc).error("未捕获异常", url=str(request.url))
    return JSONResponse(status_code=200, content=ApiResponse(code=50000, message="服务器内部错误").model_dump())


@app.post("/api/v1/documents/parse")
async def parse_document(file: UploadFile = File(...), doc_type_hint: str = Form(None)):
    if not file.filename:
        raise BizError(400, "文件名为空")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise BizError(400, f"不支持的文件类型 .{ext}，支持: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise BizError(400, f"文件大小 {len(content)} 超过限制 10MB")

    path = os.path.join(settings.upload_dir, f"{uuid.uuid4()}.{ext}")
    try:
        with open(path, "wb") as f:
            f.write(content)
        industry_hint = doc_type_hint or ""
        result = pipeline.parse(path, industry_hint=industry_hint)
        return ApiResponse(data=result.model_dump())
    except Exception as e:
        logger.error("解析失败", error=str(e))
        raise BizError(500, f"解析失败: {str(e)}")
    finally:
        if os.path.exists(path):
            os.remove(path)


@app.get("/api/v1/documents/types")
def list_types():
    return ApiResponse(data=[{"type": dt.value, "label": DOC_TYPE_LABELS[dt]} for dt in DocumentType])


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": settings.app_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
