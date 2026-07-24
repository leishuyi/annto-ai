"""文档分类器 — 升级为双路分类（关键词 + LLM 回退）+ 21 行业扩展"""
from typing import Tuple
from app.core.llm_optimizer import DualClassifier, ConfidenceCalibrator


class DocClassifier:
    """文档分类器 — 双路（关键词 + LLM 回退）+ 置信度校准"""

    def __init__(self):
        self.dual = DualClassifier(llm_callback=self._llm_classify)
        self.calibrator = ConfidenceCalibrator()

    def classify(self, ocr_text: str, image_desc: str = "", industry_hint: str = "") -> Tuple[str, float]:
        """双路分类入口"""
        result = self.dual.classify(ocr_text, industry_hint)
        return result.doc_type, result.confidence

    def _llm_classify(self, prompt: str) -> str:
        """LLM 分类回退（生产环境替换为真实 DeepSeek API）"""
        return "waybill"
