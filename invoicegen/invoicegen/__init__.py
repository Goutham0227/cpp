"""
invoicegen - OOP Python library for freelancer invoice generation.

Author: Goutham Uppu (25167936)
Module: Cloud Platform Programming, NCI
"""

from .models import Client, Project, TimeEntry, Invoice, LineItem, InvoiceStatus
from .calculator import TimeCalculator, BillingCalculator
from .invoice_builder import InvoiceBuilder
from .tax import TaxCalculator, TaxRate, TaxType
from .formatter import CurrencyFormatter, InvoiceFormatter

__version__ = "1.0.0"
__author__ = "Goutham Uppu"

__all__ = [
    "Client",
    "Project",
    "TimeEntry",
    "Invoice",
    "LineItem",
    "InvoiceStatus",
    "TimeCalculator",
    "BillingCalculator",
    "InvoiceBuilder",
    "TaxCalculator",
    "TaxRate",
    "TaxType",
    "CurrencyFormatter",
    "InvoiceFormatter",
]
