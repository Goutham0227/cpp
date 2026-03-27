"""
Amazon API Gateway Service Wrapper.
Manages REST API endpoint configuration and rate limiting.
Falls back to local mock mode when USE_AWS is false.
"""

from datetime import datetime


class APIGatewayService:
    """Wrapper for Amazon API Gateway with local mock fallback."""

    def __init__(self, use_aws=False, region="eu-west-1", api_url="https://api.example.com"):
        self.use_aws = use_aws
        self.region = region
        self.api_url = api_url
        self._mock_endpoints = []
        self._request_log = []

        if self.use_aws:
            import boto3
            self.client = boto3.client("apigateway", region_name=region)
        else:
            self.client = None
            self._init_mock_endpoints()

    def _init_mock_endpoints(self):
        """Initialize mock API endpoints matching the Flask routes."""
        endpoints = [
            ("GET", "/api/clients", "List all clients"),
            ("POST", "/api/clients", "Create a client"),
            ("GET", "/api/clients/{id}", "Get a client"),
            ("PUT", "/api/clients/{id}", "Update a client"),
            ("DELETE", "/api/clients/{id}", "Delete a client"),
            ("GET", "/api/projects", "List all projects"),
            ("POST", "/api/projects", "Create a project"),
            ("GET", "/api/projects/{id}", "Get a project"),
            ("PUT", "/api/projects/{id}", "Update a project"),
            ("DELETE", "/api/projects/{id}", "Delete a project"),
            ("GET", "/api/time-entries", "List all time entries"),
            ("POST", "/api/time-entries", "Create a time entry"),
            ("GET", "/api/time-entries/{id}", "Get a time entry"),
            ("PUT", "/api/time-entries/{id}", "Update a time entry"),
            ("DELETE", "/api/time-entries/{id}", "Delete a time entry"),
            ("GET", "/api/invoices", "List all invoices"),
            ("POST", "/api/invoices", "Create an invoice"),
            ("GET", "/api/invoices/{id}", "Get an invoice"),
            ("PUT", "/api/invoices/{id}", "Update an invoice"),
            ("DELETE", "/api/invoices/{id}", "Delete an invoice"),
            ("POST", "/api/invoices/{id}/generate", "Generate invoice PDF"),
            ("GET", "/api/aws/status", "AWS service status"),
        ]
        for method, path, desc in endpoints:
            self._mock_endpoints.append({
                "method": method,
                "path": path,
                "description": desc,
                "created_at": datetime.utcnow().isoformat(),
            })

    def get_endpoints(self) -> list:
        if self.use_aws:
            response = self.client.get_rest_apis()
            return response.get("items", [])
        return self._mock_endpoints

    def log_request(self, method: str, path: str, status_code: int) -> None:
        self._request_log.append({
            "method": method,
            "path": path,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_request_log(self) -> list:
        return self._request_log[-100:]  # Last 100 requests

    def get_status(self) -> dict:
        return {
            "service": "Amazon API Gateway",
            "status": "available",
            "mode": "aws" if self.use_aws else "local_mock",
            "api_url": self.api_url,
            "endpoints": len(self._mock_endpoints) if not self.use_aws else "N/A",
            "requests_logged": len(self._request_log),
        }
