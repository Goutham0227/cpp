"""Invoice CRUD routes with PDF generation support."""

from flask import Blueprint, request, jsonify, current_app

invoice_bp = Blueprint("invoices", __name__)


@invoice_bp.route("/api/invoices", methods=["GET"])
def get_invoices():
    """List all invoices."""
    client_id = request.args.get("client_id")
    if client_id:
        invoices = current_app.config["invoice_model"].get_by_client(client_id)
    else:
        invoices = current_app.config["invoice_model"].get_all()
    return jsonify({"invoices": invoices, "count": len(invoices)}), 200


@invoice_bp.route("/api/invoices", methods=["POST"])
def create_invoice():
    """Create a new invoice."""
    data = request.get_json()
    if not data or "client_id" not in data:
        return jsonify({"error": "client_id is required"}), 400
    invoice = current_app.config["invoice_model"].create(data)
    current_app.config["cloudwatch"].put_metric("InvoicesCreated", 1)
    current_app.config["cloudwatch"].log_event("invoices", f"Created invoice for client: {data['client_id']}")
    return jsonify(invoice), 201


@invoice_bp.route("/api/invoices/<invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    """Get a specific invoice."""
    invoice = current_app.config["invoice_model"].get(invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
    return jsonify(invoice), 200


@invoice_bp.route("/api/invoices/<invoice_id>", methods=["PUT"])
def update_invoice(invoice_id):
    """Update an invoice."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    existing = current_app.config["invoice_model"].get(invoice_id)
    if not existing:
        return jsonify({"error": "Invoice not found"}), 404
    invoice = current_app.config["invoice_model"].update(invoice_id, data)
    return jsonify(invoice), 200


@invoice_bp.route("/api/invoices/<invoice_id>", methods=["DELETE"])
def delete_invoice(invoice_id):
    """Delete an invoice."""
    existing = current_app.config["invoice_model"].get(invoice_id)
    if not existing:
        return jsonify({"error": "Invoice not found"}), 404
    current_app.config["invoice_model"].delete(invoice_id)
    return jsonify({"message": "Invoice deleted"}), 200


@invoice_bp.route("/api/invoices/<invoice_id>/generate", methods=["POST"])
def generate_invoice_pdf(invoice_id):
    """Generate invoice PDF using Lambda and store in S3."""
    invoice = current_app.config["invoice_model"].get(invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    # Invoke Lambda to generate PDF
    lambda_service = current_app.config["lambda_service"]
    result = lambda_service.invoke_invoice_generator(invoice)

    # Store mock PDF in S3
    s3_service = current_app.config["s3_service"]
    pdf_content = f"Mock PDF content for invoice {invoice_id}".encode()
    pdf_key = f"invoices/{invoice_id}.pdf"
    upload_result = s3_service.upload_file(pdf_key, pdf_content)

    # Log the generation
    current_app.config["cloudwatch"].put_metric("InvoicePDFsGenerated", 1)

    return jsonify({
        "message": "Invoice PDF generated",
        "lambda_result": result,
        "s3_location": upload_result,
        "download_url": s3_service.get_presigned_url(pdf_key),
    }), 200


@invoice_bp.route("/api/receipts/scan", methods=["POST"])
def scan_receipt():
    """Scan a receipt using Textract OCR."""
    textract = current_app.config["textract"]
    # In real implementation, would read uploaded file
    mock_image = b"mock-receipt-image-data"
    result = textract.analyze_receipt(mock_image)
    current_app.config["cloudwatch"].put_metric("ReceiptsScanned", 1)
    return jsonify(result), 200
