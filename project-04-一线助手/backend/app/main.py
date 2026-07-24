from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from app.config import settings
from app.core.response import ApiResponse
from app.core.auth import AuthMiddleware
from app.schemas.driver import RouteRequest, SignoffRequest, ScriptRequest, ReportRequest
from app.schemas.operations import ReconRequest, ScheduleRequest
from app.driver import navigation, signoff, script_assist, report
from app.operations.rpa_agent import RPAFinanceAgent
from app.operations import scheduling, alert_dashboard

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(AuthMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
rpa = RPAFinanceAgent()


@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    logger.opt(exception=exc).error("未捕获异常", url=str(request.url))
    return JSONResponse(status_code=200, content=ApiResponse(code=50000, message="服务器内部错误").model_dump())


@app.post("/api/v1/driver/navigate")
def driver_navigate(req: RouteRequest):
    try:
        return ApiResponse(data=navigation.get_route(req).model_dump())
    except Exception as e:
        return ApiResponse(code=50010, message=f"导航规划失败: {str(e)}")


@app.post("/api/v1/driver/signoff")
def driver_signoff(req: SignoffRequest):
    try:
        return ApiResponse(data=signoff.verify_signoff(req).model_dump())
    except Exception as e:
        return ApiResponse(code=50011, message=f"签收核验失败: {str(e)}")


@app.post("/api/v1/driver/script")
def driver_script(req: ScriptRequest):
    try:
        return ApiResponse(data=script_assist.get_script(req).model_dump())
    except Exception as e:
        return ApiResponse(code=50012, message=f"话术生成失败: {str(e)}")


@app.post("/api/v1/driver/report")
def driver_report(req: ReportRequest):
    try:
        return ApiResponse(data=report.submit_report(req).model_dump())
    except Exception as e:
        return ApiResponse(code=50013, message=f"上报失败: {str(e)}")


@app.post("/api/v1/ops/reconcile")
def ops_reconcile(req: ReconRequest):
    try:
        return ApiResponse(data=rpa.reconcile(req.period).model_dump())
    except Exception as e:
        return ApiResponse(code=50020, message=f"对账失败: {str(e)}")


@app.post("/api/v1/ops/reconcile/analyze")
def ops_analyze(req: ReconRequest):
    try:
        result = rpa.reconcile(req.period)
        return ApiResponse(data=rpa.analyze(result.unmatched_items).model_dump())
    except Exception as e:
        return ApiResponse(code=50021, message=f"差异分析失败: {str(e)}")


@app.post("/api/v1/ops/schedule")
def ops_schedule(req: ScheduleRequest):
    try:
        return ApiResponse(data=scheduling.generate_schedule(req).model_dump())
    except Exception as e:
        return ApiResponse(code=50022, message=f"排班失败: {str(e)}")


@app.get("/api/v1/ops/alerts")
def ops_alerts():
    try:
        return ApiResponse(data=alert_dashboard.get_alerts().model_dump())
    except Exception as e:
        return ApiResponse(code=50023, message=f"预警获取失败: {str(e)}")


@app.post("/api/v1/ops/alerts/{alert_id}/root-cause")
def ops_root_cause(alert_id: int):
    try:
        return ApiResponse(data=alert_dashboard.analyze_root_cause(alert_id).model_dump())
    except Exception as e:
        return ApiResponse(code=50024, message=f"根因分析失败: {str(e)}")


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": settings.app_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
