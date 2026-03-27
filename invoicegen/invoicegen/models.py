"""
Core data models for the invoicegen library.

Provides OOP classes for Client, Project, TimeEntry, Invoice, and LineItem.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional
import uuid


class InvoiceStatus(Enum):
    """Enumeration of possible invoice statuses."""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Client:
    """Represents a freelancer's client with billing information."""

    def __init__(self, name: str, email: str, company: str = "",
                 address: str = "", phone: str = "", client_id: str = None):
        self.client_id = client_id or str(uuid.uuid4())
        self.name = name
        self.email = email
        self.company = company
        self.address = address
        self.phone = phone
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Serialize client to dictionary."""
        return {
            "client_id": self.client_id,
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "address": self.address,
            "phone": self.phone,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Client":
        """Deserialize client from dictionary."""
        client = cls(
            name=data["name"],
            email=data["email"],
            company=data.get("company", ""),
            address=data.get("address", ""),
            phone=data.get("phone", ""),
            client_id=data.get("client_id"),
        )
        if "created_at" in data:
            client.created_at = datetime.fromisoformat(data["created_at"])
        return client

    def __repr__(self) -> str:
        return f"Client(name='{self.name}', company='{self.company}')"


class Project:
    """Represents a project associated with a client."""

    def __init__(self, name: str, client_id: str, description: str = "",
                 hourly_rate: float = 0.0, project_id: str = None):
        self.project_id = project_id or str(uuid.uuid4())
        self.name = name
        self.client_id = client_id
        self.description = description
        self.hourly_rate = hourly_rate
        self.is_active = True
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Serialize project to dictionary."""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "client_id": self.client_id,
            "description": self.description,
            "hourly_rate": self.hourly_rate,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """Deserialize project from dictionary."""
        project = cls(
            name=data["name"],
            client_id=data["client_id"],
            description=data.get("description", ""),
            hourly_rate=data.get("hourly_rate", 0.0),
            project_id=data.get("project_id"),
        )
        project.is_active = data.get("is_active", True)
        if "created_at" in data:
            project.created_at = datetime.fromisoformat(data["created_at"])
        return project

    def __repr__(self) -> str:
        return f"Project(name='{self.name}', rate={self.hourly_rate})"


