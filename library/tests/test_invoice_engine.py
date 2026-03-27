"""
Unit tests for invoice_engine library.
"""

import unittest
import re
from datetime import datetime, timedelta

from invoice_engine.calculator import TimeCalculator
from invoice_engine.invoice import InvoiceGenerator
from invoice_engine.validator import InvoiceValidator
from invoice_engine.formatter import ReportFormatter


# ---------------------------------------------------------------------------
# Sample data helpers
# ---------------------------------------------------------------------------

def _sample_time_logs():
    return [
        {
            "startTime": "2026-03-01T09:00:00",
            "endTime": "2026-03-01T11:30:00",
            "description": "Backend API development",
            "project": "ProjectA",
            "billable": True,
        },
        {
            "startTime": "2026-03-01T13:00:00",
            "endTime": "2026-03-01T15:00:00",
            "description": "Code review",
            "project": "ProjectA",
            "billable": False,
        },
        {
            "startTime": "2026-03-02T10:00:00",
            "endTime": "2026-03-02T14:00:00",
            "description": "Frontend implementation",
            "project": "ProjectA",
            "billable": True,
        },
    ]


def _sample_client():
    return {"name": "Jane Doe", "email": "jane@example.com", "company": "Acme Ltd"}


def _sample_project():
    return {"name": "ProjectA", "hourlyRate": 50, "client": "Jane Doe"}


# ===========================================================================
# TimeCalculator tests
# ===========================================================================

class TestCalculateDuration(unittest.TestCase):
    def test_basic_duration(self):
        self.assertEqual(
            TimeCalculator.calculate_duration(
                "2026-03-01T09:00:00", "2026-03-01T11:30:00"
            ),
            2.5,
        )

    def test_zero_duration(self):
        self.assertEqual(
            TimeCalculator.calculate_duration(
                "2026-03-01T09:00:00", "2026-03-01T09:00:00"
            ),
            0.0,
        )

    def test_end_before_start_raises(self):
        with self.assertRaises(ValueError):
            TimeCalculator.calculate_duration(
                "2026-03-01T12:00:00", "2026-03-01T09:00:00"
            )

    def test_overnight_duration(self):
        self.assertEqual(
            TimeCalculator.calculate_duration(
                "2026-03-01T22:00:00", "2026-03-02T02:00:00"
            ),
            4.0,
        )


class TestTotalHours(unittest.TestCase):
    def test_total_hours(self):
        logs = _sample_time_logs()
        # 2.5 + 2.0 + 4.0 = 8.5
        self.assertEqual(TimeCalculator.calculate_total_hours(logs), 8.5)

    def test_empty_logs(self):
        self.assertEqual(TimeCalculator.calculate_total_hours([]), 0.0)


class TestBillableHours(unittest.TestCase):
    def test_billable_only(self):
        logs = _sample_time_logs()
        # billable: 2.5 + 4.0 = 6.5
        self.assertEqual(TimeCalculator.calculate_billable_hours(logs, True), 6.5)

    def test_all_hours(self):
        logs = _sample_time_logs()
        self.assertEqual(TimeCalculator.calculate_billable_hours(logs, False), 8.5)


class TestProjectCost(unittest.TestCase):
    def test_cost_calculation(self):
        self.assertEqual(TimeCalculator.calculate_project_cost(8.5, 50), 425.0)

    def test_cost_rounding(self):
        self.assertEqual(TimeCalculator.calculate_project_cost(1.333, 75), 99.97)


class TestFormatDuration(unittest.TestCase):
    def test_whole_hours(self):
        self.assertEqual(TimeCalculator.format_duration(3.0), "3h 0m")

    def test_fractional_hours(self):
        self.assertEqual(TimeCalculator.format_duration(2.5), "2h 30m")

    def test_zero_hours(self):
        self.assertEqual(TimeCalculator.format_duration(0), "0h 0m")

    def test_minutes_only(self):
        self.assertEqual(TimeCalculator.format_duration(0.25), "0h 15m")


class TestDailyBreakdown(unittest.TestCase):
    def test_daily_totals(self):
        logs = _sample_time_logs()
        breakdown = TimeCalculator.get_daily_breakdown(logs)
        self.assertEqual(breakdown["2026-03-01"], 4.5)  # 2.5 + 2.0
        self.assertEqual(breakdown["2026-03-02"], 4.0)


# ===========================================================================
# InvoiceGenerator tests
# ===========================================================================

