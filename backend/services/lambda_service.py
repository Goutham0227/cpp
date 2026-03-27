"""
AWS Lambda Service Wrapper.
Handles serverless invoice generation function.
Falls back to local function execution when USE_AWS is false.
"""

import json
from datetime import datetime


class LambdaService:
    """Wrapper for AWS Lambda with local execution fallback."""

    def __init__(self, use_aws=False, region="eu-west-1", function_name="invoice-generator"):
        self.use_aws = use_aws
        self.region = region
        self.function_name = function_name
        self._invocation_log = []

        if self.use_aws:
            import boto3
            self.client = boto3.client("lambda", region_name=region)
        else:
            self.client = None

    def invoke_invoice_generator(self, invoice_data: dict) -> dict:
        """Invoke the invoice generation Lambda function."""
        if self.use_aws:
            response = self.client.invoke(
                FunctionName=self.function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(invoice_data),
            )
            result = json.loads(response["Payload"].read())
            return result
        else:
            return self._mock_generate_invoice(invoice_data)

    def invoke_async(self, function_name: str, payload: dict) -> dict:
        """Invoke a Lambda function asynchronously."""
        if self.use_aws:
            response = self.client.invoke(
                FunctionName=function_name,
                InvocationType="Event",
                Payload=json.dumps(payload),
            )
            return {"status": "invoked", "status_code": response["StatusCode"]}
        else:
            self._invocation_log.append({
                "function": function_name,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "async",
            })
            return {"status": "mock_invoked", "status_code": 202}

    def _mock_generate_invoice(self, invoice_data: dict) -> dict:
        """Local mock of invoice generation Lambda."""
        self._invocation_log.append({
            "function": self.function_name,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "sync",
        })

        line_items = invoice_data.get("line_items", [])
        subtotal = sum(
            item.get("quantity", 0) * item.get("unit_price", 0)
            for item in line_items
        )
        tax_rate = invoice_data.get("tax_rate", 0)
        tax_amount = round(subtotal * tax_rate / 100, 2)
        total = round(subtotal + tax_amount, 2)

        return {
            "statusCode": 200,
            "body": {
                "invoice_id": invoice_data.get("invoice_id", "mock-inv-001"),
                "invoice_number": invoice_data.get("invoice_number", "INV-MOCK-001"),
                "subtotal": subtotal,
                "tax_amount": tax_amount,
                "total": total,
                "pdf_key": f"invoices/{invoice_data.get('invoice_id', 'mock')}.pdf",
                "generated_at": datetime.utcnow().isoformat(),
                "status": "generated",
            },
        }

    def get_invocation_log(self) -> list:
        return self._invocation_log

    def get_status(self) -> dict:
        return {
            "service": "AWS Lambda",
            "status": "available",
            "mode": "aws" if self.use_aws else "local_mock",
            "function_name": self.function_name,
            "invocations": len(self._invocation_log),
        }
