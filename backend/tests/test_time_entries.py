"""API integration tests for time entry CRUD operations."""

import pytest


class TestTimeEntryAPI:
    def _setup_project(self, client):
        c_resp = client.post("/api/clients", json={"name": "TE Client", "email": "te@test.com"})
        client_id = c_resp.get_json()["client_id"]
        p_resp = client.post("/api/projects", json={
            "name": "TE Project", "client_id": client_id, "hourly_rate": 75.0
        })
        return p_resp.get_json()["project_id"]

    def test_list_time_entries_empty(self, client):
        resp = client.get("/api/time-entries")
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 0

    def test_create_time_entry(self, client):
        project_id = self._setup_project(client)
        resp = client.post("/api/time-entries", json={
            "project_id": project_id,
            "description": "Backend development",
            "start_time": "2025-03-10T09:00:00",
            "end_time": "2025-03-10T13:00:00",
            "hourly_rate": 75.0,
        })
        assert resp.status_code == 201
        assert resp.get_json()["description"] == "Backend development"

    def test_create_time_entry_missing_project(self, client):
        resp = client.post("/api/time-entries", json={"description": "No project"})
        assert resp.status_code == 400

    def test_get_time_entry(self, client):
        project_id = self._setup_project(client)
        create_resp = client.post("/api/time-entries", json={
            "project_id": project_id, "description": "Test", "hourly_rate": 50.0
        })
        entry_id = create_resp.get_json()["entry_id"]
        resp = client.get(f"/api/time-entries/{entry_id}")
        assert resp.status_code == 200

    def test_get_time_entry_not_found(self, client):
        resp = client.get("/api/time-entries/nonexistent")
        assert resp.status_code == 404

    def test_update_time_entry(self, client):
        project_id = self._setup_project(client)
        create_resp = client.post("/api/time-entries", json={
            "project_id": project_id, "description": "Initial"
        })
        entry_id = create_resp.get_json()["entry_id"]
        resp = client.put(f"/api/time-entries/{entry_id}", json={
            "description": "Updated description",
            "end_time": "2025-03-10T17:00:00",
        })
        assert resp.status_code == 200
        assert resp.get_json()["description"] == "Updated description"

    def test_delete_time_entry(self, client):
        project_id = self._setup_project(client)
        create_resp = client.post("/api/time-entries", json={
            "project_id": project_id, "description": "Delete me"
        })
        entry_id = create_resp.get_json()["entry_id"]
        resp = client.delete(f"/api/time-entries/{entry_id}")
        assert resp.status_code == 200
