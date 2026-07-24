"""解析管线：分类 → OCR → 提取 → 验证"""
import time
from app.config import settings
from app.schemas.document import ParseResult, DocumentType, DOC_TYPE_LABELS
from app.parser.classifier import DocClassifier
from app.parser.ocr_engine import OCREngine
from app.parser.field_extractor import FieldExtractor

class ParsePipeline:
    def __init__(self):
        self.classifier = DocClassifier()
        self.ocr = OCREngine(settings.ocr_provider)
        self.extractor = FieldExtractor()

    def parse(self, file_path: str) -> ParseResult:
        t0 = time.time()
        ocr_results = self.ocr.extract_text(file_path)
        ocr_text = ocr_results[0].text if ocr_results else ""
        ocr_conf = ocr_results[0].confidence if ocr_results else 0
        doc_type, cls_conf = self.classifier.classify(ocr_text)
        fields = self.extractor.extract(doc_type, ocr_text)
        overall = round((ocr_conf * 0.3 + cls_conf * 0.3 + sum(f.confidence for f in fields) / len(fields) * 0.4), 2)
        return ParseResult(
            doc_type=doc_type,
            doc_type_label=DOC_TYPE_LABELS.get(DocumentType(doc_type), doc_type),
            ocr_text=ocr_text,
            ocr_confidence=ocr_conf,
            fields=fields,
            overall_confidence=overall,
            processing_time_ms=int((time.time() - t0) * 1000),
        )
