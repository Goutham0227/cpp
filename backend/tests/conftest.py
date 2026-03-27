"""Shared test fixtures for backend API tests."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from config import TestingConfig


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(TestingConfig)
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_client_data():
    return {
        "name": "Test Client",
        "email": "test@example.com",
        "company": "Test Corp",
        "address": "123 Test St",
        "phone": "+353-1-234-5678",
    }


@pytest.fixture
def sample_project_data():
    return {
        "name": "Test Project",
        "client_id": "placeholder",
        "description": "A test project",
        "hourly_rate": 85.0,
    }


@pytest.fixture
def sample_time_entry_data():
    return {
        "project_id": "placeholder",
        "description": "Working on tests",
        "start_time": "2025-03-10T09:00:00",
        "end_time": "2025-03-10T12:30:00",
        "hourly_rate": 85.0,
    }


@pytest.fixture
def sample_invoice_data():
    return {
        "client_id": "placeholder",
        "line_items": [
            {"description": "Dev work", "quantity": 10.0, "unit_price": 100.0},
        ],
        "tax_rate": 23.0,
        "tax_amount": 230.0,
        "currency": "EUR",
        "notes": "Due in 30 days",
    }
