from sqlalchemy.orm import Session
from app.agents.base import BaseAgent
from app.agents.protocol import A2AMessage
from app.database.models import AgentName


class DispatchCheckAgent(BaseAgent):
    def __init__(self):
        self.agent_name = AgentName.DISPATCH_CHECK
        self.agent_label = "调度校验"

    def process(self, message: A2AMessage, db: Session) -> A2AMessage:
        trace_id = self.create_trace_record(db, message.case_id, message.payload)
        try:
            case_id = message.payload.get("case_id")
            output = {
                "case_id": case_id,
                "warehouse_available": True,
                "vehicle_available": True,
                "route_feasible": True,
                "suggested_vehicle": "轻卡(4.2m)",
                "estimated_delivery_days": 3,
                "dispatch_note": "华东仓库存充足，建议安排7月25日发车",
            }
            self.complete_trace(db, trace_id, output, confidence=0.92)
            return A2AMessage(
                message_id=f"msg_{case_id}_disp_out",
                source_agent="agent_dispatch_check",
                target_agent="agent_risk_detection",
                case_id=case_id,
                message_type="result_forward",
                payload={**message.payload, **output},
                confidence=0.92,
            )
        except Exception as e:
            self.fail_trace(db, trace_id, str(e))
            raise
