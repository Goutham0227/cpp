"""
Time and billing calculation utilities.

Provides TimeCalculator for time summaries and BillingCalculator for billing totals.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .models import TimeEntry, Invoice, InvoiceStatus


class TimeCalculator:
    """Calculates time summaries from time entries."""

    @staticmethod
    def total_hours(entries: List[TimeEntry]) -> float:
        """Calculate total hours across all entries."""
        return round(sum(e.duration_hours for e in entries), 4)

    @staticmethod
    def total_billable_amount(entries: List[TimeEntry]) -> float:
        """Calculate total billable amount across all entries."""
        return round(sum(e.total_amount for e in entries), 2)

    @staticmethod
    def weekly_summary(entries: List[TimeEntry], week_start: datetime = None) -> Dict[str, float]:
        """
        Generate a weekly summary of hours per day.
        Returns dict mapping day names to hours.
        """
        if week_start is None:
            today = datetime.utcnow().date()
            week_start = today - timedelta(days=today.weekday())
        elif hasattr(week_start, 'date'):
            week_start = week_start.date()

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        summary = {day: 0.0 for day in days}

        for entry in entries:
            if entry.end_time is None:
                continue
            entry_date = entry.start_time.date()
            week_end = week_start + timedelta(days=6)
            if week_start <= entry_date <= week_end:
                day_name = days[entry_date.weekday()]
                summary[day_name] += entry.duration_hours

        # Round values
        summary = {k: round(v, 4) for k, v in summary.items()}
        return summary

    @staticmethod
    def monthly_summary(entries: List[TimeEntry], year: int, month: int) -> Dict[str, float]:
        """
        Generate a monthly summary with total hours, billable amount, and daily breakdown.
        """
        monthly_entries = []
        for entry in entries:
            if entry.end_time is None:
                continue
            if entry.start_time.year == year and entry.start_time.month == month:
                monthly_entries.append(entry)

        daily_hours: Dict[int, float] = {}
        for entry in monthly_entries:
            day = entry.start_time.day
            daily_hours[day] = daily_hours.get(day, 0.0) + entry.duration_hours

        total_hrs = sum(e.duration_hours for e in monthly_entries)
        total_amt = sum(e.total_amount for e in monthly_entries)

        return {
            "year": year,
            "month": month,
            "total_hours": round(total_hrs, 4),
            "total_amount": round(total_amt, 2),
            "num_entries": len(monthly_entries),
            "daily_hours": {str(k): round(v, 4) for k, v in sorted(daily_hours.items())},
        }

    @staticmethod
    def entries_by_project(entries: List[TimeEntry]) -> Dict[str, List[TimeEntry]]:
        """Group time entries by project ID."""
        grouped: Dict[str, List[TimeEntry]] = {}
        for entry in entries:
            if entry.project_id not in grouped:
                grouped[entry.project_id] = []
            grouped[entry.project_id].append(entry)
        return grouped

    @staticmethod
    def average_daily_hours(entries: List[TimeEntry]) -> float:
        """Calculate average hours worked per day with entries."""
        if not entries:
            return 0.0
        days_with_entries = set()
        total_hours = 0.0
        for entry in entries:
            if entry.end_time is None:
                continue
            days_with_entries.add(entry.start_time.date())
            total_hours += entry.duration_hours
        if not days_with_entries:
            return 0.0
        return round(total_hours / len(days_with_entries), 4)


class BillingCalculator:
    """Calculates billing summaries and overdue detection."""

    @staticmethod
    def client_billing_summary(invoices: List[Invoice], client_id: str) -> Dict:
        """
        Generate billing summary for a specific client.
        Includes totals by status and overall amounts.
        """
        client_invoices = [inv for inv in invoices if inv.client_id == client_id]

        total_billed = sum(inv.total for inv in client_invoices)
        total_paid = sum(inv.total for inv in client_invoices if inv.status == InvoiceStatus.PAID)
        total_outstanding = sum(
            inv.total for inv in client_invoices
            if inv.status in (InvoiceStatus.SENT, InvoiceStatus.OVERDUE)
        )
        total_overdue = sum(
            inv.total for inv in client_invoices
            if inv.status == InvoiceStatus.OVERDUE or (inv.is_overdue and inv.status != InvoiceStatus.PAID)
        )

        return {
            "client_id": client_id,
            "total_invoices": len(client_invoices),
            "total_billed": round(total_billed, 2),
            "total_paid": round(total_paid, 2),
            "total_outstanding": round(total_outstanding, 2),
            "total_overdue": round(total_overdue, 2),
        }

    @staticmethod
    def find_overdue_invoices(invoices: List[Invoice]) -> List[Invoice]:
        """Find all invoices that are past their due date and unpaid."""
        overdue = []
        now = datetime.utcnow()
        for inv in invoices:
            if inv.status == InvoiceStatus.PAID or inv.status == InvoiceStatus.CANCELLED:
                continue
            if now > inv.due_date:
                overdue.append(inv)
        return overdue

    @staticmethod
    def revenue_by_month(invoices: List[Invoice]) -> Dict[str, float]:
        """Calculate revenue (paid invoices) grouped by month."""
        monthly: Dict[str, float] = {}
        for inv in invoices:
            if inv.status == InvoiceStatus.PAID:
                key = inv.created_at.strftime("%Y-%m")
                monthly[key] = monthly.get(key, 0.0) + inv.total
        return {k: round(v, 2) for k, v in sorted(monthly.items())}
