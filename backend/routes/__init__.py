"""Flask route blueprints for all CRUD operations."""

from .client_routes import client_bp
from .project_routes import project_bp
from .time_entry_routes import time_entry_bp
from .invoice_routes import invoice_bp
from .aws_routes import aws_bp

__all__ = ["client_bp", "project_bp", "time_entry_bp", "invoice_bp", "aws_bp"]