class TestInvoiceNumber(unittest.TestCase):
    def test_format(self):
        num = InvoiceGenerator.generate_invoice_number()
        self.assertTrue(re.match(r"^INV-\d{8}-\d{4}$", num))

    def test_uniqueness(self):
        numbers = {InvoiceGenerator.generate_invoice_number() for _ in range(50)}
        # Very likely all unique (random 4 digits)
        self.assertGreater(len(numbers), 1)


class TestLineItems(unittest.TestCase):
    def test_line_item_count(self):
        items = InvoiceGenerator.calculate_line_items(_sample_time_logs(), 50)
        self.assertEqual(len(items), 3)

    def test_line_item_fields(self):
        items = InvoiceGenerator.calculate_line_items(_sample_time_logs(), 50)
        for item in items:
            self.assertIn("date", item)
            self.assertIn("description", item)
            self.assertIn("hours", item)
            self.assertIn("rate", item)
            self.assertIn("amount", item)

    def test_line_item_amount(self):
        items = InvoiceGenerator.calculate_line_items(_sample_time_logs(), 50)
        # First log: 2.5h * 50 = 125
        self.assertEqual(items[0]["amount"], 125.0)


class TestGenerateInvoice(unittest.TestCase):
    def test_invoice_structure(self):
        inv = InvoiceGenerator.generate_invoice(
            _sample_client(), _sample_project(), _sample_time_logs(), 50, tax_rate=10
        )
        self.assertIn("invoiceNumber", inv)
        self.assertIn("lineItems", inv)
        self.assertIn("subtotal", inv)
        self.assertIn("tax", inv)
        self.assertIn("total", inv)

    def test_invoice_totals(self):
        inv = InvoiceGenerator.generate_invoice(
            _sample_client(), _sample_project(), _sample_time_logs(), 50, tax_rate=10
        )
        # subtotal = 2.5*50 + 2*50 + 4*50 = 125+100+200 = 425
        self.assertEqual(inv["subtotal"], 425.0)
        self.assertEqual(inv["tax"], 42.5)
        self.assertEqual(inv["total"], 467.5)

    def test_invoice_dates(self):
        inv = InvoiceGenerator.generate_invoice(
            _sample_client(), _sample_project(), _sample_time_logs(), 50
        )
        issued = datetime.strptime(inv["issuedDate"], "%Y-%m-%d")
        due = datetime.strptime(inv["dueDate"], "%Y-%m-%d")
        self.assertEqual((due - issued).days, 30)


class TestDiscount(unittest.TestCase):
    def test_discount_applied(self):
        inv = InvoiceGenerator.generate_invoice(
            _sample_client(), _sample_project(), _sample_time_logs(), 50, tax_rate=0
        )
        discounted = InvoiceGenerator.apply_discount(inv, 10)
        # 425 - 10% = 382.5
        self.assertEqual(discounted["subtotal"], 382.5)
        self.assertEqual(discounted["discountAmount"], 42.5)
        self.assertEqual(discounted["total"], 382.5)

    def test_discount_with_tax(self):
        inv = InvoiceGenerator.generate_invoice(
            _sample_client(), _sample_project(), _sample_time_logs(), 50, tax_rate=20
        )
        discounted = InvoiceGenerator.apply_discount(inv, 10)
        # subtotal after discount: 425 - 42.5 = 382.5; tax 20%: 76.5; total: 459
        self.assertEqual(discounted["subtotal"], 382.5)
        self.assertEqual(discounted["tax"], 76.5)
        self.assertEqual(discounted["total"], 459.0)


class TestInvoiceFormatting(unittest.TestCase):
    def test_text_format(self):
        inv = InvoiceGenerator.generate_invoice(
            _sample_client(), _sample_project(), _sample_time_logs(), 50
        )
        text = InvoiceGenerator.format_invoice_text(inv)
        self.assertIn("INVOICE", text)
        self.assertIn(inv["invoiceNumber"], text)
        self.assertIn("Jane Doe", text)

    def test_html_format(self):
        inv = InvoiceGenerator.generate_invoice(
            _sample_client(), _sample_project(), _sample_time_logs(), 50
        )
        html = InvoiceGenerator.format_invoice_html(inv)
        self.assertIn("<html>", html)
        self.assertIn(inv["invoiceNumber"], html)


# ===========================================================================
# InvoiceValidator tests
# ===========================================================================

