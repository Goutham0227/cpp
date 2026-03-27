"""
Input validation utilities for invoice data.
"""

import re
from datetime import datetime


class InvoiceValidator:
    """Validates client, project, and time log data."""

    @staticmethod
    def validate_client(data):
        """
        Validate client data.

        Args:
            data (dict): Client dict with name, email, and optional company.

        Returns:
            tuple: (is_valid: bool, errors: list of str)
        """
        errors = []

        if not data.get("name") or not str(data["name"]).strip():
            errors.append("Client name is required")

        email = data.get("email", "")
        if not email or not str(email).strip():
            errors.append("Client email is required")
        elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email)):
            errors.append("Client email is invalid")

        # company is optional — no validation needed

        return (len(errors) == 0, errors)

    @staticmethod
    def validate_project(data):
        """
        Validate project data.

        Args:
            data (dict): Project dict with name, hourlyRate, client.

        Returns:
            tuple: (is_valid: bool, errors: list of str)
        """
        errors = []

        if not data.get("name") or not str(data["name"]).strip():
            errors.append("Project name is required")

        rate = data.get("hourlyRate")
        if rate is None:
            errors.append("Hourly rate is required")
        else:
            valid, rate_errors = InvoiceValidator.validate_hourly_rate(rate)
            if not valid:
                errors.extend(rate_errors)

        if not data.get("client"):
            errors.append("Client is required")

        return (len(errors) == 0, errors)

    @staticmethod
    def validate_time_log(data):
        """
        Validate a time log entry.

        Args:
            data (dict): Time log dict with startTime, endTime, description.

        Returns:
            tuple: (is_valid: bool, errors: list of str)
        """
        errors = []

        start_str = data.get("startTime")
        end_str = data.get("endTime")

        if not start_str:
            errors.append("Start time is required")
        if not end_str:
            errors.append("End time is required")

        if start_str and end_str:
            try:
                start = datetime.fromisoformat(start_str)
                end = datetime.fromisoformat(end_str)
                if end <= start:
                    errors.append("End time must be after start time")
            except (ValueError, TypeError):
                errors.append("Invalid datetime format; use ISO format")

        if not data.get("description") or not str(data["description"]).strip():
            errors.append("Description is required")

        return (len(errors) == 0, errors)

    @staticmethod
    def sanitize_input(text):
        """
        Strip HTML tags from text.

        Args:
            text (str): Input text possibly containing HTML.

        Returns:
            str: Text with HTML tags removed.
        """
        return re.sub(r"<[^>]+>", "", str(text))

    @staticmethod
    def validate_hourly_rate(rate):
        """
        Validate that the hourly rate is a positive number.

        Args:
            rate: Value to validate.

        Returns:
            tuple: (is_valid: bool, errors: list of str)
        """
        errors = []
        try:
            rate_val = float(rate)
            if rate_val <= 0:
                errors.append("Hourly rate must be a positive number")
        except (ValueError, TypeError):
            errors.append("Hourly rate must be a valid number")

        return (len(errors) == 0, errors)
