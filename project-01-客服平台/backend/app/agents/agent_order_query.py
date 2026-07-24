import datetime
from sqlalchemy.orm import Session
from app.agents.base import BaseAgent
from app.agents.protocol import A2AMessage
from app.database.models import AgentName, Case


class OrderQueryAgent(BaseAgent):
    def __init__(self):
        self.agent_name = AgentName.ORDER_QUERY
        self.agent_label = "订单查询"

    def process(self, message: A2AMessage, db: Session) -> A2AMessage:
        trace_id = self.create_trace_record(db, message.case_id, message.payload)
        try:
            case_id = message.payload.get("case_id")
            case = db.query(Case).filter(Case.id == case_id).first()
            output = {
                "case_id": case_id,
                "order_no": case.order_no if case and case.order_no else f"ORD-{case_id:06d}",
                "sender": case.sender if case else "佛山市美的工业园",
                "receiver": case.receiver if case else "上海华联超市",
                "destination": case.destination if case else "上海市浦东新区",
                "status": "运输中",
                "current_location": "佛山分拨中心已发出",
                "estimated_arrival": "2026-07-28 18:00",
            }
            self.complete_trace(db, trace_id, output, confidence=0.96)
            return A2AMessage(
                message_id=f"msg_{case_id}_order_out",
                source_agent="agent_order_query",
                target_agent="agent_doc_intake",
                case_id=case_id,
                message_type="result_forward",
                payload={**message.payload, **output},
                confidence=0.96,
            )
        except Exception as e:
            self.fail_trace(db, trace_id, str(e))
            raise
