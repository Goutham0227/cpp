"""API integration tests for client CRUD operations."""

import json
import pytest


class TestClientAPI:
    def test_list_clients_empty(self, client):
        resp = client.get("/api/clients")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 0

    def test_create_client(self, client, sample_client_data):
        resp = client.post("/api/clients", json=sample_client_data)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "Test Client"
        assert data["email"] == "test@example.com"

    def test_create_client_missing_fields(self, client):
        resp = client.post("/api/clients", json={"name": "Incomplete"})
        assert resp.status_code == 400

    def test_get_client(self, client, sample_client_data):
        create_resp = client.post("/api/clients", json=sample_client_data)
        client_id = create_resp.get_json()["client_id"]
        resp = client.get(f"/api/clients/{client_id}")
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Test Client"

    def test_get_client_not_found(self, client):
        resp = client.get("/api/clients/nonexistent")
        assert resp.status_code == 404

    def test_update_client(self, client, sample_client_data):
        create_resp = client.post("/api/clients", json=sample_client_data)
        client_id = create_resp.get_json()["client_id"]
        resp = client.put(f"/api/clients/{client_id}", json={"name": "Updated Name"})
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Updated Name"

    def test_update_client_not_found(self, client):
        resp = client.put("/api/clients/nonexistent", json={"name": "X"})
        assert resp.status_code == 404

    def test_delete_client(self, client, sample_client_data):
        create_resp = client.post("/api/clients", json=sample_client_data)
        client_id = create_resp.get_json()["client_id"]
        resp = client.delete(f"/api/clients/{client_id}")
        assert resp.status_code == 200
        # Verify deleted
        resp = client.get(f"/api/clients/{client_id}")
        assert resp.status_code == 404

    def test_delete_client_not_found(self, client):
        resp = client.delete("/api/clients/nonexistent")
        assert resp.status_code == 404
