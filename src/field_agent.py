"""Authenticated field-agent routes, approvals, and tenant-scoped audit logs."""

import json
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

try:
    from .dependencies import get_current_user
    from .agent_llm import plan_with_llm, AgentLLMError
    from .erp_client import erp_client, ERPClientError
except ImportError:
    from dependencies import get_current_user
    from agent_llm import plan_with_llm, AgentLLMError
    from erp_client import erp_client, ERPClientError


router = APIRouter(prefix="/agent", tags=["Autonomous Field Agent"])

DB_PATH = Path("data/agent_state.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

READ_TOOLS = {"inventory_lookup"}
WRITE_TOOLS = {"update_lead_status", "create_support_ticket"}


class AgentRequest(BaseModel):
    instruction: str = Field(min_length=3, max_length=1000)


class ApprovalRequest(BaseModel):
    approved: bool


def get_connection():
    """Open the agent state database with row-style results."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create approval and audit tables and their query indexes."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS agent_approvals (
                approval_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                tool TEXT NOT NULL,
                arguments TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                handled_at TEXT
            );

            CREATE TABLE IF NOT EXISTS agent_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event TEXT NOT NULL,
                details TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_agent_approvals_owner
            ON agent_approvals(user_id, tenant_id, status);

            CREATE INDEX IF NOT EXISTS idx_agent_audit_tenant
            ON agent_audit(tenant_id, id);
        """)


init_db()


def now():
    """Return a timezone-aware ISO timestamp for persisted agent events."""
    return datetime.now(timezone.utc).isoformat()


