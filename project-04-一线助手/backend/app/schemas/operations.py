"""Schemas for operations module"""
from typing import Optional
from pydantic import BaseModel


class ReconRequest(BaseModel):
    period: str = "2026-07"


class ReconResult(BaseModel):
    total_invoices: int
    total_amount: float
    matched_count: int
    unmatched_count: int
    unmatched_items: list[dict] = []


class AnalysisResult(BaseModel):
    discrepancy_reason: str
    confidence: float
    suggested_action: str


class AdjustmentSuggestion(BaseModel):
    action: str  # auto_fix | manual_review
    amount: float = 0
    reason: str


class ScheduleRequest(BaseModel):
    region: str = "华东"
    date: str = "2026-07-25"


class ScheduleResult(BaseModel):
    assignments: list[dict]
    total_drivers: int
    total_orders: int


class AlertItem(BaseModel):
    id: int
    type: str
    level: str  # info | warning | critical
    message: str
    time: str


class AlertList(BaseModel):
    alerts: list[AlertItem]
    total: int


class RootCauseAnalysis(BaseModel):
    alert_id: int
    root_cause: str
    impact: str
    recommendation: str
