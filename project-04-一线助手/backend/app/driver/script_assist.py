"""Script assistant (mock)"""
from app.schemas.driver import ScriptRequest, ScriptResponse
from app.core.llm import llm


def get_script(req: ScriptRequest) -> ScriptResponse:
    response = llm.chat([{"role": "user", "content": req.customer_query}])
    sentiment = "negative" if any(k in req.customer_query for k in ["投诉", "差评", "破损"]) else "neutral"
    return ScriptResponse(suggested_response=response, sentiment=sentiment)
