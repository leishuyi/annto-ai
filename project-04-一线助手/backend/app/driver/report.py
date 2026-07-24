"""Anomaly report (mock)"""
from app.schemas.driver import ReportRequest, ReportResult


def submit_report(req: ReportRequest) -> ReportResult:
    text = req.voice_text.lower()
    if "破损" in text or "损坏" in text:
        return ReportResult(issue_type="goods_damage", priority="high", description=req.voice_text)
    if "迟到" in text or "延迟" in text:
        return ReportResult(issue_type="delivery_delay", priority="medium", description=req.voice_text)
    if "地址" in text or "送错" in text:
        return ReportResult(issue_type="wrong_address", priority="high", description=req.voice_text)
    return ReportResult(issue_type="other", priority="low", description=req.voice_text)
