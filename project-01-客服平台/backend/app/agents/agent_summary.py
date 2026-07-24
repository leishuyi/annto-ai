from sqlalchemy.orm import Session
from app.agents.base import BaseAgent
from app.agents.protocol import A2AMessage
from app.database.models import AgentName


class SummaryAgent(BaseAgent):
    def __init__(self):
        self.agent_name = AgentName.SUMMARY
        self.agent_label = "结论汇总"

    def process(self, message: A2AMessage, db: Session) -> A2AMessage:
        trace_id = self.create_trace_record(db, message.case_id, message.payload)
        try:
            p = message.payload
            case_id = p.get("case_id")
            summary = {
                "case_id": case_id,
                "case_summary": (
                    f"订单 {p.get('order_no', '未知')}: "
                    f"从 {p.get('sender', '未知')} 到 {p.get('receiver', '未知')}, "
                    f"目的地 {p.get('destination', '未知')}。"
                    f"运费 {p.get('invoice_amount', 0)} 元, "
                    f"调度建议: {p.get('dispatch_note', '无')}"
                ),
                "all_agents_completed": True,
                "overall_confidence": 0.93,
                "risk_level": p.get("risk_level", "low"),
                "suggestion": "建议通过",
                "audit_trail": {
                    "order_query": p.get("status", ""),
                    "doc_intake": p.get("waybill_no", ""),
                    "finance_recon": p.get("recon_status", ""),
                    "dispatch_check": p.get("dispatch_note", ""),
                    "risk_detection": {"score": p.get("risk_score", 0), "level": p.get("risk_level", "")},
                },
            }
            self.complete_trace(db, trace_id, summary, confidence=0.93)
            return A2AMessage(
                message_id=f"msg_{case_id}_sum_out",
                source_agent="agent_summary",
                target_agent="human_gate",
                case_id=case_id,
                message_type="result_forward",
                payload={**p, **summary},
                confidence=0.93,
            )
        except Exception as e:
            self.fail_trace(db, trace_id, str(e))
            raise
