"""文档分类器：LLM 判断单据类型"""
from typing import Tuple

class DocClassifier:
    def __init__(self):
        self.doc_types = ["waybill", "receipt", "warehouse_doc", "invoice", "id_document"]
        self.labels = {"waybill": "运单", "receipt": "回单", "warehouse_doc": "仓储单", "invoice": "发票", "id_document": "证件"}

    def classify(self, ocr_text: str, image_desc: str = "") -> Tuple[str, float]:
        """判断文档类型，返回 (doc_type, confidence)"""
        text_lower = ocr_text.lower()
        keyword_scores = {
            "waybill": sum(1 for k in ["运单号", "托运人", "收货人", "始发站", " destination"] if k in text_lower),
            "receipt": sum(1 for k in ["签收", "回单", "签收人", "收货日期", "完好"] if k in text_lower),
            "warehouse_doc": sum(1 for k in ["入库单", "SKU", "货位", "库位", "数量"] if k in text_lower),
            "invoice": sum(1 for k in ["发票", "税额", "价税合计", "纳税人", "¥"] if k in text_lower),
            "id_document": sum(1 for k in ["身份证", "姓名", "性别", "民族", "出生"] if k in text_lower),
        }
        best = max(keyword_scores, key=keyword_scores.get)
        confidence = min(0.95, 0.5 + keyword_scores[best] * 0.1)
        if keyword_scores[best] == 0:
            return ("waybill", 0.6)
        return (best, round(confidence, 2))
