import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


DB_PATH = Path(os.getenv("ERP_DB_PATH", "data/erp_mock.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Datheon Mock ERP/CRM API",
    version="1.0.0",
    description="Independent REST API for inventory, CRM leads and support tickets."
)

ALLOWED_STATUSES = {
    "new", "contacted", "qualified", "proposal", "won", "lost"
}
ALLOWED_PRIORITIES = {"low", "medium", "high", "urgent"}


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS inventory (
                sku TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity >= 0)
            );

            CREATE TABLE IF NOT EXISTS leads (
                lead_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        conn.executemany(
            """
            INSERT OR IGNORE INTO inventory (sku, name, quantity)
            VALUES (?, ?, ?)
            """,
            [
                ("LAPTOP-001", "Business Laptop", 24),
                ("MOUSE-002", "Wireless Mouse", 150),
                ("MONITOR-003", "Office Monitor", 12),
            ],
        )

        conn.executemany(
            """
            INSERT OR IGNORE INTO leads (lead_id, name, status)
            VALUES (?, ?, ?)
            """,
            [
                ("LEAD-1001", "Acme Corp", "new"),
                ("LEAD-1002", "Northwind", "contacted"),
            ],
        )


init_db()


class LeadUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=20)


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=3, max_length=1000)
    priority: str = "medium"


@app.get("/health")
def health():
    return {"status": "healthy", "service": "mock-erp-crm"}


@app.get("/inventory/{sku}")
def inventory_lookup(sku: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM inventory WHERE sku = ?",
            (sku.strip().upper(),),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return dict(row)


@app.get("/leads/{lead_id}")
def get_lead(lead_id: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM leads WHERE lead_id = ?",
            (lead_id.strip().upper(),),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")

    return dict(row)


@app.patch("/leads/{lead_id}/status")
def update_lead(lead_id: str, request: LeadUpdate):
    lead_id = lead_id.strip().upper()
    status = request.status.strip().lower()

    if status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Allowed: {sorted(ALLOWED_STATUSES)}",
        )

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM leads WHERE lead_id = ?",
            (lead_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Lead not found")

        previous = row["status"]

        conn.execute(
            "UPDATE leads SET status = ? WHERE lead_id = ?",
            (status, lead_id),
        )

    return {
        "lead_id": lead_id,
        "previous_status": previous,
        "new_status": status,
        "updated": True,
    }


@app.post("/tickets", status_code=201)
def create_ticket(request: TicketCreate):
    priority = request.priority.strip().lower()

    if priority not in ALLOWED_PRIORITIES:
        raise HTTPException(
            status_code=422,
            detail=f"Priority must be one of {sorted(ALLOWED_PRIORITIES)}",
        )

    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        next_number = conn.execute(
            "SELECT COUNT(*) + 1001 AS number FROM tickets"
        ).fetchone()["number"]

        ticket = {
            "ticket_id": f"TKT-{next_number}",
            "subject": request.subject.strip(),
            "description": request.description.strip(),
            "priority": priority,
            "status": "open",
            "created_at": created_at,
        }

        conn.execute(
            """
            INSERT INTO tickets
            (ticket_id, subject, description, priority, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ticket["ticket_id"],
                ticket["subject"],
                ticket["description"],
                ticket["priority"],
                ticket["status"],
                ticket["created_at"],
            ),
        )

    return ticket


@app.get("/tickets")
def list_tickets():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tickets ORDER BY created_at DESC"
        ).fetchall()

    return {"tickets": [dict(row) for row in rows]}
