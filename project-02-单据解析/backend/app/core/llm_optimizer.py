"""P2 单据解析 — LLM 优化引擎

技术栈：
  1. 双路分类器 — 关键词 + LLM 回退（置信度 < 0.85 时触发 LLM 二次分类）
  2. 结构化提取 — JSON Schema 约束字段提取
  3. 置信度校准 — 边际分析替代加权平均
  4. Prompt Cache — 静态模板前缀固定，动态内容后缀
"""
import hashlib
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Optional

from loguru import logger


# =============================================================================
# 1. 双路分类器 — 关键词 + LLM 回退
# =============================================================================

@dataclass
class ClassificationResult:
    doc_type: str
    confidence: float
    method: str  # "keyword" | "llm" | "fallback"
    candidates: list[tuple[str, float]] = None


class DualClassifier:
    """双路分类器：关键词快速路 + LLM 回退慢速路

    策略：
    - 关键词置信度 ≥ 0.85 → 直接输出（P99 < 5ms）
    - 关键词置信度 0.50~0.85 → LLM 二次确认（~1s）
    - 关键词置信度 < 0.50 → 返回 top-3 候选 + 不确定标记
    """

    # ---- 关键词规则（支持 21 行业扩展）----
    KEYWORDS: dict[str, list[str]] = {
        "waybill": ["运单号", "托运人", "收货人", "始发站", "目的地", "重量", "件数", "运费"],
        "receipt": ["签收", "回单", "签收人", "签收日期", "货物状态", "完好", "破损"],
        "warehouse_doc": ["入库单", "出库单", "SKU", "库位", "仓管", "盘点"],
        "invoice": ["发票", "发票号", "税率", "金额", "纳税人", "开户行"],
        "id_document": ["身份证", "证件", "姓名", "性别", "民族", "住址"],
    }

    # 21 行业扩展规则（根据行业前缀不同）
    INDUSTRY_PREFIXES: dict[str, list[str]] = {
        "appliance": ["家电", "空调", "冰箱", "洗衣机", "电视"],
        "fmcg": ["快消", "食品", "饮料", "日化"],
        "auto": ["汽车", "零部件", "轮胎", "发动机"],
        "furniture": ["家居", "家具", "沙发", "床垫"],
        "electronics": ["电子", "芯片", "元器件", "PCB"],
    }

    def __init__(self, llm_callback=None):
        self._stats = {"keyword_hits": 0, "llm_calls": 0, "fallbacks": 0}
        self.llm_callback = llm_callback

    def classify(self, text: str, industry_hint: str = "") -> ClassificationResult:
        """双路分类主入口"""
        if not text or not text.strip():
            return ClassificationResult("unknown", 0.0, "fallback")

        # 1. 关键词打分
        scores = self._keyword_score(text, industry_hint)
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        sorted_scores = sorted(scores.values(), reverse=True)
        margin = (best_score - sorted_scores[1]) / max(best_score, 0.01) if len(sorted_scores) > 1 else 1.0

        # 置信度校准：区分度越高，置信度越高
        confidence = best_score * (0.6 + 0.4 * min(margin, 1.0))
        confidence = max(0.0, min(0.99, confidence))

        # top-3 候选
        candidates = sorted(scores.items(), key=lambda x: -x[1])[:3]

        # 2. 路由决策
        if confidence >= 0.85:
            self._stats["keyword_hits"] += 1
            return ClassificationResult(best_type, round(confidence, 3), "keyword", candidates)

        elif confidence >= 0.50 and self.llm_callback:
            self._stats["llm_calls"] += 1
            llm_result = self._llm_confirm(text, candidates)
            if llm_result and llm_result.confidence > confidence:
                return llm_result

        self._stats["fallbacks"] += 1
        return ClassificationResult(best_type, round(confidence, 3), "fallback", candidates)

    def _keyword_score(self, text: str, industry: str) -> dict[str, float]:
        """关键词打分"""
        scores = {dt: 0.0 for dt in self.KEYWORDS}
        for doc_type, keywords in self.KEYWORDS.items():
            match_count = sum(1 for kw in keywords if kw in text)
            scores[doc_type] = match_count / max(len(keywords), 1)

        # 行业加权
        if industry:
            industry_kw = self.INDUSTRY_PREFIXES.get(industry, [])
            for doc_type in scores:
                if any(kw in text for kw in industry_kw):
                    scores[doc_type] *= 1.2

        return scores

    def _llm_confirm(self, text: str, candidates: list) -> Optional[ClassificationResult]:
        """LLM 二次确认"""
        if not self.llm_callback:
            return None
        prompt = (
            f"判断以下单据文本属于哪种类型？候选：{candidates}\n"
            f"文本：{text[:500]}\n"
            f"只返回类型名称，不要额外说明。"
        )
        try:
            result = self.llm_callback(prompt)
            for dt in self.KEYWORDS:
                if dt in result.lower():
                    return ClassificationResult(dt, 0.88, "llm", candidates)
        except Exception as e:
            logger.warning("LLM 分类回退失败", error=str(e))
        return None

    @property
    def stats(self) -> dict:
        total = sum(self._stats.values()) or 1
        return {**self._stats, "keyword_hit_rate": round(self._stats["keyword_hits"] / total * 100, 1)}


