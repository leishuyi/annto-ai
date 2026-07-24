"""字段提取器：按文档类型提取结构化字段"""
from typing import Any, List
from app.schemas.document import FieldExtraction
from app.parser.ocr_engine import MOCK_WAYBILL_TEXT

MOCK_FIELDS = {
    "waybill": [
        FieldExtraction(field_name="waybill_no", value="YD202407240001", confidence=0.98),
        FieldExtraction(field_name="sender", value="美的集团佛山工厂", confidence=0.95),
        FieldExtraction(field_name="receiver", value="上海华联超市", confidence=0.95),
        FieldExtraction(field_name="origin", value="佛山", confidence=0.97),
        FieldExtraction(field_name="destination", value="上海", confidence=0.97),
        FieldExtraction(field_name="weight_kg", value=1250, confidence=0.92),
        FieldExtraction(field_name="pieces", value=50, confidence=0.90),
    ],
    "receipt": [
        FieldExtraction(field_name="signer", value="李强", confidence=0.96),
        FieldExtraction(field_name="sign_date", value="2026-07-24", confidence=0.94),
        FieldExtraction(field_name="goods_status", value="完好", confidence=0.88),
    ],
    "warehouse_doc": [
        FieldExtraction(field_name="sku", value="SKU-001", confidence=0.97),
        FieldExtraction(field_name="product", value="空调", confidence=0.95),
        FieldExtraction(field_name="quantity", value=200, confidence=0.96),
        FieldExtraction(field_name="location", value="A-12-03", confidence=0.93),
    ],
}

class FieldExtractor:
    def extract(self, doc_type: str, ocr_text: str) -> List[FieldExtraction]:
        return MOCK_FIELDS.get(doc_type, MOCK_FIELDS["waybill"])
