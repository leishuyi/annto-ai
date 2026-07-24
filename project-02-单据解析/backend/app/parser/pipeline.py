"""解析管线：分类 → OCR → 提取 → 置信度校准

优化点：
  - 关键词 + LLM 双路分类（旧：纯关键词）
  - 边际分析置信度校准（旧：简单加权平均）
  - 结构化提取 Schema 约束
"""
import time
from app.config import settings
from app.schemas.document import ParseResult, DocumentType, DOC_TYPE_LABELS
from app.parser.classifier import DocClassifier
from app.parser.ocr_engine import OCREngine
from app.parser.field_extractor import FieldExtractor
from app.core.llm_optimizer import ConfidenceCalibrator


class ParsePipeline:
    def __init__(self):
        self.classifier = DocClassifier()
        self.ocr = OCREngine(settings.ocr_provider)
        self.extractor = FieldExtractor()
        self.calibrator = ConfidenceCalibrator()

    def parse(self, file_path: str, industry_hint: str = "") -> ParseResult:
        t0 = time.time()
        ocr_results = self.ocr.extract_text(file_path)
        ocr_text = ocr_results[0].text if ocr_results else ""
        ocr_conf = ocr_results[0].confidence if ocr_results else 0

        # [优化] 双路分类 + 置信度校准
        doc_type, cls_conf = self.classifier.classify(ocr_text, industry_hint)
        fields = self.extractor.extract(doc_type, ocr_text)

        field_confs = [f.confidence for f in fields]
        cal = self.calibrator.calibrate(ocr_conf, cls_conf, field_confs)

        return ParseResult(
            doc_type=doc_type,
            doc_type_label=DOC_TYPE_LABELS.get(DocumentType(doc_type), doc_type),
            ocr_text=ocr_text,
            ocr_confidence=ocr_conf,
            fields=fields,
            overall_confidence=cal.final_confidence,
            processing_time_ms=int((time.time() - t0) * 1000),
        )
