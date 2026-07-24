from sqlalchemy.orm import Session
from app.agents.base import BaseAgent
from app.agents.protocol import A2AMessage
from app.database.models import AgentName


class DocIntakeAgent(BaseAgent):
    def __init__(self):
        self.agent_name = AgentName.DOC_INTAKE
        self.agent_label = "单据录入"

    def process(self, message: A2AMessage, db: Session) -> A2AMessage:
        trace_id = self.create_trace_record(db, message.case_id, message.payload)
        try:
            case_id = message.payload.get("case_id")
            output = {
                "case_id": case_id,
                "waybill_no": f"YD{case_id:010d}",
                "documents_parsed": [
                    {"type": "运单", "status": "已识别", "confidence": 0.98},
                    {"type": "回单", "status": "已识别", "confidence": 0.95},
                ],
                "goods_desc": "家电一批（空调+冰箱）",
                "total_weight_kg": 1250,
                "total_pieces": 50,
            }
            self.complete_trace(db, trace_id, output, confidence=0.95)
            return A2AMessage(
                message_id=f"msg_{case_id}_doc_out",
                source_agent="agent_doc_intake",
                target_agent="agent_finance_recon",
                case_id=case_id,
                message_type="result_forward",
                payload={**message.payload, **output},
                confidence=0.95,
            )
        except Exception as e:
            self.fail_trace(db, trace_id, str(e))
            raise
