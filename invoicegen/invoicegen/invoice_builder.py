"""
Builder pattern for constructing invoices from time entries.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from .models import Invoice, LineItem, TimeEntry, Client, InvoiceStatus
from .tax import TaxCalculator, TaxRate
from .formatter import CurrencyFormatter


class InvoiceBuilder:
    """
    Fluent builder for constructing invoices from time entries.
    Supports grouping entries, applying tax, and setting terms.
    """

    def __init__(self):
        self._client_id: Optional[str] = None
        self._entries: List[TimeEntry] = []
        self._tax_rate: Optional[TaxRate] = None
        self._due_days: int = 30
        self._currency: str = "EUR"
        self._notes: str = ""
        self._invoice_number: Optional[str] = None
        self._group_by_project: bool = False
        self._custom_line_items: List[LineItem] = []

    def set_client(self, client_id: str) -> "InvoiceBuilder":
        """Set the client for this invoice."""
        self._client_id = client_id
        return self

    def add_time_entries(self, entries: List[TimeEntry]) -> "InvoiceBuilder":
        """Add time entries to convert into line items."""
        self._entries.extend(entries)
        return self

    def add_time_entry(self, entry: TimeEntry) -> "InvoiceBuilder":
        """Add a single time entry."""
        self._entries.append(entry)
        return self

    def add_custom_line_item(self, description: str, quantity: float,
                              unit_price: float) -> "InvoiceBuilder":
        """Add a custom line item not derived from time entries."""
        self._custom_line_items.append(LineItem(description, quantity, unit_price))
        return self

    def set_tax_rate(self, tax_rate: TaxRate) -> "InvoiceBuilder":
        """Set the tax rate for this invoice."""
        self._tax_rate = tax_rate
        return self

    def set_due_days(self, days: int) -> "InvoiceBuilder":
        """Set payment terms in days."""
        self._due_days = days
        return self

    def set_currency(self, currency: str) -> "InvoiceBuilder":
        """Set the currency code."""
        self._currency = currency
        return self

    def set_notes(self, notes: str) -> "InvoiceBuilder":
        """Set invoice notes."""
        self._notes = notes
        return self

    def set_invoice_number(self, number: str) -> "InvoiceBuilder":
        """Set a custom invoice number."""
        self._invoice_number = number
        return self

    def group_by_project(self, group: bool = True) -> "InvoiceBuilder":
        """Group time entries by project into single line items."""
        self._group_by_project = group
        return self

    def build(self) -> Invoice:
        """
        Build the invoice from configured options.
        Raises ValueError if client is not set.
        """
        if not self._client_id:
            raise ValueError("Client ID must be set before building invoice")

        invoice = Invoice(
            client_id=self._client_id,
            invoice_number=self._invoice_number,
            due_date=datetime.utcnow() + timedelta(days=self._due_days),
            currency=self._currency,
        )

        # Add line items from time entries
        if self._group_by_project and self._entries:
            self._add_grouped_entries(invoice)
        else:
            for entry in self._entries:
                if entry.end_time is not None:
                    item = LineItem(
                        description=entry.description or "Time entry",
                        quantity=round(entry.duration_hours, 2),
                        unit_price=entry.hourly_rate,
                    )
                    invoice.add_line_item(item)

        # Add custom line items
        for item in self._custom_line_items:
            invoice.add_line_item(item)

        # Apply tax
        if self._tax_rate:
            invoice.tax_rate = self._tax_rate.rate
            invoice.tax_amount = self._tax_rate.calculate_tax(invoice.subtotal)

        invoice.notes = self._notes

        return invoice

    def _add_grouped_entries(self, invoice: Invoice) -> None:
        """Group entries by project and create combined line items."""
        project_groups = {}
        for entry in self._entries:
            if entry.end_time is None:
                continue
            pid = entry.project_id
            if pid not in project_groups:
                project_groups[pid] = {
                    "hours": 0.0,
                    "rate": entry.hourly_rate,
                    "descriptions": [],
                }
            project_groups[pid]["hours"] += entry.duration_hours
            if entry.description:
                project_groups[pid]["descriptions"].append(entry.description)

        for pid, group in project_groups.items():
            desc = f"Project {pid}: " + ", ".join(group["descriptions"][:3])
            if len(group["descriptions"]) > 3:
                desc += f" (+{len(group['descriptions']) - 3} more)"
            item = LineItem(
                description=desc,
                quantity=round(group["hours"], 2),
                unit_price=group["rate"],
            )
            invoice.add_line_item(item)
