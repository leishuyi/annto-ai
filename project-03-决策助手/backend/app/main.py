from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from app.config import settings
from app.core.response import ApiResponse
from app.core.auth import AuthMiddleware
from app.reasoning.agentic_reasoning import ReasoningChain
from app.reasoning.nl2sql import NL2SQL
from app.reasoning.simulation import Simulation
from app.schemas.decision import Question

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(AuthMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

reasoning = ReasoningChain()
nl2sql = NL2SQL()
simulation = Simulation()


@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    logger.opt(exception=exc).error("未捕获异常", url=str(request.url))
    return JSONResponse(status_code=200, content=ApiResponse(code=50000, message="服务器内部错误").model_dump())


@app.post("/api/v1/decision/ask")
def ask_question(q: Question):
    try:
        return ApiResponse(data=reasoning.ask(q.text))
    except Exception as e:
        logger.error("决策推理失败", error=str(e))
        return ApiResponse(code=50001, message=f"推理失败: {str(e)}")


@app.post("/api/v1/decision/nl2sql")
def query_data(q: Question):
    try:
        return ApiResponse(data=nl2sql.query(q.text))
    except Exception as e:
        return ApiResponse(code=50002, message=f"查询失败: {str(e)}")


@app.post("/api/v1/decision/simulate")
def simulate(q: Question):
    try:
        return ApiResponse(data=simulation.run(q.text))
    except Exception as e:
        return ApiResponse(code=50003, message=f"仿真失败: {str(e)}")


@app.get("/api/v1/decision/agents")
def list_agents():
    return ApiResponse(data=[
        {"name": "stock", "label": "库存查询"},
        {"name": "order", "label": "在途查询"},
        {"name": "forecast", "label": "销量预测"},
    ])


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": settings.app_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
