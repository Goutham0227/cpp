"""
Report formatting utilities.
"""

import csv
import io
from datetime import datetime
from collections import defaultdict

from invoice_engine.calculator import TimeCalculator


class ReportFormatter:
    """Formats time tracking data into various report formats."""

    @staticmethod
    def format_project_summary(project, time_logs):
        """
        Generate a text summary for a project.

        Args:
            project (dict): Project info with name, hourlyRate.
            time_logs (list): Time log entries.

        Returns:
            str: Formatted project summary text.
        """
        total_hours = TimeCalculator.calculate_total_hours(time_logs)
        rate = project.get("hourlyRate", 0)
        total_cost = TimeCalculator.calculate_project_cost(total_hours, rate)
        billable = TimeCalculator.calculate_billable_hours(time_logs, billable_only=True)
        formatted = TimeCalculator.format_duration(total_hours)

        lines = [
            "=" * 40,
            f"Project Summary: {project.get('name', 'N/A')}",
            "=" * 40,
            f"Total Hours:    {formatted} ({total_hours}h)",
            f"Billable Hours: {billable}h",
            f"Hourly Rate:    ${rate:.2f}",
            f"Total Cost:     ${total_cost:.2f}",
            "=" * 40,
        ]
        return "\n".join(lines)

    @staticmethod
    def format_weekly_report(time_logs, hourly_rate):
        """
        Generate a weekly breakdown report.

        Args:
            time_logs (list): Time log entries.
            hourly_rate (float): Billing rate per hour.

        Returns:
            str: Weekly breakdown text.
        """
        weekly = defaultdict(float)
        for log in time_logs:
            start = datetime.fromisoformat(log["startTime"])
            # ISO calendar: year, week number, weekday
            year, week, _ = start.isocalendar()
            week_key = f"{year}-W{week:02d}"
            duration = TimeCalculator.calculate_duration(
                log["startTime"], log["endTime"]
            )
            weekly[week_key] += duration

        lines = [
            "=" * 40,
            "Weekly Time Report",
            "=" * 40,
            f"{'Week':<12} {'Hours':>8} {'Cost':>12}",
            "-" * 40,
        ]
        grand_total_hours = 0.0
        for week_key in sorted(weekly.keys()):
            hours = round(weekly[week_key], 2)
            cost = round(hours * hourly_rate, 2)
            grand_total_hours += hours
            lines.append(f"{week_key:<12} {hours:>8.2f} ${cost:>11.2f}")

        grand_cost = round(grand_total_hours * hourly_rate, 2)
        lines.append("-" * 40)
        lines.append(f"{'Total':<12} {grand_total_hours:>8.2f} ${grand_cost:>11.2f}")
        lines.append("=" * 40)
        return "\n".join(lines)

    @staticmethod
    def to_csv(time_logs):
        """
        Convert time logs to CSV format.

        Args:
            time_logs (list): Time log entries.

        Returns:
            str: CSV string with header: date,project,description,hours,billable
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["date", "project", "description", "hours", "billable"])

        for log in time_logs:
            start = datetime.fromisoformat(log["startTime"])
            date_str = start.strftime("%Y-%m-%d")
            hours = TimeCalculator.calculate_duration(
                log["startTime"], log["endTime"]
            )
            writer.writerow([
                date_str,
                log.get("project", ""),
                log.get("description", ""),
                hours,
                log.get("billable", False),
            ])

        return output.getvalue()

    @staticmethod
    def format_client_statement(client, invoices):
        """
        Generate a statement showing all invoices for a client.

        Args:
            client (dict): Client info.
            invoices (list): List of invoice dicts.

        Returns:
            str: Formatted client statement text.
        """
        lines = [
            "=" * 55,
            "CLIENT STATEMENT",
            "=" * 55,
            f"Client:  {client.get('name', 'N/A')}",
        ]
        if client.get("company"):
            lines.append(f"Company: {client['company']}")
        lines.append(f"Email:   {client.get('email', 'N/A')}")
        lines.append("")
        lines.append(f"{'Invoice #':<20} {'Date':<12} {'Due':<12} {'Total':>10}")
        lines.append("-" * 55)

        grand_total = 0.0
        for inv in invoices:
            grand_total += inv.get("total", 0)
            lines.append(
                f"{inv['invoiceNumber']:<20} {inv['issuedDate']:<12} "
                f"{inv['dueDate']:<12} {inv['total']:>10.2f}"
            )

        lines.append("-" * 55)
        lines.append(f"{'Total Outstanding:':>44} {grand_total:>10.2f}")
        lines.append("=" * 55)
        return "\n".join(lines)
