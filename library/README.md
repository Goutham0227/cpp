# invoice-engine-nci

A Python library for freelancer time tracking and invoice generation. Built with only the Python standard library -- no external dependencies required.

## Installation

```bash
pip install invoice-engine-nci
```

## Quick Start

```python
from invoice_engine import TimeCalculator, InvoiceGenerator, InvoiceValidator, ReportFormatter

# Define time logs
time_logs = [
    {
        "startTime": "2026-03-01T09:00:00",
        "endTime": "2026-03-01T11:30:00",
        "description": "Backend API development",
        "project": "WebApp",
        "billable": True,
    },
    {
        "startTime": "2026-03-01T13:00:00",
        "endTime": "2026-03-01T15:00:00",
        "description": "Code review",
        "project": "WebApp",
        "billable": False,
    },
]

# Calculate hours
calc = TimeCalculator()
total = calc.calculate_total_hours(time_logs)
billable = calc.calculate_billable_hours(time_logs)
cost = calc.calculate_project_cost(billable, 75.00)

print(f"Total: {calc.format_duration(total)}")
print(f"Billable: {billable}h")
print(f"Cost: ${cost}")

# Generate an invoice
client = {"name": "Jane Doe", "email": "jane@example.com", "company": "Acme Ltd"}
project = {"name": "WebApp", "hourlyRate": 75}

gen = InvoiceGenerator()
invoice = gen.generate_invoice(client, project, time_logs, 75, tax_rate=10)

# Print formatted invoice
print(gen.format_invoice_text(invoice))

# Export time logs to CSV
fmt = ReportFormatter()
print(fmt.to_csv(time_logs))
```

## Modules

### TimeCalculator

- `calculate_duration(start_time, end_time)` -- Duration in hours between two ISO datetime strings.
- `calculate_total_hours(time_logs)` -- Sum of all durations.
- `calculate_billable_hours(time_logs, billable_only=True)` -- Sum of billable durations.
- `calculate_project_cost(hours, hourly_rate)` -- Total cost.
- `format_duration(hours)` -- Format as "Xh Ym".
- `get_daily_breakdown(time_logs)` -- Dict of date to total hours.

### InvoiceGenerator

- `generate_invoice(client, project, time_logs, hourly_rate, tax_rate=0)` -- Full invoice dict.
- `generate_invoice_number()` -- Unique invoice number.
- `calculate_line_items(time_logs, hourly_rate)` -- Line item list.
- `apply_discount(invoice, discount_pct)` -- Apply a percentage discount.
- `format_invoice_text(invoice)` -- Plain text invoice.
- `format_invoice_html(invoice)` -- HTML invoice.

### InvoiceValidator

- `validate_client(data)` -- Validate client data.
- `validate_project(data)` -- Validate project data.
- `validate_time_log(data)` -- Validate time log entry.
- `sanitize_input(text)` -- Strip HTML tags.
- `validate_hourly_rate(rate)` -- Check rate is positive.

### ReportFormatter

- `format_project_summary(project, time_logs)` -- Text project summary.
- `format_weekly_report(time_logs, hourly_rate)` -- Weekly breakdown report.
- `to_csv(time_logs)` -- CSV export.
- `format_client_statement(client, invoices)` -- Client statement.

## Testing

```bash
python -m pytest tests/
```

## Author

Goutham Uppu

## License

MIT
