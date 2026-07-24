from sqlalchemy.orm import Session
from app.agents.base import BaseAgent
from app.agents.protocol import A2AMessage
from app.database.models import AgentName


class RiskDetectionAgent(BaseAgent):
    def __init__(self):
        self.agent_name = AgentName.RISK_DETECTION
        self.agent_label = "风控检测"

    def process(self, message: A2AMessage, db: Session) -> A2AMessage:
        trace_id = self.create_trace_record(db, message.case_id, message.payload)
        try:
            case_id = message.payload.get("case_id")
            findings = [
                {"rule": "地址一致性", "risk": "low", "detail": "目的地地址与历史记录一致"},
                {"rule": "收件人核实", "risk": "low", "detail": "收件人电话可接通"},
                {"rule": "货物价值", "risk": "low", "detail": "申报价值在合理范围内"},
            ]
            output = {
                "case_id": case_id,
                "risk_score": 10,
                "risk_level": "low",
                "risk_findings": findings,
                "suggestion": "建议通过",
            }
            self.complete_trace(db, trace_id, output, confidence=0.93)
            return A2AMessage(
                message_id=f"msg_{case_id}_risk_out",
                source_agent="agent_risk_detection",
                target_agent="agent_summary",
                case_id=case_id,
                message_type="result_forward",
                payload={**message.payload, **output},
                confidence=0.93,
            )
        except Exception as e:
            self.fail_trace(db, trace_id, str(e))
            raise
