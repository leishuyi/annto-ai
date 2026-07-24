"""Agent 编排器 — 支持串行/并行混合调度 + 事件驱动。

编排策略：
- 串行: A(订单) → B(单据) → (C(财务) ‖ D(调度)) → E(风控) → F(汇总)
- 并行段通过 feature_agent_parallel 控制
"""
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.config import settings
from app.agents.protocol import A2AMessage
from app.agents.agent_order_query import OrderQueryAgent
from app.agents.agent_doc_intake import DocIntakeAgent
from app.agents.agent_finance_recon import FinanceReconAgent
from app.agents.agent_dispatch_check import DispatchCheckAgent
from app.agents.agent_risk_detection import RiskDetectionAgent
from app.agents.agent_summary import SummaryAgent
from app.database.models import Case, CaseStatus, AuditLog
from app.events import event_bus


class AgentOrchestrator:
    """Agent 编排器 — 串行/并行混合调度 + 事件驱动。"""

    # 串行段（基础依赖）
    SERIAL_HEAD = [
        ("agent_order_query", "订单查询"),
        ("agent_doc_intake", "单据录入"),
    ]

    # 并行段（互不依赖）
    PARALLEL_GROUP = [
        ("agent_finance_recon", "财务对账"),
        ("agent_dispatch_check", "调度校验"),
    ]

    # 串行段（依赖前面全部结果）
    SERIAL_TAIL = [
        ("agent_risk_detection", "风控检测"),
        ("agent_summary", "结论汇总"),
    ]

    def __init__(self):
        self.agents = {
            "agent_order_query": OrderQueryAgent(),
            "agent_doc_intake": DocIntakeAgent(),
            "agent_finance_recon": FinanceReconAgent(),
            "agent_dispatch_check": DispatchCheckAgent(),
            "agent_risk_detection": RiskDetectionAgent(),
            "agent_summary": SummaryAgent(),
        }

    def run_chain(self, case_id: int, db: Session) -> Optional[str]:
        """执行 Agent 链路，返回错误信息（None=成功）。"""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return "工单不存在"

        case.status = CaseStatus.PROCESSING
        db.commit()
        logger.info("开始执行 Agent 链路", case_id=case_id, case_no=case.case_no)

        payload: dict = {"case_id": case_id}

        # Phase 1: 串行段 A → B
        error = self._run_serial(self.SERIAL_HEAD, payload, case_id, db)
        if error:
            return self._fail(case, db, error)

        # Phase 2: 并行段 C ‖ D
        if settings.feature_agent_parallel:
            error = self._run_parallel(self.PARALLEL_GROUP, payload, case_id, db)
        else:
            error = self._run_serial(self.PARALLEL_GROUP, payload, case_id, db)
        if error:
            return self._fail(case, db, error)

        # Phase 3: 串行段 E → F
        error = self._run_serial(self.SERIAL_TAIL, payload, case_id, db)
        if error:
            return self._fail(case, db, error)

        # 完成
        return self._finish(case, payload, db)

    def _run_serial(self, chain: list, payload: dict, case_id: int, db: Session) -> Optional[str]:
        """串行执行 Agent 列表。"""
        for agent_key, agent_label in chain:
            agent = self.agents[agent_key]
            msg = A2AMessage(
                message_id=f"msg_{case_id}_{agent_key}",
                source_agent=agent_key, target_agent="",
                case_id=case_id, message_type="request", payload=payload,
            )
            try:
                result = agent.process(msg, db)
                payload.update(result.payload)
                event_bus.publish("agent.completed", {
                    "case_id": case_id, "agent": agent_key,
                    "label": agent_label, "confidence": result.confidence,
                })
            except Exception as e:
                return f"{agent_label} 执行失败: {str(e)}"
        return None

    def _run_parallel(self, group: list, payload: dict, case_id: int, db: Session) -> Optional[str]:
        """并行执行一组 Agent。"""
        logger.info("并行执行 Agent", agents=[a for a, _ in group])
        with ThreadPoolExecutor(max_workers=len(group)) as executor:
            future_map = {}
            for agent_key, agent_label in group:
                agent = self.agents[agent_key]
                msg = A2AMessage(
                    message_id=f"msg_{case_id}_{agent_key}_parallel",
                    source_agent=agent_key, target_agent="",
                    case_id=case_id, message_type="request", payload=dict(payload),
                )
                future = executor.submit(agent.process, msg, db)
                future_map[future] = (agent_key, agent_label)

            for future in as_completed(future_map):
                agent_key, agent_label = future_map[future]
                try:
                    result = future.result()
                    payload.update(result.payload)
                    event_bus.publish("agent.completed", {
                        "case_id": case_id, "agent": agent_key,
                        "label": agent_label, "confidence": result.confidence,
                    })
                except Exception as e:
                    return f"{agent_label} 并行执行失败: {str(e)}"
        return None

    def _fail(self, case: Case, db: Session, error: str) -> str:
        case.status = CaseStatus.DRAFT
        db.commit()
        logger.error("Agent 链路失败", case_id=case.id, error=error)
        return error

    def _finish(self, case: Case, payload: dict, db: Session) -> None:
        case.status = CaseStatus.PENDING_REVIEW
        case.calculated_amount = payload.get("calculated_amount")
        case.risk_level = payload.get("risk_level", case.risk_level)

        log = AuditLog(case_id=case.id, action="agents_completed",
                       comment="全链路 Agent 处理完成，等待人工审核", operator="system")
        db.add(log)
        db.commit()

        logger.info("Agent 链路执行完成", case_id=case.id, status=str(case.status.value),
                    amount=case.calculated_amount, risk=str(case.risk_level.value))

        event_bus.publish("case.pending_review", {
            "case_id": case.id, "case_no": case.case_no,
            "risk_level": case.risk_level.value,
            "calculated_amount": case.calculated_amount,
        })
        return None
