"""AWS service status and management routes."""

from flask import Blueprint, jsonify, current_app

aws_bp = Blueprint("aws", __name__)


@aws_bp.route("/api/aws/status", methods=["GET"])
def get_aws_status():
    """Get status of all 7 AWS services."""
    services = {
        "dynamodb": current_app.config["dynamodb"].get_status(),
        "s3": current_app.config["s3_service"].get_status(),
        "lambda": current_app.config["lambda_service"].get_status(),
        "api_gateway": current_app.config["api_gateway"].get_status(),
        "cognito": current_app.config["cognito"].get_status(),
        "cloudwatch": current_app.config["cloudwatch"].get_status(),
        "textract": current_app.config["textract"].get_status(),
    }
    return jsonify({
        "aws_services": services,
        "total_services": 7,
        "mode": "aws" if current_app.config.get("USE_AWS") else "local_mock",
    }), 200


@aws_bp.route("/api/aws/metrics", methods=["GET"])
def get_metrics():
    """Get CloudWatch metrics."""
    metrics = current_app.config["cloudwatch"].get_metrics()
    return jsonify({"metrics": metrics}), 200


@aws_bp.route("/api/aws/logs", methods=["GET"])
def get_logs():
    """Get CloudWatch logs."""
    logs = current_app.config["cloudwatch"].get_logs()
    return jsonify({"logs": logs}), 200


@aws_bp.route("/api/aws/alarms", methods=["GET"])
def get_alarms():
    """Get CloudWatch alarms."""
    alarms = current_app.config["cloudwatch"].get_alarms()
    return jsonify({"alarms": alarms}), 200


@aws_bp.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "application": "Freelancer Time Tracking & Invoice Generator",
        "student": "Goutham Uppu (25167936)",
    }), 200
