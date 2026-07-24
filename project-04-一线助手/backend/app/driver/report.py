"""Anomaly report — 异常上报，含否定词检测避免误报。"""
from app.schemas.driver import ReportRequest, ReportResult

# 否定词列表，匹配这些词时不触发对应分类
_NEGATORS = {"没有", "没", "无", "未", "不是", "不会", "别", "不用"}


def _has_negation(text: str, keyword: str) -> bool:
    """检测 keyword 前是否有否定词"""
    idx = text.find(keyword)
    if idx == -1:
        return False
    # 检查 keyword 前 5 个字符是否有否定词
    before = text[max(0, idx - 5):idx]
    return any(n in before for n in _NEGATORS)


def submit_report(req: ReportRequest) -> ReportResult:
    text = req.voice_text.lower()
    has_breakage = ("破损" in text or "损坏" in text) and not _has_negation(text, "破损") and not _has_negation(text, "损坏")
    has_delay = ("迟到" in text or "延迟" in text) and not _has_negation(text, "迟到") and not _has_negation(text, "延迟")
    has_address = ("地址" in text or "送错" in text) and not _has_negation(text, "地址")

    if has_breakage:
        return ReportResult(issue_type="goods_damage", priority="high", description=req.voice_text)
    if has_delay:
        return ReportResult(issue_type="delivery_delay", priority="medium", description=req.voice_text)
    if has_address:
        return ReportResult(issue_type="wrong_address", priority="high", description=req.voice_text)
    return ReportResult(issue_type="other", priority="low", description=req.voice_text)
