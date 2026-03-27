"""
SQLite database layer for local development.
Provides CRUD operations for all entities.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from contextlib import contextmanager


class Database:
    """SQLite database manager with connection pooling."""

    def __init__(self, db_path="timetracker.db"):
        self.db_path = db_path
        self._memory_conn = None
        if db_path == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:")
            self._memory_conn.row_factory = sqlite3.Row
            self._memory_conn.execute("PRAGMA foreign_keys = ON")
        self.init_db()

    def get_connection(self):
        if self._memory_conn is not None:
            return self._memory_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def get_db(self):
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if self._memory_conn is None:
                conn.close()

    def init_db(self):
        with self.get_db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS clients (
                    client_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    company TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    hourly_rate REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (client_id) REFERENCES clients(client_id)
                );

                CREATE TABLE IF NOT EXISTS time_entries (
                    entry_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    hourly_rate REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id)
                );

                CREATE TABLE IF NOT EXISTS invoices (
                    invoice_id TEXT PRIMARY KEY,
                    invoice_number TEXT UNIQUE NOT NULL,
                    client_id TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    created_at TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    tax_rate REAL DEFAULT 0.0,
                    tax_amount REAL DEFAULT 0.0,
                    currency TEXT DEFAULT 'EUR',
                    notes TEXT DEFAULT '',
                    line_items TEXT DEFAULT '[]',
                    FOREIGN KEY (client_id) REFERENCES clients(client_id)
                );
            """)


class ClientModel:
    """CRUD operations for clients."""

    def __init__(self, db: Database):
        self.db = db

    def create(self, data: dict) -> dict:
        client_id = data.get("client_id", str(uuid.uuid4()))
        now = datetime.utcnow().isoformat()
        with self.db.get_db() as conn:
            conn.execute(
                "INSERT INTO clients (client_id, name, email, company, address, phone, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (client_id, data["name"], data["email"],
                 data.get("company", ""), data.get("address", ""),
                 data.get("phone", ""), now)
            )
        return self.get(client_id)

    def get(self, client_id: str) -> dict:
        with self.db.get_db() as conn:
            row = conn.execute("SELECT * FROM clients WHERE client_id = ?", (client_id,)).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_all(self) -> list:
        with self.db.get_db() as conn:
            rows = conn.execute("SELECT * FROM clients ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def update(self, client_id: str, data: dict) -> dict:
        fields = []
        values = []
        for key in ("name", "email", "company", "address", "phone"):
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        if not fields:
            return self.get(client_id)
        values.append(client_id)
        with self.db.get_db() as conn:
            conn.execute(f"UPDATE clients SET {', '.join(fields)} WHERE client_id = ?", values)
        return self.get(client_id)

    def delete(self, client_id: str) -> bool:
        with self.db.get_db() as conn:
            cursor = conn.execute("DELETE FROM clients WHERE client_id = ?", (client_id,))
        return cursor.rowcount > 0


class ProjectModel:
    """CRUD operations for projects."""

    def __init__(self, db: Database):
        self.db = db

    def create(self, data: dict) -> dict:
        project_id = data.get("project_id", str(uuid.uuid4()))
        now = datetime.utcnow().isoformat()
        with self.db.get_db() as conn:
            conn.execute(
                "INSERT INTO projects (project_id, name, client_id, description, hourly_rate, is_active, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (project_id, data["name"], data["client_id"],
                 data.get("description", ""), data.get("hourly_rate", 0.0),
                 1, now)
            )
        return self.get(project_id)

    def get(self, project_id: str) -> dict:
        with self.db.get_db() as conn:
            row = conn.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["is_active"] = bool(result["is_active"])
        return result

    def get_all(self) -> list:
        with self.db.get_db() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        results = [dict(r) for r in rows]
        for r in results:
            r["is_active"] = bool(r["is_active"])
        return results

    def get_by_client(self, client_id: str) -> list:
        with self.db.get_db() as conn:
            rows = conn.execute("SELECT * FROM projects WHERE client_id = ? ORDER BY created_at DESC",
                                (client_id,)).fetchall()
        results = [dict(r) for r in rows]
        for r in results:
            r["is_active"] = bool(r["is_active"])
        return results

    def update(self, project_id: str, data: dict) -> dict:
        fields = []
        values = []
        for key in ("name", "client_id", "description", "hourly_rate", "is_active"):
            if key in data:
                fields.append(f"{key} = ?")
                val = data[key]
                if key == "is_active":
                    val = 1 if val else 0
                values.append(val)
        if not fields:
            return self.get(project_id)
        values.append(project_id)
        with self.db.get_db() as conn:
            conn.execute(f"UPDATE projects SET {', '.join(fields)} WHERE project_id = ?", values)
        return self.get(project_id)

    def delete(self, project_id: str) -> bool:
        with self.db.get_db() as conn:
            cursor = conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        return cursor.rowcount > 0


