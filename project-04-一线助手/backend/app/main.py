from fastapi import FastAPI
from app.config import settings
from app.core.response import ApiResponse
from app.schemas.driver import RouteRequest, SignoffRequest, ScriptRequest, ReportRequest
from app.schemas.operations import ReconRequest, ScheduleRequest
from app.driver import navigation, signoff, script_assist, report
from app.operations.rpa_agent import RPAFinanceAgent
from app.operations import scheduling, alert_dashboard

app = FastAPI(title=settings.app_name, version="1.0.0")
rpa = RPAFinanceAgent()


@app.post("/api/v1/driver/navigate")
def driver_navigate(req: RouteRequest):
    return ApiResponse(data=navigation.get_route(req).model_dump())


@app.post("/api/v1/driver/signoff")
def driver_signoff(req: SignoffRequest):
    return ApiResponse(data=signoff.verify_signoff(req).model_dump())


@app.post("/api/v1/driver/script")
def driver_script(req: ScriptRequest):
    return ApiResponse(data=script_assist.get_script(req).model_dump())


@app.post("/api/v1/driver/report")
def driver_report(req: ReportRequest):
    return ApiResponse(data=report.submit_report(req).model_dump())


@app.post("/api/v1/ops/reconcile")
def ops_reconcile(req: ReconRequest):
    return ApiResponse(data=rpa.reconcile(req.period).model_dump())


@app.post("/api/v1/ops/reconcile/analyze")
def ops_analyze(req: ReconRequest):
    result = rpa.reconcile(req.period)
    return ApiResponse(data=rpa.analyze(result.unmatched_items).model_dump())


@app.post("/api/v1/ops/schedule")
def ops_schedule(req: ScheduleRequest):
    return ApiResponse(data=scheduling.generate_schedule(req).model_dump())


@app.get("/api/v1/ops/alerts")
def ops_alerts():
    return ApiResponse(data=alert_dashboard.get_alerts().model_dump())


@app.post("/api/v1/ops/alerts/{alert_id}/root-cause")
def ops_root_cause(alert_id: int):
    return ApiResponse(data=alert_dashboard.analyze_root_cause(alert_id).model_dump())


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": settings.app_name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
