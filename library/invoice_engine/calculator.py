"""
Time calculation utilities for freelancer time tracking.
"""

from datetime import datetime
from collections import defaultdict


class TimeCalculator:
    """Handles all time-related calculations for freelancer billing."""

    @staticmethod
    def calculate_duration(start_time, end_time):
        """
        Calculate duration between two ISO datetime strings in hours.

        Args:
            start_time (str): ISO format datetime string (e.g., "2026-03-01T09:00:00").
            end_time (str): ISO format datetime string.

        Returns:
            float: Duration in hours, rounded to 2 decimal places.

        Raises:
            ValueError: If end_time is before start_time or strings are invalid.
        """
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        if end < start:
            raise ValueError("end_time must be after start_time")
        delta = end - start
        hours = delta.total_seconds() / 3600
        return round(hours, 2)

    @staticmethod
    def calculate_total_hours(time_logs):
        """
        Sum all durations from a list of time log dicts.

        Args:
            time_logs (list): List of dicts with 'startTime' and 'endTime' keys.

        Returns:
            float: Total hours, rounded to 2 decimal places.
        """
        total = 0.0
        for log in time_logs:
            total += TimeCalculator.calculate_duration(
                log["startTime"], log["endTime"]
            )
        return round(total, 2)

    @staticmethod
    def calculate_billable_hours(time_logs, billable_only=True):
        """
        Filter logs by billable status and sum hours.

        Args:
            time_logs (list): List of time log dicts with 'billable' key.
            billable_only (bool): If True, only sum billable entries.

        Returns:
            float: Total billable (or all) hours, rounded to 2 decimal places.
        """
        if billable_only:
            filtered = [log for log in time_logs if log.get("billable", False)]
        else:
            filtered = time_logs
        return TimeCalculator.calculate_total_hours(filtered)

    @staticmethod
    def calculate_project_cost(hours, hourly_rate):
        """
        Calculate project cost from hours and rate.

        Args:
            hours (float): Number of hours worked.
            hourly_rate (float): Rate per hour.

        Returns:
            float: Total cost, rounded to 2 decimal places.
        """
        return round(hours * hourly_rate, 2)

    @staticmethod
    def format_duration(hours):
        """
        Format a decimal hours value into 'Xh Ym' string.

        Args:
            hours (float): Duration in hours.

        Returns:
            str: Formatted string, e.g., '2h 30m'.
        """
        total_minutes = round(hours * 60)
        h = total_minutes // 60
        m = total_minutes % 60
        return f"{h}h {m}m"

    @staticmethod
    def get_daily_breakdown(time_logs):
        """
        Calculate total hours per day from time logs.

        Args:
            time_logs (list): List of time log dicts.

        Returns:
            dict: Mapping of date string (YYYY-MM-DD) to total hours.
        """
        daily = defaultdict(float)
        for log in time_logs:
            start = datetime.fromisoformat(log["startTime"])
            date_key = start.strftime("%Y-%m-%d")
            duration = TimeCalculator.calculate_duration(
                log["startTime"], log["endTime"]
            )
            daily[date_key] += duration
        # Round each day's total
        return {k: round(v, 2) for k, v in daily.items()}