class TimeEntry:
    """Represents a time tracking entry for a project."""

    def __init__(self, project_id: str, description: str = "",
                 start_time: datetime = None, end_time: datetime = None,
                 hourly_rate: float = 0.0, entry_id: str = None):
        self.entry_id = entry_id or str(uuid.uuid4())
        self.project_id = project_id
        self.description = description
        self.start_time = start_time or datetime.utcnow()
        self.end_time = end_time
        self.hourly_rate = hourly_rate

    @property
    def duration_hours(self) -> float:
        """Calculate duration in hours between start and end time."""
        if self.end_time is None:
            return 0.0
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600.0

    @property
    def total_amount(self) -> float:
        """Calculate total billable amount for this entry."""
        return round(self.duration_hours * self.hourly_rate, 2)

    @property
    def is_running(self) -> bool:
        """Check if the timer is currently running."""
        return self.end_time is None

    def stop(self) -> None:
        """Stop the running timer."""
        if self.is_running:
            self.end_time = datetime.utcnow()

    def to_dict(self) -> dict:
        """Serialize time entry to dictionary."""
        return {
            "entry_id": self.entry_id,
            "project_id": self.project_id,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "hourly_rate": self.hourly_rate,
            "duration_hours": round(self.duration_hours, 4),
            "total_amount": self.total_amount,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimeEntry":
        """Deserialize time entry from dictionary."""
        entry = cls(
            project_id=data["project_id"],
            description=data.get("description", ""),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            hourly_rate=data.get("hourly_rate", 0.0),
            entry_id=data.get("entry_id"),
        )
        return entry

    def __repr__(self) -> str:
        return f"TimeEntry(desc='{self.description}', hours={self.duration_hours:.2f})"


class LineItem:
    """Represents a single line item on an invoice."""

    def __init__(self, description: str, quantity: float, unit_price: float,
                 item_id: str = None):
        self.item_id = item_id or str(uuid.uuid4())
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price

    @property
    def subtotal(self) -> float:
        """Calculate line item subtotal."""
        return round(self.quantity * self.unit_price, 2)

    def to_dict(self) -> dict:
        """Serialize line item to dictionary."""
        return {
            "item_id": self.item_id,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": self.subtotal,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LineItem":
        """Deserialize line item from dictionary."""
        return cls(
            description=data["description"],
            quantity=data["quantity"],
            unit_price=data["unit_price"],
            item_id=data.get("item_id"),
        )

    def __repr__(self) -> str:
        return f"LineItem(desc='{self.description}', subtotal={self.subtotal})"


class Invoice:
    """Represents a complete invoice with line items and tax."""

    def __init__(self, client_id: str, invoice_number: str = None,
                 invoice_id: str = None, due_date: datetime = None,
                 currency: str = "EUR"):
        self.invoice_id = invoice_id or str(uuid.uuid4())
        self.invoice_number = invoice_number or f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        self.client_id = client_id
        self.line_items: List[LineItem] = []
        self.status = InvoiceStatus.DRAFT
        self.created_at = datetime.utcnow()
        self.due_date = due_date or (datetime.utcnow() + timedelta(days=30))
        self.tax_rate = 0.0
        self.tax_amount = 0.0
        self.currency = currency
        self.notes = ""

    def add_line_item(self, item: LineItem) -> None:
        """Add a line item to the invoice."""
        self.line_items.append(item)

    def remove_line_item(self, item_id: str) -> bool:
        """Remove a line item by ID. Returns True if removed."""
        original_len = len(self.line_items)
        self.line_items = [li for li in self.line_items if li.item_id != item_id]
        return len(self.line_items) < original_len

    @property
    def subtotal(self) -> float:
        """Calculate subtotal before tax."""
        return round(sum(item.subtotal for item in self.line_items), 2)

    @property
    def total(self) -> float:
        """Calculate total including tax."""
        return round(self.subtotal + self.tax_amount, 2)

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if self.status == InvoiceStatus.PAID:
            return False
        return datetime.utcnow() > self.due_date

    def mark_sent(self) -> None:
        """Mark invoice as sent."""
        self.status = InvoiceStatus.SENT

    def mark_paid(self) -> None:
        """Mark invoice as paid."""
        self.status = InvoiceStatus.PAID

    def mark_overdue(self) -> None:
        """Mark invoice as overdue."""
        self.status = InvoiceStatus.OVERDUE

    def to_dict(self) -> dict:
        """Serialize invoice to dictionary."""
        return {
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "client_id": self.client_id,
            "line_items": [item.to_dict() for item in self.line_items],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "due_date": self.due_date.isoformat(),
            "tax_rate": self.tax_rate,
            "tax_amount": self.tax_amount,
            "subtotal": self.subtotal,
            "total": self.total,
            "currency": self.currency,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Invoice":
        """Deserialize invoice from dictionary."""
        invoice = cls(
            client_id=data["client_id"],
            invoice_number=data.get("invoice_number"),
            invoice_id=data.get("invoice_id"),
            currency=data.get("currency", "EUR"),
        )
        invoice.status = InvoiceStatus(data.get("status", "draft"))
        invoice.tax_rate = data.get("tax_rate", 0.0)
        invoice.tax_amount = data.get("tax_amount", 0.0)
        invoice.notes = data.get("notes", "")
        if "created_at" in data:
            invoice.created_at = datetime.fromisoformat(data["created_at"])
        if "due_date" in data:
            invoice.due_date = datetime.fromisoformat(data["due_date"])
        for item_data in data.get("line_items", []):
            invoice.add_line_item(LineItem.from_dict(item_data))
        return invoice

    def __repr__(self) -> str:
        return f"Invoice(number='{self.invoice_number}', total={self.total}, status={self.status.value})"
