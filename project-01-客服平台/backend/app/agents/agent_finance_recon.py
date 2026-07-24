from sqlalchemy.orm import Session
from app.agents.base import BaseAgent
from app.agents.protocol import A2AMessage
from app.database.models import AgentName


class FinanceReconAgent(BaseAgent):
    def __init__(self):
        self.agent_name = AgentName.FINANCE_RECON
        self.agent_label = "财务对账"

    def process(self, message: A2AMessage, db: Session) -> A2AMessage:
        trace_id = self.create_trace_record(db, message.case_id, message.payload)
        try:
            case_id = message.payload.get("case_id")
            output = {
                "case_id": case_id,
                "invoice_amount": 12500.00,
                "actual_charge": 12200.00,
                "difference": -300.00,
                "recon_status": "部分差异",
                "recon_detail": "保险费未体现在发票中，差额300元",
            }
            self.complete_trace(db, trace_id, output, confidence=0.90)
            return A2AMessage(
                message_id=f"msg_{case_id}_fin_out",
                source_agent="agent_finance_recon",
                target_agent="agent_dispatch_check",
                case_id=case_id,
                message_type="result_forward",
                payload={**message.payload, **output},
                confidence=0.90,
            )
        except Exception as e:
            self.fail_trace(db, trace_id, str(e))
            raise
