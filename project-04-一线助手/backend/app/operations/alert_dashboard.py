"""Alert dashboard (mock)"""
from app.schemas.operations import AlertItem, AlertList, RootCauseAnalysis
from app.core.llm import llm


def get_alerts() -> AlertList:
    return AlertList(
        alerts=[
            AlertItem(id=1, type="delivery_delay", level="warning", message="浦东区订单延迟率上升至12%", time="2026-07-24 14:30"),
            AlertItem(id=2, type="inventory", level="critical", message="SKU-AC-001华东库存低于安全水位", time="2026-07-24 13:15"),
            AlertItem(id=3, type="damage", level="info", message="本周破损率0.3%处于正常范围", time="2026-07-24 10:00"),
        ],
        total=3,
    )


def analyze_root_cause(alert_id: int) -> RootCauseAnalysis:
    reasons = {
        1: "浦东区因修路导致部分路段封闭，配送车辆需绕行，平均增加30分钟配送时间",
        2: "上周销量超出预期30%，且佛山工厂一批次发货延迟2天",
        3: "无异常",
    }
    impacts = {
        1: "预计影响约200单/天的配送时效，客户投诉率可能上升5%",
        2: "当前库存仅够3天，如不补货将影响约1200台订单",
        3: "影响有限",
    }
    return RootCauseAnalysis(
        alert_id=alert_id,
        root_cause=reasons.get(alert_id, "未知原因"),
        impact=impacts.get(alert_id, "待评估"),
        recommendation="已通知相关人员处理，预计24小时内解决",
    )