def record(user: dict, event: str, details: dict[str, Any]):
    """Append an audit event scoped to the acting user and tenant."""
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO agent_audit
            (user_id, tenant_id, timestamp, event, details)
            VALUES (?, ?, ?, ?, ?)""",
            (
                str(user["user_id"]),
                str(user["tenant_id"]),
                now(),
                event,
                json.dumps(details, default=str),
            ),
        )


def execute_tool(tool: str, arguments: dict[str, Any]):
    """Dispatch only the explicitly allowlisted ERP/CRM operations."""
    if tool == "inventory_lookup":
        return erp_client.inventory_lookup(arguments["sku"])

    if tool == "update_lead_status":
        return erp_client.update_lead_status(
            arguments["lead_id"],
            arguments["status"],
        )

    if tool == "create_support_ticket":
        return erp_client.create_ticket(
            arguments["subject"],
            arguments["description"],
            arguments["priority"],
        )

    raise ValueError("Tool is not permitted.")


def save_approval(user, tool, arguments):
    """Persist a pending write operation owned by one user and tenant."""
    approval_id = str(uuid.uuid4())

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO agent_approvals
            (approval_id, user_id, tenant_id, tool, arguments, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
            (
                approval_id,
                str(user["user_id"]),
                str(user["tenant_id"]),
                tool,
                json.dumps(arguments),
                now(),
            ),
        )

    return approval_id


@router.post("/run")
def run_agent(
    request: AgentRequest,
    user: dict = Depends(get_current_user),
):
    """Plan a tool call, execute reads, and pause writes for approval."""
    try:
        plan = plan_with_llm(request.instruction)
    except AgentLLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    tool_call = plan.get("tool_call")
    decision = plan.get("decision", "The agent evaluated the request.")

    cycles = [{"stage": "decision", "message": decision}]

    if not tool_call:
        cycles.append({
            "stage": "observation",
            "message": decision,
        })
        record(user, "agent_needs_input", {"instruction": request.instruction})
        return {
            "status": "needs_input",
            "message": decision,
            "cycles": cycles,
        }

    tool = tool_call["name"]
    arguments = tool_call["arguments"]

    if tool not in READ_TOOLS | WRITE_TOOLS:
        raise HTTPException(status_code=422, detail="Tool is not permitted.")

    cycles.append({
        "stage": "action",
        "tool": tool,
        "arguments": arguments,
    })

    if tool in WRITE_TOOLS:
        approval_id = save_approval(user, tool, arguments)

        record(user, "approval_requested", {
            "approval_id": approval_id,
            "tool": tool,
            "arguments": arguments,
        })

        cycles.append({
            "stage": "observation",
            "message": "Execution paused. Human approval is required.",
        })

        return {
            "status": "pending_approval",
            "approval_id": approval_id,
            "tool": tool,
            "arguments": arguments,
            "cycles": cycles,
        }

    last_error = None

    for attempt in range(1, 4):
        try:
            result = execute_tool(tool, arguments)

            record(user, "tool_executed", {
                "tool": tool,
                "attempt": attempt,
                "result": result,
            })

            cycles.append({
                "stage": "observation",
                "message": "ERP/CRM tool execution succeeded.",
                "result": result,
            })

            return {
                "status": "completed",
                "tool": tool,
                "attempts": attempt,
                "result": result,
                "cycles": cycles,
            }

        except ERPClientError as exc:
            last_error = str(exc)
            break
        except Exception as exc:
            last_error = str(exc)
            break

    record(user, "tool_failed", {
        "tool": tool,
        "attempts": attempt,
        "error": last_error,
    })

    raise HTTPException(
        status_code=502,
        detail={
            "message": "ERP/CRM tool execution failed.",
            "attempts": attempt,
            "error": last_error,
        },
    )


@router.post("/approve/{approval_id}")
def approve_action(
    approval_id: str,
    request: ApprovalRequest,
    user: dict = Depends(get_current_user),
):
    """Atomically consume an owned approval before executing its operation."""
    # Ownership and tenant predicates prevent cross-user and cross-tenant
    # approval access before the state transition is attempted.
    with get_connection() as conn:
        pending = conn.execute(
            """SELECT * FROM agent_approvals
            WHERE approval_id = ?
            AND user_id = ?
            AND tenant_id = ?
            AND status = 'pending'""",
            (
                approval_id,
                str(user["user_id"]),
                str(user["tenant_id"]),
            ),
        ).fetchone()

        if not pending:
            raise HTTPException(
                status_code=404,
                detail="Approval not found, already handled, or not owned by this user.",
            )

        if not request.approved:
            conn.execute(
                """UPDATE agent_approvals
                SET status = 'rejected', handled_at = ?
                WHERE approval_id = ? AND status = 'pending'""",
                (now(), approval_id),
            )
            rejected_tool = pending["tool"]
        else:
            # Claiming only pending rows makes a second approval request fail,
            # preventing replay and duplicate side effects.
            cursor = conn.execute(
                """UPDATE agent_approvals
                SET status = 'processing', handled_at = ?
                WHERE approval_id = ? AND status = 'pending'""",
                (now(), approval_id),
            )

            if cursor.rowcount != 1:
                raise HTTPException(
                    status_code=409,
                    detail="Approval is already being handled.",
                )

            tool = pending["tool"]
            arguments = json.loads(pending["arguments"])

    # Write the rejection audit event only after the transaction closes.
    if not request.approved:
        record(user, "approval_rejected", {
            "approval_id": approval_id,
            "tool": rejected_tool,
        })

        return {
            "status": "rejected",
            "message": "The operation was not executed.",
        }

    try:
        result = execute_tool(tool, arguments)

        with get_connection() as conn:
            conn.execute(
                "UPDATE agent_approvals SET status = 'completed' WHERE approval_id = ?",
                (approval_id,),
            )

        record(user, "approved_tool_executed", {
            "approval_id": approval_id,
            "tool": tool,
            "result": result,
        })

        return {
            "status": "completed",
            "tool": tool,
            "result": result,
            "observation": "Approved operation executed successfully.",
        }

    except Exception as exc:
        with get_connection() as conn:
            conn.execute(
                "UPDATE agent_approvals SET status = 'failed' WHERE approval_id = ?",
                (approval_id,),
            )

        record(user, "approved_tool_failed", {
            "approval_id": approval_id,
            "tool": tool,
            "error": str(exc),
        })

        raise HTTPException(
            status_code=502,
            detail="Approved ERP/CRM operation failed. Check the audit log.",
        )


@router.get("/approvals")
def list_approvals(user: dict = Depends(get_current_user)):
    """List only approvals initiated by the authenticated user in its tenant."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT approval_id, tool, arguments, status, created_at, handled_at
            FROM agent_approvals
            WHERE user_id = ? AND tenant_id = ?
            ORDER BY created_at DESC LIMIT 100""",
            (str(user["user_id"]), str(user["tenant_id"])),
        ).fetchall()

    return {
        "approvals": [
            {
                **dict(row),
                "arguments": json.loads(row["arguments"]),
            }
            for row in rows
        ]
    }


@router.get("/tools")
def list_tools(user: dict = Depends(get_current_user)):
    """Describe the allowlisted tools and their approval requirements."""
    return {
        "tools": [
            {"name": "inventory_lookup", "type": "read", "requires_approval": False},
            {"name": "update_lead_status", "type": "write", "requires_approval": True},
            {"name": "create_support_ticket", "type": "write", "requires_approval": True},
        ]
    }


@router.get("/audit")
def get_audit_log(user: dict = Depends(get_current_user)):
    """Return audit events for the authenticated user's tenant."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT timestamp, event, details
            FROM agent_audit
            WHERE tenant_id = ?
            ORDER BY id DESC LIMIT 100""",
            (str(user["tenant_id"]),),
        ).fetchall()

    events = [
        {
            "timestamp": row["timestamp"],
            "event": row["event"],
            "details": json.loads(row["details"]),
        }
        for row in rows
    ]

    return {"count": len(events), "events": events}
