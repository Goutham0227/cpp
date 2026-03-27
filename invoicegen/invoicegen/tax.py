"""
Tax calculation module supporting multiple tax types and rates.
"""

from enum import Enum
from typing import Dict, Optional


class TaxType(Enum):
    """Supported tax types."""
    VAT = "vat"
    SALES_TAX = "sales_tax"
    GST = "gst"
    NO_TAX = "no_tax"


class TaxRate:
    """Represents a tax rate with type and percentage."""

    # Common predefined rates
    IRELAND_STANDARD = None  # Will be set after class definition
    IRELAND_REDUCED = None
    UK_STANDARD = None
    US_NO_FEDERAL = None
    ZERO_RATE = None

    def __init__(self, name: str, rate: float, tax_type: TaxType = TaxType.VAT):
        if rate < 0 or rate > 100:
            raise ValueError(f"Tax rate must be between 0 and 100, got {rate}")
        self.name = name
        self.rate = rate
        self.tax_type = tax_type

    def calculate_tax(self, amount: float) -> float:
        """Calculate tax amount for a given subtotal."""
        return round(amount * (self.rate / 100.0), 2)

    def calculate_gross(self, net_amount: float) -> float:
        """Calculate gross amount (net + tax)."""
        return round(net_amount + self.calculate_tax(net_amount), 2)

    def extract_tax(self, gross_amount: float) -> float:
        """Extract tax amount from a gross (tax-inclusive) amount."""
        return round(gross_amount - (gross_amount / (1 + self.rate / 100.0)), 2)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "rate": self.rate,
            "tax_type": self.tax_type.value,
        }

    def __repr__(self) -> str:
        return f"TaxRate(name='{self.name}', rate={self.rate}%, type={self.tax_type.value})"


# Predefined common rates
TaxRate.IRELAND_STANDARD = TaxRate("Ireland Standard VAT", 23.0, TaxType.VAT)
TaxRate.IRELAND_REDUCED = TaxRate("Ireland Reduced VAT", 13.5, TaxType.VAT)
TaxRate.UK_STANDARD = TaxRate("UK Standard VAT", 20.0, TaxType.VAT)
TaxRate.US_NO_FEDERAL = TaxRate("US No Federal Tax", 0.0, TaxType.NO_TAX)
TaxRate.ZERO_RATE = TaxRate("Zero Rate", 0.0, TaxType.NO_TAX)


class TaxCalculator:
    """Handles tax calculations for invoices with support for multiple rates."""

    def __init__(self, default_rate: TaxRate = None):
        self.default_rate = default_rate or TaxRate.IRELAND_STANDARD
        self._custom_rates: Dict[str, TaxRate] = {}

    def add_custom_rate(self, key: str, rate: TaxRate) -> None:
        """Register a custom tax rate."""
        self._custom_rates[key] = rate

    def get_rate(self, key: str) -> Optional[TaxRate]:
        """Get a registered custom tax rate by key."""
        return self._custom_rates.get(key)

    def calculate_invoice_tax(self, subtotal: float, rate: TaxRate = None) -> Dict:
        """
        Calculate full tax breakdown for an invoice subtotal.
        Returns dict with subtotal, tax_amount, tax_rate, and total.
        """
        tax_rate = rate or self.default_rate
        tax_amount = tax_rate.calculate_tax(subtotal)
        total = round(subtotal + tax_amount, 2)

        return {
            "subtotal": round(subtotal, 2),
            "tax_rate_name": tax_rate.name,
            "tax_rate_percent": tax_rate.rate,
            "tax_amount": tax_amount,
            "total": total,
        }

    def calculate_multi_rate_tax(self, items: list) -> Dict:
        """
        Calculate tax for items with different rates.
        Each item should be a dict with 'amount' and optionally 'tax_rate' (TaxRate).
        """
        total_subtotal = 0.0
        total_tax = 0.0
        breakdown = []

        for item in items:
            amount = item["amount"]
            rate = item.get("tax_rate", self.default_rate)
            tax = rate.calculate_tax(amount)
            total_subtotal += amount
            total_tax += tax
            breakdown.append({
                "amount": round(amount, 2),
                "tax_rate": rate.name,
                "tax_percent": rate.rate,
                "tax_amount": tax,
            })

        return {
            "subtotal": round(total_subtotal, 2),
            "total_tax": round(total_tax, 2),
            "total": round(total_subtotal + total_tax, 2),
            "breakdown": breakdown,
        }
