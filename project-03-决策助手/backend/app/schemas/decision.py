from typing import Optional
from pydantic import BaseModel
class Question(BaseModel):
    text: str
    type: str = "reasoning"
class ReasoningResult(BaseModel):
    question: str; region: str; data: dict; recommendation: str; reasoning_steps: list[str]
class NLQueryResult(BaseModel):
    intent: str; sql: str; results: list; chart_type: str
class SimulationResult(BaseModel):
    scenario: str; impact: str; confidence: float
