from fastapi import FastAPI
from app.config import settings
from app.core.response import ApiResponse
from app.reasoning.agentic_reasoning import ReasoningChain
from app.reasoning.nl2sql import NL2SQL
from app.reasoning.simulation import Simulation
from app.schemas.decision import Question

app = FastAPI(title=settings.app_name, version="1.0.0")
reasoning = ReasoningChain()
nl2sql = NL2SQL()
simulation = Simulation()


@app.post("/api/v1/decision/ask")
def ask_question(q: Question):
    return ApiResponse(data=reasoning.ask(q.text))


@app.post("/api/v1/decision/nl2sql")
def query_data(q: Question):
    return ApiResponse(data=nl2sql.query(q.text))


@app.post("/api/v1/decision/simulate")
def simulate(q: Question):
    return ApiResponse(data=simulation.run(q.text))


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
    uvicorn.run(app, host="0.0.0.0", port=8002)
