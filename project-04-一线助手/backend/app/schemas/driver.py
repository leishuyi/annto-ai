"""Schemas for driver module"""
from typing import Optional
from pydantic import BaseModel


class RouteRequest(BaseModel):
    origin: str
    destination: str
    vehicle_type: str = "轻卡"


class RouteResult(BaseModel):
    waypoints: list[dict]
    total_km: float
    estimated_min: int
    traffic_delay_min: int = 0


class SignoffRequest(BaseModel):
    image_data: str = ""
    customer_name: str = ""


class SignoffResult(BaseModel):
    signature_match: bool = True
    seal_present: bool = True
    damage_detected: bool = False
    confidence: float = 0.95


class ScriptRequest(BaseModel):
    customer_query: str
    context: dict = {}


class ScriptResponse(BaseModel):
    suggested_response: str
    sentiment: str = "neutral"  # positive | neutral | negative


class ReportRequest(BaseModel):
    voice_text: str
    location: str = ""
    image_count: int = 0


class ReportResult(BaseModel):
    issue_type: str
    priority: str  # low | medium | high
    description: str
    auto_filled: bool = True
