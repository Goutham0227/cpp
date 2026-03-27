"""
Invoice generation utilities.
"""

from datetime import datetime, timedelta
import random

from invoice_engine.calculator import TimeCalculator


class InvoiceGenerator:
    """Generates invoices from time tracking data."""

    @staticmethod
    def generate_invoice_number():
        """
        Generate a unique invoice number in format INV-YYYYMMDD-XXXX.

        Returns:
            str: Invoice number string.
        """
        date_part = datetime.now().strftime("%Y%m%d")
        rand_part = str(random.randint(1000, 9999))
        return f"INV-{date_part}-{rand_part}"

    @staticmethod
    def calculate_line_items(time_logs, hourly_rate):
        """
        Build line items from time logs.

        Args:
            time_logs (list): List of time log dicts.
            hourly_rate (float): Billing rate per hour.

        Returns:
            list: List of line item dicts with date, description, hours, rate, amount.
        """
        items = []
        for log in time_logs:
            start = datetime.fromisoformat(log["startTime"])
            hours = TimeCalculator.calculate_duration(
                log["startTime"], log["endTime"]
            )
            amount = round(hours * hourly_rate, 2)
            items.append({
                "date": start.strftime("%Y-%m-%d"),
                "description": log.get("description", "Work performed"),
                "hours": hours,
                "rate": hourly_rate,
                "amount": amount,
            })
        return items

    @staticmethod
    def generate_invoice(client, project, time_logs, hourly_rate, tax_rate=0):
        """
        Generate a complete invoice dict.

        Args:
            client (dict): Client info with name, email, optional company.
            project (dict): Project info with name.
            time_logs (list): Time log entries.
            hourly_rate (float): Billing rate.
            tax_rate (float): Tax percentage (0-100). Default 0.

        Returns:
            dict: Full invoice with line items, totals, dates.
        """
        line_items = InvoiceGenerator.calculate_line_items(time_logs, hourly_rate)
        subtotal = round(sum(item["amount"] for item in line_items), 2)
        tax = round(subtotal * (tax_rate / 100), 2)
        total = round(subtotal + tax, 2)

        now = datetime.now()
        due = now + timedelta(days=30)

        return {
            "invoiceNumber": InvoiceGenerator.generate_invoice_number(),
            "client": client,
            "project": project,
            "lineItems": line_items,
            "subtotal": subtotal,
            "taxRate": tax_rate,
            "tax": tax,
            "total": total,
            "issuedDate": now.strftime("%Y-%m-%d"),
            "dueDate": due.strftime("%Y-%m-%d"),
        }

    @staticmethod
    def apply_discount(invoice, discount_pct):
        """
        Apply a percentage discount to an invoice and return a new invoice dict.

        Args:
            invoice (dict): Original invoice.
            discount_pct (float): Discount percentage (0-100).

        Returns:
            dict: New invoice with discount applied.
        """
        new_invoice = dict(invoice)
        discount_amount = round(new_invoice["subtotal"] * (discount_pct / 100), 2)
        discounted_subtotal = round(new_invoice["subtotal"] - discount_amount, 2)
        tax = round(discounted_subtotal * (new_invoice["taxRate"] / 100), 2)
        total = round(discounted_subtotal + tax, 2)

        new_invoice["discount"] = discount_pct
        new_invoice["discountAmount"] = discount_amount
        new_invoice["subtotal"] = discounted_subtotal
        new_invoice["tax"] = tax
        new_invoice["total"] = total
        return new_invoice

    @staticmethod
    def format_invoice_text(invoice):
        """
        Format an invoice dict as plain text.

        Args:
            invoice (dict): Invoice dict.

        Returns:
            str: Human-readable text invoice.
        """
        lines = []
        lines.append("=" * 50)
        lines.append("INVOICE")
        lines.append("=" * 50)
        lines.append(f"Invoice #:    {invoice['invoiceNumber']}")
        lines.append(f"Issued Date:  {invoice['issuedDate']}")
        lines.append(f"Due Date:     {invoice['dueDate']}")
        lines.append("")
        lines.append("Bill To:")
        client = invoice["client"]
        lines.append(f"  {client.get('name', 'N/A')}")
        if client.get("company"):
            lines.append(f"  {client['company']}")
        lines.append(f"  {client.get('email', 'N/A')}")
        lines.append("")
        lines.append(f"Project: {invoice['project'].get('name', 'N/A')}")
        lines.append("")
        lines.append("-" * 50)
        lines.append(f"{'Date':<12} {'Description':<20} {'Hours':>6} {'Rate':>8} {'Amount':>10}")
        lines.append("-" * 50)
        for item in invoice["lineItems"]:
            lines.append(
                f"{item['date']:<12} {item['description']:<20} {item['hours']:>6.2f} "
                f"{item['rate']:>8.2f} {item['amount']:>10.2f}"
            )
        lines.append("-" * 50)
        lines.append(f"{'Subtotal:':>40} {invoice['subtotal']:>10.2f}")
        if invoice.get("discount"):
            lines.append(f"{'Discount (' + str(invoice['discount']) + '%)':>40} -{invoice['discountAmount']:>9.2f}")
        if invoice["taxRate"] > 0:
            lines.append(f"{'Tax (' + str(invoice['taxRate']) + '%)':>40} {invoice['tax']:>10.2f}")
        lines.append(f"{'TOTAL:':>40} {invoice['total']:>10.2f}")
        lines.append("=" * 50)
        return "\n".join(lines)

    @staticmethod
    def format_invoice_html(invoice):
        """
        Format an invoice dict as simple HTML.

        Args:
            invoice (dict): Invoice dict.

        Returns:
            str: HTML string of the invoice.
        """
        client = invoice["client"]
        project = invoice["project"]

        rows = ""
        for item in invoice["lineItems"]:
            rows += (
                f"<tr>"
                f"<td>{item['date']}</td>"
                f"<td>{item['description']}</td>"
                f"<td>{item['hours']:.2f}</td>"
                f"<td>{item['rate']:.2f}</td>"
                f"<td>{item['amount']:.2f}</td>"
                f"</tr>\n"
            )

        discount_row = ""
        if invoice.get("discount"):
            discount_row = (
                f"<tr><td colspan='4' style='text-align:right'>"
                f"Discount ({invoice['discount']}%)</td>"
                f"<td>-{invoice['discountAmount']:.2f}</td></tr>\n"
            )

        tax_row = ""
        if invoice["taxRate"] > 0:
            tax_row = (
                f"<tr><td colspan='4' style='text-align:right'>"
                f"Tax ({invoice['taxRate']}%)</td>"
                f"<td>{invoice['tax']:.2f}</td></tr>\n"
            )

        html = f"""<!DOCTYPE html>
<html>
<head><title>Invoice {invoice['invoiceNumber']}</title></head>
<body>
<h1>Invoice</h1>
<p><strong>Invoice #:</strong> {invoice['invoiceNumber']}</p>
<p><strong>Issued:</strong> {invoice['issuedDate']} | <strong>Due:</strong> {invoice['dueDate']}</p>

<h2>Bill To</h2>
<p>{client.get('name', 'N/A')}<br>
{client.get('company', '')}<br>
{client.get('email', 'N/A')}</p>

<h2>Project: {project.get('name', 'N/A')}</h2>

<table border="1" cellpadding="5" cellspacing="0">
<tr><th>Date</th><th>Description</th><th>Hours</th><th>Rate</th><th>Amount</th></tr>
{rows}
<tr><td colspan="4" style="text-align:right"><strong>Subtotal</strong></td><td>{invoice['subtotal']:.2f}</td></tr>
{discount_row}{tax_row}
<tr><td colspan="4" style="text-align:right"><strong>TOTAL</strong></td><td><strong>{invoice['total']:.2f}</strong></td></tr>
</table>
</body>
</html>"""
        return html
