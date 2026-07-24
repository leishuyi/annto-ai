"""OCR 引擎：PaddleOCR / Mock 回退（线程安全）"""
import threading
from typing import List
from app.schemas.document import OCRResult

MOCK_WAYBILL_TEXT = """运单号：YD202407240001
托运人：美的集团佛山工厂
收货人：上海华联超市
始发站：佛山  目的地：上海
重量：1250kg  件数：50  体积：8.5m³
运费：¥8,500.00  付款方式：到付
日期：2026-07-24"""

MOCK_TEXTS = [
    MOCK_WAYBILL_TEXT,
    "签收回单\n签收人：李强\n签收日期：2026-07-24\n货物状态：完好\n备注：13:30送达",
    "入库单\nSKU: SKU-001 空调\n数量：200台\n库位：A-12-03\n经手人：王主管",
]


class OCREngine:
    def __init__(self, provider: str = "mock"):
        self.provider = provider
        self._lock = threading.Lock()
        self._counter = 0

    def extract_text(self, image_path: str) -> List[OCRResult]:
        if self.provider == "mock":
            with self._lock:
                idx = self._counter % len(MOCK_TEXTS)
                self._counter += 1
            return [OCRResult(text=MOCK_TEXTS[idx], confidence=0.92)]
        raise NotImplementedError(f"OCR provider '{self.provider}' not implemented")
