"""API integration tests for invoice CRUD and generation."""

import pytest


class TestInvoiceAPI:
    def _create_client(self, client):
        resp = client.post("/api/clients", json={"name": "Inv Client", "email": "inv@test.com"})
        return resp.get_json()["client_id"]

    def test_list_invoices_empty(self, client):
        resp = client.get("/api/invoices")
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 0

    def test_create_invoice(self, client):
        client_id = self._create_client(client)
        resp = client.post("/api/invoices", json={
            "client_id": client_id,
            "line_items": [{"description": "Dev", "quantity": 10, "unit_price": 100}],
            "tax_rate": 23.0,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["client_id"] == client_id

    def test_create_invoice_missing_client(self, client):
        resp = client.post("/api/invoices", json={"notes": "No client"})
        assert resp.status_code == 400

    def test_get_invoice(self, client):
        client_id = self._create_client(client)
        create_resp = client.post("/api/invoices", json={"client_id": client_id})
        invoice_id = create_resp.get_json()["invoice_id"]
        resp = client.get(f"/api/invoices/{invoice_id}")
        assert resp.status_code == 200

    def test_get_invoice_not_found(self, client):
        resp = client.get("/api/invoices/nonexistent")
        assert resp.status_code == 404

    def test_update_invoice(self, client):
        client_id = self._create_client(client)
        create_resp = client.post("/api/invoices", json={"client_id": client_id})
        invoice_id = create_resp.get_json()["invoice_id"]
        resp = client.put(f"/api/invoices/{invoice_id}", json={
            "status": "sent", "notes": "Updated notes"
        })
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "sent"

    def test_delete_invoice(self, client):
        client_id = self._create_client(client)
        create_resp = client.post("/api/invoices", json={"client_id": client_id})
        invoice_id = create_resp.get_json()["invoice_id"]
        resp = client.delete(f"/api/invoices/{invoice_id}")
        assert resp.status_code == 200

    def test_generate_invoice_pdf(self, client):
        client_id = self._create_client(client)
        create_resp = client.post("/api/invoices", json={
            "client_id": client_id,
            "line_items": [{"description": "Work", "quantity": 5, "unit_price": 80}],
        })
        invoice_id = create_resp.get_json()["invoice_id"]
        resp = client.post(f"/api/invoices/{invoice_id}/generate")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "lambda_result" in data
        assert "s3_location" in data

    def test_scan_receipt(self, client):
        resp = client.post("/api/receipts/scan")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "vendor" in data
        assert "total" in data