class TestValidateClient(unittest.TestCase):
    def test_valid_client(self):
        valid, errors = InvoiceValidator.validate_client(_sample_client())
        self.assertTrue(valid)
        self.assertEqual(errors, [])

    def test_missing_name(self):
        valid, errors = InvoiceValidator.validate_client({"email": "a@b.com"})
        self.assertFalse(valid)
        self.assertTrue(any("name" in e.lower() for e in errors))

    def test_invalid_email(self):
        valid, errors = InvoiceValidator.validate_client(
            {"name": "X", "email": "not-an-email"}
        )
        self.assertFalse(valid)
        self.assertTrue(any("email" in e.lower() for e in errors))


class TestValidateProject(unittest.TestCase):
    def test_valid_project(self):
        valid, errors = InvoiceValidator.validate_project(_sample_project())
        self.assertTrue(valid)

    def test_negative_rate(self):
        valid, errors = InvoiceValidator.validate_project(
            {"name": "P", "hourlyRate": -10, "client": "C"}
        )
        self.assertFalse(valid)

    def test_missing_client(self):
        valid, errors = InvoiceValidator.validate_project(
            {"name": "P", "hourlyRate": 50}
        )
        self.assertFalse(valid)


class TestValidateTimeLog(unittest.TestCase):
    def test_valid_log(self):
        valid, errors = InvoiceValidator.validate_time_log(
            {"startTime": "2026-03-01T09:00:00", "endTime": "2026-03-01T10:00:00", "description": "Work"}
        )
        self.assertTrue(valid)

    def test_end_before_start(self):
        valid, errors = InvoiceValidator.validate_time_log(
            {"startTime": "2026-03-01T12:00:00", "endTime": "2026-03-01T09:00:00", "description": "Work"}
        )
        self.assertFalse(valid)

    def test_missing_description(self):
        valid, errors = InvoiceValidator.validate_time_log(
            {"startTime": "2026-03-01T09:00:00", "endTime": "2026-03-01T10:00:00"}
        )
        self.assertFalse(valid)


class TestSanitizeInput(unittest.TestCase):
    def test_strip_tags(self):
        self.assertEqual(
            InvoiceValidator.sanitize_input("<b>Hello</b> <script>alert(1)</script>World"),
            "Hello alert(1)World",
        )


class TestValidateHourlyRate(unittest.TestCase):
    def test_valid_rate(self):
        valid, _ = InvoiceValidator.validate_hourly_rate(50)
        self.assertTrue(valid)

    def test_zero_rate(self):
        valid, _ = InvoiceValidator.validate_hourly_rate(0)
        self.assertFalse(valid)

    def test_string_rate(self):
        valid, _ = InvoiceValidator.validate_hourly_rate("abc")
        self.assertFalse(valid)


# ===========================================================================
# ReportFormatter tests
# ===========================================================================

class TestCSVExport(unittest.TestCase):
    def test_csv_header(self):
        csv_str = ReportFormatter.to_csv(_sample_time_logs())
        first_line = csv_str.strip().split("\n")[0].strip("\r")
        self.assertEqual(first_line, "date,project,description,hours,billable")

    def test_csv_row_count(self):
        csv_str = ReportFormatter.to_csv(_sample_time_logs())
        lines = csv_str.strip().split("\n")
        # header + 3 data rows
        self.assertEqual(len(lines), 4)


class TestWeeklyReport(unittest.TestCase):
    def test_contains_total(self):
        report = ReportFormatter.format_weekly_report(_sample_time_logs(), 50)
        self.assertIn("Total", report)

    def test_contains_week_key(self):
        report = ReportFormatter.format_weekly_report(_sample_time_logs(), 50)
        # 2026-03-01 is in week 9
        self.assertIn("2026-W09", report)


class TestProjectSummary(unittest.TestCase):
    def test_summary_content(self):
        summary = ReportFormatter.format_project_summary(_sample_project(), _sample_time_logs())
        self.assertIn("ProjectA", summary)
        self.assertIn("$425.00", summary)


class TestClientStatement(unittest.TestCase):
    def test_statement_structure(self):
        inv = InvoiceGenerator.generate_invoice(
            _sample_client(), _sample_project(), _sample_time_logs(), 50
        )
        stmt = ReportFormatter.format_client_statement(_sample_client(), [inv])
        self.assertIn("CLIENT STATEMENT", stmt)
        self.assertIn("Jane Doe", stmt)


if __name__ == "__main__":
    unittest.main()
