"""
Formatting utilities for currencies and invoice display.
"""

from typing import Dict, Optional
from .models import Invoice, InvoiceStatus


class CurrencyFormatter:
    """Formats monetary amounts with currency symbols and locale conventions."""

    SYMBOLS = {
        "EUR": "\u20ac",
        "USD": "$",
        "GBP": "\u00a3",
        "JPY": "\u00a5",
        "CHF": "CHF",
        "CAD": "C$",
        "AUD": "A$",
        "INR": "\u20b9",
    }

    DECIMAL_PLACES = {
        "JPY": 0,
    }

    def __init__(self, default_currency: str = "EUR"):
        self.default_currency = default_currency

    def format(self, amount: float, currency: str = None) -> str:
        """Format an amount with currency symbol."""
        curr = currency or self.default_currency
        symbol = self.SYMBOLS.get(curr, curr + " ")
        decimals = self.DECIMAL_PLACES.get(curr, 2)

        if decimals == 0:
            formatted = f"{symbol}{int(round(amount)):,}"
        else:
            formatted = f"{symbol}{amount:,.{decimals}f}"

        return formatted

    def format_with_code(self, amount: float, currency: str = None) -> str:
        """Format amount with both symbol and currency code."""
        curr = currency or self.default_currency
        return f"{self.format(amount, curr)} {curr}"


class InvoiceFormatter:
    """Formats invoice data for display or export."""

    def __init__(self, currency_formatter: CurrencyFormatter = None):
        self.currency = currency_formatter or CurrencyFormatter()

    def format_invoice_summary(self, invoice: Invoice) -> str:
        """Generate a text summary of an invoice."""
        lines = [
            f"Invoice: {invoice.invoice_number}",
            f"Status: {invoice.status.value.upper()}",
            f"Date: {invoice.created_at.strftime('%Y-%m-%d')}",
            f"Due: {invoice.due_date.strftime('%Y-%m-%d')}",
            "",
            "Line Items:",
            "-" * 60,
        ]

        for item in invoice.line_items:
            amount_str = self.currency.format(item.subtotal, invoice.currency)
            lines.append(
                f"  {item.description:<30} {item.quantity:>8.2f} hrs x "
                f"{self.currency.format(item.unit_price, invoice.currency)} = {amount_str}"
            )

        lines.append("-" * 60)
        lines.append(f"  {'Subtotal:':<40} {self.currency.format(invoice.subtotal, invoice.currency):>18}")
        if invoice.tax_amount > 0:
            lines.append(f"  {'Tax (' + str(invoice.tax_rate) + '%):':<40} {self.currency.format(invoice.tax_amount, invoice.currency):>18}")
        lines.append(f"  {'TOTAL:':<40} {self.currency.format(invoice.total, invoice.currency):>18}")

        if invoice.notes:
            lines.append("")
            lines.append(f"Notes: {invoice.notes}")

        return "\n".join(lines)

    def format_status_badge(self, status: InvoiceStatus) -> str:
        """Return a text badge for invoice status."""
        badges = {
            InvoiceStatus.DRAFT: "[DRAFT]",
            InvoiceStatus.SENT: "[SENT]",
            InvoiceStatus.PAID: "[PAID]",
            InvoiceStatus.OVERDUE: "[OVERDUE]",
            InvoiceStatus.CANCELLED: "[CANCELLED]",
        }
        return badges.get(status, "[UNKNOWN]")

    def format_line_items_table(self, invoice: Invoice) -> list:
        """Format line items as a list of dicts for table display."""
        rows = []
        for item in invoice.line_items:
            rows.append({
                "description": item.description,
                "hours": round(item.quantity, 2),
                "rate": self.currency.format(item.unit_price, invoice.currency),
                "amount": self.currency.format(item.subtotal, invoice.currency),
            })
        return rows
