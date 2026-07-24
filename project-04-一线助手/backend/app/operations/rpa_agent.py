"""RPA finance reconciliation agent — mock with period-based variation."""
import hashlib
from app.schemas.operations import ReconResult, AnalysisResult, AdjustmentSuggestion
from app.core.llm import llm


class RPAFinanceAgent:
    def reconcile(self, period: str) -> ReconResult:
        # 基于 period 生成确定性差异，同一周期返回相同结果
        seed = int(hashlib.md5(period.encode()).hexdigest()[:8], 16)
        total = 150 + (seed % 20)
        matched = total - (seed % 10) - 1
        return ReconResult(
            total_invoices=total,
            total_amount=round(1000000 + seed * 100, 2),
            matched_count=max(0, matched),
            unmatched_count=max(1, total - matched),
            unmatched_items=[
                {"invoice_no": f"INV-{period}-{i:03d}", "expected": 8000 + i * 100, "actual": 7800 + i * 50, "diff": -200 - i * 50}
                for i in range(max(1, total - matched))
            ],
        )

    def analyze(self, items: list) -> AnalysisResult:
        reasons = llm.chat([{"role": "user", "content": f"分析这些对账差异: {items}"}])
        return AnalysisResult(
            discrepancy_reason=reasons,
            confidence=0.82,
            suggested_action="建议核实未匹配项目，可能存在未开票或价格变动情况",
        )

    def suggest_adjustment(self, analysis: AnalysisResult) -> AdjustmentSuggestion:
        return AdjustmentSuggestion(action="auto_fix", amount=6500, reason=analysis.suggested_action)
