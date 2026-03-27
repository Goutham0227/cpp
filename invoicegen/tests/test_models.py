"""Tests for invoicegen.models module."""

import pytest
from datetime import datetime, timedelta
from invoicegen.models import (
    Client, Project, TimeEntry, Invoice, LineItem, InvoiceStatus
)


class TestClient:
    def test_create_client(self):
        client = Client(name="John Doe", email="john@example.com", company="Acme Corp")
        assert client.name == "John Doe"
        assert client.email == "john@example.com"
        assert client.company == "Acme Corp"
        assert client.client_id is not None

    def test_client_to_dict(self):
        client = Client(name="Jane", email="jane@test.com")
        d = client.to_dict()
        assert d["name"] == "Jane"
        assert d["email"] == "jane@test.com"
        assert "client_id" in d

    def test_client_from_dict(self):
        data = {"name": "Bob", "email": "bob@test.com", "company": "BobCo", "client_id": "abc123"}
        client = Client.from_dict(data)
        assert client.name == "Bob"
        assert client.client_id == "abc123"

    def test_client_repr(self):
        client = Client(name="Test", email="test@test.com", company="TestCo")
        assert "Test" in repr(client)


class TestProject:
    def test_create_project(self):
        project = Project(name="Website Redesign", client_id="c1", hourly_rate=75.0)
        assert project.name == "Website Redesign"
        assert project.hourly_rate == 75.0
        assert project.is_active is True

    def test_project_serialization(self):
        project = Project(name="API Dev", client_id="c2", hourly_rate=100.0)
        d = project.to_dict()
        restored = Project.from_dict(d)
        assert restored.name == "API Dev"
        assert restored.hourly_rate == 100.0


class TestTimeEntry:
    def test_create_time_entry(self):
        start = datetime(2025, 1, 15, 9, 0)
        end = datetime(2025, 1, 15, 12, 30)
        entry = TimeEntry(project_id="p1", description="Backend work",
                          start_time=start, end_time=end, hourly_rate=80.0)
        assert entry.duration_hours == 3.5
        assert entry.total_amount == 280.0

    def test_running_entry(self):
        entry = TimeEntry(project_id="p1", hourly_rate=50.0)
        assert entry.is_running is True
        assert entry.duration_hours == 0.0

    def test_stop_entry(self):
        entry = TimeEntry(project_id="p1", hourly_rate=50.0)
        entry.stop()
        assert entry.is_running is False

    def test_entry_serialization(self):
        start = datetime(2025, 2, 1, 10, 0)
        end = datetime(2025, 2, 1, 14, 0)
        entry = TimeEntry(project_id="p1", start_time=start, end_time=end, hourly_rate=60.0)
        d = entry.to_dict()
        restored = TimeEntry.from_dict(d)
        assert restored.duration_hours == 4.0
        assert restored.total_amount == 240.0


class TestLineItem:
    def test_create_line_item(self):
        item = LineItem(description="Web Development", quantity=10.5, unit_price=75.0)
        assert item.subtotal == 787.5

    def test_line_item_serialization(self):
        item = LineItem(description="Design", quantity=5.0, unit_price=100.0)
        d = item.to_dict()
        restored = LineItem.from_dict(d)
        assert restored.subtotal == 500.0


class TestInvoice:
    def test_create_invoice(self):
        invoice = Invoice(client_id="c1")
        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.total == 0.0

    def test_add_line_items(self):
        invoice = Invoice(client_id="c1")
        invoice.add_line_item(LineItem("Task A", 5.0, 100.0))
        invoice.add_line_item(LineItem("Task B", 3.0, 80.0))
        assert invoice.subtotal == 740.0
        assert len(invoice.line_items) == 2

    def test_remove_line_item(self):
        invoice = Invoice(client_id="c1")
        item = LineItem("Remove me", 1.0, 50.0)
        invoice.add_line_item(item)
        assert invoice.remove_line_item(item.item_id) is True
        assert len(invoice.line_items) == 0

    def test_invoice_with_tax(self):
        invoice = Invoice(client_id="c1")
        invoice.add_line_item(LineItem("Work", 10.0, 100.0))
        invoice.tax_rate = 23.0
        invoice.tax_amount = 230.0
        assert invoice.subtotal == 1000.0
        assert invoice.total == 1230.0

    def test_mark_sent_and_paid(self):
        invoice = Invoice(client_id="c1")
        invoice.mark_sent()
        assert invoice.status == InvoiceStatus.SENT
        invoice.mark_paid()
        assert invoice.status == InvoiceStatus.PAID

    def test_overdue_detection(self):
        invoice = Invoice(client_id="c1")
        invoice.due_date = datetime.utcnow() - timedelta(days=5)
        assert invoice.is_overdue is True

    def test_paid_not_overdue(self):
        invoice = Invoice(client_id="c1")
        invoice.due_date = datetime.utcnow() - timedelta(days=5)
        invoice.mark_paid()
        assert invoice.is_overdue is False

    def test_invoice_serialization(self):
        invoice = Invoice(client_id="c1", currency="USD")
        invoice.add_line_item(LineItem("Dev", 8.0, 120.0))
        invoice.tax_rate = 10.0
        invoice.tax_amount = 96.0
        d = invoice.to_dict()
        restored = Invoice.from_dict(d)
        assert restored.subtotal == 960.0
        assert restored.currency == "USD"