class TimeEntryModel:
    """CRUD operations for time entries."""

    def __init__(self, db: Database):
        self.db = db

    def create(self, data: dict) -> dict:
        entry_id = data.get("entry_id", str(uuid.uuid4()))
        now = datetime.utcnow().isoformat()
        start_time = data.get("start_time", now)
        with self.db.get_db() as conn:
            conn.execute(
                "INSERT INTO time_entries (entry_id, project_id, description, start_time, end_time, hourly_rate, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (entry_id, data["project_id"], data.get("description", ""),
                 start_time, data.get("end_time"), data.get("hourly_rate", 0.0), now)
            )
        return self.get(entry_id)

    def get(self, entry_id: str) -> dict:
        with self.db.get_db() as conn:
            row = conn.execute("SELECT * FROM time_entries WHERE entry_id = ?", (entry_id,)).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_all(self) -> list:
        with self.db.get_db() as conn:
            rows = conn.execute("SELECT * FROM time_entries ORDER BY start_time DESC").fetchall()
        return [dict(r) for r in rows]

    def get_by_project(self, project_id: str) -> list:
        with self.db.get_db() as conn:
            rows = conn.execute("SELECT * FROM time_entries WHERE project_id = ? ORDER BY start_time DESC",
                                (project_id,)).fetchall()
        return [dict(r) for r in rows]

    def update(self, entry_id: str, data: dict) -> dict:
        fields = []
        values = []
        for key in ("project_id", "description", "start_time", "end_time", "hourly_rate"):
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        if not fields:
            return self.get(entry_id)
        values.append(entry_id)
        with self.db.get_db() as conn:
            conn.execute(f"UPDATE time_entries SET {', '.join(fields)} WHERE entry_id = ?", values)
        return self.get(entry_id)

    def delete(self, entry_id: str) -> bool:
        with self.db.get_db() as conn:
            cursor = conn.execute("DELETE FROM time_entries WHERE entry_id = ?", (entry_id,))
        return cursor.rowcount > 0


class InvoiceModel:
    """CRUD operations for invoices."""

    def __init__(self, db: Database):
        self.db = db

    def create(self, data: dict) -> dict:
        invoice_id = data.get("invoice_id", str(uuid.uuid4()))
        invoice_number = data.get("invoice_number",
                                   f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}")
        now = datetime.utcnow().isoformat()
        from datetime import timedelta
        due = data.get("due_date", (datetime.utcnow() + timedelta(days=30)).isoformat())
        line_items = json.dumps(data.get("line_items", []))
        with self.db.get_db() as conn:
            conn.execute(
                "INSERT INTO invoices (invoice_id, invoice_number, client_id, status, created_at, due_date, "
                "tax_rate, tax_amount, currency, notes, line_items) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (invoice_id, invoice_number, data["client_id"],
                 data.get("status", "draft"), now, due,
                 data.get("tax_rate", 0.0), data.get("tax_amount", 0.0),
                 data.get("currency", "EUR"), data.get("notes", ""), line_items)
            )
        return self.get(invoice_id)

    def get(self, invoice_id: str) -> dict:
        with self.db.get_db() as conn:
            row = conn.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["line_items"] = json.loads(result["line_items"])
        return result

    def get_all(self) -> list:
        with self.db.get_db() as conn:
            rows = conn.execute("SELECT * FROM invoices ORDER BY created_at DESC").fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["line_items"] = json.loads(d["line_items"])
            results.append(d)
        return results

    def get_by_client(self, client_id: str) -> list:
        with self.db.get_db() as conn:
            rows = conn.execute("SELECT * FROM invoices WHERE client_id = ? ORDER BY created_at DESC",
                                (client_id,)).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["line_items"] = json.loads(d["line_items"])
            results.append(d)
        return results

    def update(self, invoice_id: str, data: dict) -> dict:
        fields = []
        values = []
        for key in ("client_id", "status", "due_date", "tax_rate", "tax_amount", "currency", "notes"):
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        if "line_items" in data:
            fields.append("line_items = ?")
            values.append(json.dumps(data["line_items"]))
        if not fields:
            return self.get(invoice_id)
        values.append(invoice_id)
        with self.db.get_db() as conn:
            conn.execute(f"UPDATE invoices SET {', '.join(fields)} WHERE invoice_id = ?", values)
        return self.get(invoice_id)

    def delete(self, invoice_id: str) -> bool:
        with self.db.get_db() as conn:
            cursor = conn.execute("DELETE FROM invoices WHERE invoice_id = ?", (invoice_id,))
        return cursor.rowcount > 0
