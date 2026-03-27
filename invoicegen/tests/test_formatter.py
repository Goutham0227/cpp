"""Tests for invoicegen.formatter module."""

import pytest
from datetime import datetime, timedelta
from invoicegen.models import Invoice, LineItem, InvoiceStatus
from invoicegen.formatter import CurrencyFormatter, InvoiceFormatter


class TestCurrencyFormatter:
    def test_format_eur(self):
        fmt = CurrencyFormatter("EUR")
        assert fmt.format(1234.56) == "\u20ac1,234.56"

    def test_format_usd(self):
        fmt = CurrencyFormatter("USD")
        assert fmt.format(999.99) == "$999.99"

    def test_format_gbp(self):
        fmt = CurrencyFormatter()
        assert fmt.format(500.0, "GBP") == "\u00a3500.00"

    def test_format_jpy_no_decimals(self):
        fmt = CurrencyFormatter("JPY")
        result = fmt.format(10000)
        assert result == "\u00a510,000"

    def test_format_with_code(self):
        fmt = CurrencyFormatter("EUR")
        result = fmt.format_with_code(100.0)
        assert "EUR" in result
        assert "\u20ac" in result

    def test_unknown_currency(self):
        fmt = CurrencyFormatter("XYZ")
        result = fmt.format(100.0)
        assert "100.00" in result


class TestInvoiceFormatter:
    def _make_invoice(self):
        inv = Invoice(client_id="c1", currency="EUR")
        inv.add_line_item(LineItem("Web Development", 10.0, 100.0))
        inv.add_line_item(LineItem("Design", 5.0, 80.0))
        inv.tax_rate = 23.0
        inv.tax_amount = 322.0
        inv.notes = "Thank you for your business"
        return inv

    def test_format_invoice_summary(self):
        inv = self._make_invoice()
        formatter = InvoiceFormatter()
        summary = formatter.format_invoice_summary(inv)
        assert "Web Development" in summary
        assert "Design" in summary
        assert "DRAFT" in summary
        assert "Thank you" in summary

    def test_format_status_badge(self):
        formatter = InvoiceFormatter()
        assert formatter.format_status_badge(InvoiceStatus.PAID) == "[PAID]"
        assert formatter.format_status_badge(InvoiceStatus.OVERDUE) == "[OVERDUE]"
        assert formatter.format_status_badge(InvoiceStatus.DRAFT) == "[DRAFT]"

    def test_format_line_items_table(self):
        inv = self._make_invoice()
        formatter = InvoiceFormatter()
        rows = formatter.format_line_items_table(inv)
        assert len(rows) == 2
        assert rows[0]["description"] == "Web Development"
        assert rows[0]["hours"] == 10.0
