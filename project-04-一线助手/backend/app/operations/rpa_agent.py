"""RPA finance reconciliation agent (mock)"""
from app.schemas.operations import ReconResult, AnalysisResult, AdjustmentSuggestion
from app.core.llm import llm


class RPAFinanceAgent:
    def reconcile(self, period: str) -> ReconResult:
        return ReconResult(
            total_invoices=150,
            total_amount=1250000.00,
            matched_count=145,
            unmatched_count=5,
            unmatched_items=[
                {"invoice_no": "INV-2024-089", "expected": 8500, "actual": 8200, "diff": -300},
                {"invoice_no": "INV-2024-092", "expected": 12000, "actual": 12500, "diff": 500},
                {"invoice_no": "INV-2024-095", "expected": 6500, "actual": 0, "diff": -6500},
            ],
        )

    def analyze(self, items: list) -> AnalysisResult:
        reasons = llm.chat([{"role": "user", "content": f"分析这些对账差异: {items}"}])
        return AnalysisResult(
            discrepancy_reason=reasons,
            confidence=0.82,
            suggested_action="差异INV-2024-095可能为未开票，建议核实后补录",
        )

    def suggest_adjustment(self, analysis: AnalysisResult) -> AdjustmentSuggestion:
        return AdjustmentSuggestion(action="auto_fix", amount=6500, reason=analysis.suggested_action)
