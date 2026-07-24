import os, uuid
from fastapi import FastAPI, UploadFile, File, Form
from app.config import settings
from app.core.response import ApiResponse, BizError
from app.schemas.document import DocumentType, DOC_TYPE_LABELS
from app.parser.pipeline import ParsePipeline

pipeline = ParsePipeline()
os.makedirs(settings.upload_dir, exist_ok=True)

app = FastAPI(title=settings.app_name, version="1.0.0")

@app.post("/api/v1/documents/parse")
async def parse_document(file: UploadFile = File(...), doc_type_hint: str = Form(None)):
    ext = file.filename.split(".")[-1] if file.filename else "jpg"
    path = os.path.join(settings.upload_dir, f"{uuid.uuid4()}.{ext}")
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    result = pipeline.parse(path)
    os.remove(path)
    return ApiResponse(data=result.model_dump())

@app.get("/api/v1/documents/types")
def list_types():
    return ApiResponse(data=[{"type": dt.value, "label": DOC_TYPE_LABELS[dt]} for dt in DocumentType])

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": settings.app_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
