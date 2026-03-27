"""Tests for invoicegen.invoice_builder module."""

import pytest
from datetime import datetime, timedelta
from invoicegen.models import TimeEntry, InvoiceStatus
from invoicegen.invoice_builder import InvoiceBuilder
from invoicegen.tax import TaxRate, TaxType


class TestInvoiceBuilder:
    def _make_entry(self, desc, hours, rate, project_id="p1"):
        start = datetime(2025, 3, 10, 9, 0)
        end = start + timedelta(hours=hours)
        return TimeEntry(project_id=project_id, description=desc,
                         start_time=start, end_time=end, hourly_rate=rate)

    def test_build_basic_invoice(self):
        entries = [
            self._make_entry("Backend", 4, 100),
            self._make_entry("Frontend", 3, 80),
        ]
        invoice = (InvoiceBuilder()
                   .set_client("c1")
                   .add_time_entries(entries)
                   .build())
        assert invoice.client_id == "c1"
        assert len(invoice.line_items) == 2
        assert invoice.subtotal == 640.0

    def test_build_with_tax(self):
        entries = [self._make_entry("Work", 10, 100)]
        tax = TaxRate("VAT", 23.0, TaxType.VAT)
        invoice = (InvoiceBuilder()
                   .set_client("c1")
                   .add_time_entries(entries)
                   .set_tax_rate(tax)
                   .build())
        assert invoice.tax_amount == 230.0
        assert invoice.total == 1230.0

    def test_build_with_custom_line_item(self):
        invoice = (InvoiceBuilder()
                   .set_client("c1")
                   .add_custom_line_item("Hosting Fee", 1, 50.0)
                   .add_custom_line_item("Domain", 1, 15.0)
                   .build())
        assert invoice.subtotal == 65.0

    def test_build_with_currency(self):
        invoice = (InvoiceBuilder()
                   .set_client("c1")
                   .set_currency("USD")
                   .add_custom_line_item("Work", 5, 100)
                   .build())
        assert invoice.currency == "USD"

    def test_build_with_notes(self):
        invoice = (InvoiceBuilder()
                   .set_client("c1")
                   .set_notes("Payment due in 30 days")
                   .add_custom_line_item("Work", 1, 100)
                   .build())
        assert invoice.notes == "Payment due in 30 days"

    def test_build_without_client_raises(self):
        with pytest.raises(ValueError, match="Client ID"):
            InvoiceBuilder().build()

    def test_build_grouped_by_project(self):
        entries = [
            self._make_entry("Task A", 2, 100, project_id="p1"),
            self._make_entry("Task B", 3, 100, project_id="p1"),
            self._make_entry("Task C", 4, 80, project_id="p2"),
        ]
        invoice = (InvoiceBuilder()
                   .set_client("c1")
                   .add_time_entries(entries)
                   .group_by_project()
                   .build())
        assert len(invoice.line_items) == 2  # grouped by project

    def test_set_due_days(self):
        invoice = (InvoiceBuilder()
                   .set_client("c1")
                   .set_due_days(14)
                   .add_custom_line_item("Rush job", 1, 500)
                   .build())
        diff = (invoice.due_date - invoice.created_at).days
        assert 13 <= diff <= 15

    def test_set_invoice_number(self):
        invoice = (InvoiceBuilder()
                   .set_client("c1")
                   .set_invoice_number("INV-2025-001")
                   .add_custom_line_item("Work", 1, 100)
                   .build())
        assert invoice.invoice_number == "INV-2025-001"

    def test_add_single_entry(self):
        entry = self._make_entry("Solo task", 2, 75)
        invoice = (InvoiceBuilder()
                   .set_client("c1")
                   .add_time_entry(entry)
                   .build())
        assert len(invoice.line_items) == 1
        assert invoice.subtotal == 150.0
