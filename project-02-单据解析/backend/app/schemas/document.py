import enum
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class DocumentType(str, enum.Enum):
    WAYBILL = "waybill"
    RECEIPT = "receipt"
    WAREHOUSE_DOC = "warehouse_doc"
    INVOICE = "invoice"
    ID_DOCUMENT = "id_document"

DOC_TYPE_LABELS = {
    DocumentType.WAYBILL: "运单",
    DocumentType.RECEIPT: "回单",
    DocumentType.WAREHOUSE_DOC: "仓储单",
    DocumentType.INVOICE: "发票",
    DocumentType.ID_DOCUMENT: "证件",
}


class OCRResult(BaseModel):
    text: str
    confidence: float
    bbox: Optional[list[float]] = None


class FieldExtraction(BaseModel):
    field_name: str
    value: Any
    confidence: float


class ParseResult(BaseModel):
    doc_type: str
    doc_type_label: str
    ocr_text: str
    ocr_confidence: float
    fields: list[FieldExtraction]
    overall_confidence: float
    processing_time_ms: int
