"""Tests for invoicegen.calculator module."""

import pytest
from datetime import datetime, timedelta
from invoicegen.models import TimeEntry, Invoice, LineItem, InvoiceStatus
from invoicegen.calculator import TimeCalculator, BillingCalculator


class TestTimeCalculator:
    def _make_entry(self, hours, rate=50.0, start_date=None):
        start = start_date or datetime(2025, 3, 10, 9, 0)
        end = start + timedelta(hours=hours)
        return TimeEntry(project_id="p1", description="Work",
                         start_time=start, end_time=end, hourly_rate=rate)

    def test_total_hours(self):
        entries = [self._make_entry(2), self._make_entry(3), self._make_entry(1.5)]
        assert TimeCalculator.total_hours(entries) == 6.5

    def test_total_billable_amount(self):
        entries = [self._make_entry(2, rate=100), self._make_entry(3, rate=80)]
        assert TimeCalculator.total_billable_amount(entries) == 440.0

    def test_weekly_summary(self):
        # Monday March 10, 2025
        monday = datetime(2025, 3, 10, 9, 0)
        wednesday = datetime(2025, 3, 12, 9, 0)
        entries = [
            self._make_entry(4, start_date=monday),
            self._make_entry(6, start_date=wednesday),
        ]
        summary = TimeCalculator.weekly_summary(entries, week_start=monday)
        assert summary["Monday"] == 4.0
        assert summary["Wednesday"] == 6.0
        assert summary["Friday"] == 0.0

    def test_monthly_summary(self):
        entries = [
            self._make_entry(3, rate=100, start_date=datetime(2025, 3, 5, 9, 0)),
            self._make_entry(5, rate=100, start_date=datetime(2025, 3, 15, 9, 0)),
        ]
        summary = TimeCalculator.monthly_summary(entries, 2025, 3)
        assert summary["total_hours"] == 8.0
        assert summary["total_amount"] == 800.0
        assert summary["num_entries"] == 2

    def test_entries_by_project(self):
        e1 = TimeEntry(project_id="p1", start_time=datetime(2025, 1, 1, 9, 0),
                       end_time=datetime(2025, 1, 1, 10, 0), hourly_rate=50)
        e2 = TimeEntry(project_id="p2", start_time=datetime(2025, 1, 1, 9, 0),
                       end_time=datetime(2025, 1, 1, 11, 0), hourly_rate=60)
        e3 = TimeEntry(project_id="p1", start_time=datetime(2025, 1, 2, 9, 0),
                       end_time=datetime(2025, 1, 2, 12, 0), hourly_rate=50)
        grouped = TimeCalculator.entries_by_project([e1, e2, e3])
        assert len(grouped["p1"]) == 2
        assert len(grouped["p2"]) == 1

    def test_average_daily_hours(self):
        entries = [
            self._make_entry(4, start_date=datetime(2025, 3, 10, 9, 0)),
            self._make_entry(6, start_date=datetime(2025, 3, 10, 14, 0)),
            self._make_entry(8, start_date=datetime(2025, 3, 11, 9, 0)),
        ]
        avg = TimeCalculator.average_daily_hours(entries)
        assert avg == 9.0  # 18 hours / 2 days

    def test_average_daily_hours_empty(self):
        assert TimeCalculator.average_daily_hours([]) == 0.0


class TestBillingCalculator:
    def _make_invoice(self, client_id, total_amount, status=InvoiceStatus.SENT, overdue=False):
        inv = Invoice(client_id=client_id)
        inv.add_line_item(LineItem("Work", total_amount / 100, 100.0))
        inv.status = status
        if overdue:
            inv.due_date = datetime.utcnow() - timedelta(days=10)
        return inv

    def test_client_billing_summary(self):
        invoices = [
            self._make_invoice("c1", 1000, InvoiceStatus.PAID),
            self._make_invoice("c1", 500, InvoiceStatus.SENT),
            self._make_invoice("c1", 300, InvoiceStatus.OVERDUE, overdue=True),
            self._make_invoice("c2", 2000, InvoiceStatus.PAID),
        ]
        summary = BillingCalculator.client_billing_summary(invoices, "c1")
        assert summary["total_invoices"] == 3
        assert summary["total_paid"] == 1000.0
        assert summary["total_outstanding"] == 800.0

    def test_find_overdue_invoices(self):
        invoices = [
            self._make_invoice("c1", 500, InvoiceStatus.SENT, overdue=True),
            self._make_invoice("c1", 300, InvoiceStatus.PAID),
            self._make_invoice("c1", 200, InvoiceStatus.SENT, overdue=False),
        ]
        overdue = BillingCalculator.find_overdue_invoices(invoices)
        assert len(overdue) == 1

    def test_revenue_by_month(self):
        inv1 = Invoice(client_id="c1")
        inv1.add_line_item(LineItem("Work", 10, 100))
        inv1.status = InvoiceStatus.PAID
        inv1.created_at = datetime(2025, 1, 15)

        inv2 = Invoice(client_id="c1")
        inv2.add_line_item(LineItem("Work", 5, 100))
        inv2.status = InvoiceStatus.PAID
        inv2.created_at = datetime(2025, 2, 10)

        revenue = BillingCalculator.revenue_by_month([inv1, inv2])
        assert revenue["2025-01"] == 1000.0
        assert revenue["2025-02"] == 500.0
