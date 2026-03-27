"""API integration tests for project CRUD operations."""

import pytest


class TestProjectAPI:
    def _create_client(self, client):
        resp = client.post("/api/clients", json={"name": "PC", "email": "pc@test.com"})
        return resp.get_json()["client_id"]

    def test_list_projects_empty(self, client):
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 0

    def test_create_project(self, client):
        client_id = self._create_client(client)
        resp = client.post("/api/projects", json={
            "name": "Web App", "client_id": client_id, "hourly_rate": 100.0
        })
        assert resp.status_code == 201
        assert resp.get_json()["name"] == "Web App"

    def test_create_project_missing_fields(self, client):
        resp = client.post("/api/projects", json={"name": "No client"})
        assert resp.status_code == 400

    def test_get_project(self, client):
        client_id = self._create_client(client)
        create_resp = client.post("/api/projects", json={
            "name": "API", "client_id": client_id, "hourly_rate": 80.0
        })
        project_id = create_resp.get_json()["project_id"]
        resp = client.get(f"/api/projects/{project_id}")
        assert resp.status_code == 200
        assert resp.get_json()["hourly_rate"] == 80.0

    def test_get_project_not_found(self, client):
        resp = client.get("/api/projects/nonexistent")
        assert resp.status_code == 404

    def test_update_project(self, client):
        client_id = self._create_client(client)
        create_resp = client.post("/api/projects", json={
            "name": "Old Name", "client_id": client_id
        })
        project_id = create_resp.get_json()["project_id"]
        resp = client.put(f"/api/projects/{project_id}", json={"name": "New Name", "hourly_rate": 120.0})
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "New Name"

    def test_delete_project(self, client):
        client_id = self._create_client(client)
        create_resp = client.post("/api/projects", json={
            "name": "Delete Me", "client_id": client_id
        })
        project_id = create_resp.get_json()["project_id"]
        resp = client.delete(f"/api/projects/{project_id}")
        assert resp.status_code == 200
