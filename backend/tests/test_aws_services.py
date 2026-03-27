"""API integration tests for AWS service status and health endpoints."""

import pytest


class TestAWSRoutes:
    def test_health_check(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert "25167936" in data["student"]

    def test_aws_status(self, client):
        resp = client.get("/api/aws/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_services"] == 7
        assert "dynamodb" in data["aws_services"]
        assert "s3" in data["aws_services"]
        assert "lambda" in data["aws_services"]
        assert "api_gateway" in data["aws_services"]
        assert "cognito" in data["aws_services"]
        assert "cloudwatch" in data["aws_services"]
        assert "textract" in data["aws_services"]

    def test_aws_all_services_available(self, client):
        resp = client.get("/api/aws/status")
        data = resp.get_json()
        for service_name, service_data in data["aws_services"].items():
            assert service_data["status"] == "available", f"{service_name} not available"
            assert service_data["mode"] == "local_mock"

    def test_get_metrics(self, client):
        resp = client.get("/api/aws/metrics")
        assert resp.status_code == 200

    def test_get_logs(self, client):
        resp = client.get("/api/aws/logs")
        assert resp.status_code == 200

    def test_get_alarms(self, client):
        resp = client.get("/api/aws/alarms")
        assert resp.status_code == 200
