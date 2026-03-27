"""Tests for invoicegen.tax module."""

import pytest
from invoicegen.tax import TaxCalculator, TaxRate, TaxType


class TestTaxRate:
    def test_ireland_standard_vat(self):
        rate = TaxRate.IRELAND_STANDARD
        assert rate.rate == 23.0
        assert rate.tax_type == TaxType.VAT

    def test_calculate_tax(self):
        rate = TaxRate("Test", 20.0, TaxType.VAT)
        assert rate.calculate_tax(100.0) == 20.0
        assert rate.calculate_tax(250.0) == 50.0

    def test_calculate_gross(self):
        rate = TaxRate("Test", 23.0, TaxType.VAT)
        assert rate.calculate_gross(100.0) == 123.0

    def test_extract_tax(self):
        rate = TaxRate("Test", 20.0, TaxType.VAT)
        # From gross 120, tax should be 20
        assert rate.extract_tax(120.0) == 20.0

    def test_zero_rate(self):
        rate = TaxRate.ZERO_RATE
        assert rate.calculate_tax(1000.0) == 0.0

    def test_invalid_rate(self):
        with pytest.raises(ValueError):
            TaxRate("Bad", -5.0)
        with pytest.raises(ValueError):
            TaxRate("Bad", 101.0)

    def test_tax_rate_to_dict(self):
        rate = TaxRate("Custom", 15.0, TaxType.GST)
        d = rate.to_dict()
        assert d["name"] == "Custom"
        assert d["rate"] == 15.0
        assert d["tax_type"] == "gst"


class TestTaxCalculator:
    def test_calculate_invoice_tax_default(self):
        calc = TaxCalculator()
        result = calc.calculate_invoice_tax(1000.0)
        assert result["tax_amount"] == 230.0
        assert result["total"] == 1230.0
        assert result["tax_rate_percent"] == 23.0

    def test_calculate_invoice_tax_custom_rate(self):
        calc = TaxCalculator()
        rate = TaxRate("Custom", 10.0, TaxType.SALES_TAX)
        result = calc.calculate_invoice_tax(500.0, rate)
        assert result["tax_amount"] == 50.0
        assert result["total"] == 550.0

    def test_custom_rate_registry(self):
        calc = TaxCalculator()
        rate = TaxRate("Special", 5.0, TaxType.GST)
        calc.add_custom_rate("special", rate)
        retrieved = calc.get_rate("special")
        assert retrieved.rate == 5.0

    def test_multi_rate_tax(self):
        calc = TaxCalculator()
        items = [
            {"amount": 100.0, "tax_rate": TaxRate("High", 23.0, TaxType.VAT)},
            {"amount": 200.0, "tax_rate": TaxRate("Low", 10.0, TaxType.VAT)},
        ]
        result = calc.calculate_multi_rate_tax(items)
        assert result["subtotal"] == 300.0
        assert result["total_tax"] == 43.0  # 23 + 20
        assert result["total"] == 343.0
        assert len(result["breakdown"]) == 2
