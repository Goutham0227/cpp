"""
Amazon Textract Service Wrapper.
Handles receipt and expense OCR processing.
Falls back to local mock mode when USE_AWS is false.
"""

import uuid
from datetime import datetime


class TextractService:
    """Wrapper for Amazon Textract with local mock fallback."""

    def __init__(self, use_aws=False, region="eu-west-1"):
        self.use_aws = use_aws
        self.region = region
        self._mock_results = []

        if self.use_aws:
            import boto3
            self.client = boto3.client("textract", region_name=region)
        else:
            self.client = None

    def analyze_receipt(self, image_bytes: bytes) -> dict:
        """Analyze a receipt image and extract expense data."""
        if self.use_aws:
            response = self.client.analyze_expense(
                Document={"Bytes": image_bytes}
            )
            return self._parse_expense_response(response)
        else:
            return self._mock_analyze_receipt(image_bytes)

    def detect_text(self, image_bytes: bytes) -> dict:
        """Detect text in an image."""
        if self.use_aws:
            response = self.client.detect_document_text(
                Document={"Bytes": image_bytes}
            )
            return {
                "blocks": response.get("Blocks", []),
                "text": " ".join(
                    b["Text"] for b in response.get("Blocks", [])
                    if b["BlockType"] == "LINE"
                ),
            }
        else:
            return self._mock_detect_text(image_bytes)

    def _mock_analyze_receipt(self, image_bytes: bytes) -> dict:
        """Generate mock receipt analysis results."""
        result = {
            "receipt_id": str(uuid.uuid4()),
            "analyzed_at": datetime.utcnow().isoformat(),
            "vendor": "Office Supplies Ltd",
            "date": "2025-03-01",
            "total": 145.99,
            "tax": 27.54,
            "subtotal": 118.45,
            "currency": "EUR",
            "items": [
                {"description": "Printer Paper A4", "quantity": 5, "price": 8.99},
                {"description": "Ink Cartridge Black", "quantity": 2, "price": 24.99},
                {"description": "USB Cable", "quantity": 1, "price": 12.50},
            ],
            "confidence": 0.95,
            "raw_text": "Office Supplies Ltd\nDate: 01/03/2025\nPrinter Paper A4 x5 8.99\nInk Cartridge x2 24.99\nUSB Cable x1 12.50\nSubtotal: 118.45\nVAT: 27.54\nTotal: 145.99",
        }
        self._mock_results.append(result)
        return result

    def _mock_detect_text(self, image_bytes: bytes) -> dict:
        """Generate mock text detection results."""
        result = {
            "text": "Sample detected text from receipt or document image.",
            "blocks": [
                {"type": "LINE", "text": "Sample detected text", "confidence": 0.98},
                {"type": "LINE", "text": "from receipt or document image.", "confidence": 0.96},
            ],
            "confidence": 0.97,
        }
        return result

    def _parse_expense_response(self, response: dict) -> dict:
        """Parse AWS Textract expense analysis response."""
        documents = response.get("ExpenseDocuments", [])
        if not documents:
            return {"error": "No expense data found"}

        doc = documents[0]
        summary_fields = {}
        for field in doc.get("SummaryFields", []):
            label = field.get("Type", {}).get("Text", "")
            value = field.get("ValueDetection", {}).get("Text", "")
            summary_fields[label] = value

        return {
            "receipt_id": str(uuid.uuid4()),
            "analyzed_at": datetime.utcnow().isoformat(),
            "vendor": summary_fields.get("VENDOR_NAME", "Unknown"),
            "total": summary_fields.get("TOTAL", "0.00"),
            "tax": summary_fields.get("TAX", "0.00"),
            "date": summary_fields.get("INVOICE_RECEIPT_DATE", ""),
            "raw_fields": summary_fields,
        }

    def get_analysis_history(self) -> list:
        return self._mock_results

    def get_status(self) -> dict:
        return {
            "service": "Amazon Textract",
            "status": "available",
            "mode": "aws" if self.use_aws else "local_mock",
            "analyses_performed": len(self._mock_results),
        }