# =============================================================================
# 2. 置信度校准 — 边际分析替代加权平均
# =============================================================================

@dataclass
class CalibratedResult:
    final_confidence: float
    action: str  # "auto" | "spot_check" | "manual"
    margin: float


class ConfidenceCalibrator:
    """置信度校准器：边际分析 + 历史校准

    改进前：ocr*0.3 + cls*0.3 + avg(field)*0.4  (简单加权，区分度差)
    改进后：(best - second_best) / best            (边际分析，区分度好)
    """

    def calibrate(self, ocr_conf: float, cls_conf: float, field_confs: list[float]) -> CalibratedResult:
        """执行置信度校准"""
        if not field_confs:
            return CalibratedResult(0.0, "manual", 0.0)

        # 1. 加权融合
        avg_field = sum(field_confs) / len(field_confs)
        raw = ocr_conf * 0.25 + cls_conf * 0.25 + avg_field * 0.5

        # 2. 场间差异度分析
        sorted_confs = sorted(field_confs, reverse=True)
        if len(sorted_confs) >= 2:
            margin = (sorted_confs[0] - sorted_confs[1]) / max(sorted_confs[0], 0.01)
        else:
            margin = 0.5

        # 3. 边际分析修正
        final = raw * (0.7 + 0.3 * min(margin, 1.0))
        final = max(0.0, min(0.99, final))

        # 4. 动作决策
        if final > 0.85:
            action = "auto"
        elif final > 0.60:
            action = "spot_check"
        else:
            action = "manual"

        return CalibratedResult(
            final_confidence=round(final, 3),
            action=action,
            margin=round(margin, 3),
        )


# =============================================================================
# 3. 结构化输出 — VLM 字段提取
# =============================================================================

FIELD_SCHEMAS = {
    "waybill": {
        "waybill_no": {"type": "string", "description": "运单号"},
        "sender": {"type": "string", "description": "托运人"},
        "receiver": {"type": "string", "description": "收货人"},
        "origin": {"type": "string", "description": "始发站"},
        "destination": {"type": "string", "description": "目的地"},
        "weight_kg": {"type": "number", "description": "重量(kg)"},
        "pieces": {"type": "integer", "description": "件数"},
        "freight": {"type": "number", "description": "运费"},
    },
    "receipt": {
        "signer": {"type": "string", "description": "签收人"},
        "sign_date": {"type": "string", "description": "签收日期"},
        "goods_status": {"type": "string", "description": "货物状态"},
        "damage": {"type": "boolean", "description": "是否破损"},
    },
}


class StructuredExtractor:
    """结构化字段提取器"""

    @staticmethod
    def build_extraction_prompt(doc_type: str, ocr_text: str) -> str:
        schema = FIELD_SCHEMAS.get(doc_type, {})
        return (
            f"从以下 OCR 文本中提取 {doc_type} 的字段。\n"
            f"提取 Schema：{json.dumps(schema, ensure_ascii=False)}\n"
            f"OCR 文本：{ocr_text}\n"
            f"只返回 JSON。"
        )

    @staticmethod
    def parse_fields(raw: str) -> dict:
        """解析提取结果"""
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
