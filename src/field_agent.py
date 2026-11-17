import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/agent", tags=["Autonomous Field Agent"])

# Mock enterprise ERP/CRM records.
INVENTORY = {
    "LAPTOP-001": {"sku": "LAPTOP-001", "name": "Business Laptop", "quantity": 24},
    "MOUSE-002": {"sku": "MOUSE-002", "name": "Wireless Mouse", "quantity": 150},
    "MONITOR-003": {"sku": "MONITOR-003", "name": "Office Monitor", "quantity": 12},
}

LEADS = {
    "LEAD-1001": {"lead_id": "LEAD-1001", "name": "Acme Corp", "status": "new"},
    "LEAD-1002": {"lead_id": "LEAD-1002", "name": "Northwind", "status": "contacted"},
}

TICKETS: list[dict[str, Any]] = []
PENDING: dict[str, dict[str, Any]] = {}
AUDIT_LOG: list[dict[str, Any]] = []

ALLOWED_STATUSES = {"new", "contacted", "qualified", "proposal", "won", "lost"}


class AgentRequest(BaseModel):
    instruction: str = Field(min_length=3, max_length=1000)


class ApprovalRequest(BaseModel):
    approved: bool


def record(event: str, details: dict[str, Any]) -> dict[str, Any]:
    item = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "details": details,
    }
    AUDIT_LOG.append(item)
    return item


def inventory_lookup(sku: str) -> dict[str, Any]:
    sku = sku.upper().strip()
    if sku not in INVENTORY:
        raise ValueError(f"Inventory item not found: {sku}")
    return INVENTORY[sku].copy()


def update_lead_status(lead_id: str, status: str) -> dict[str, Any]:
    lead_id = lead_id.upper().strip()
    status = status.lower().strip()

    if lead_id not in LEADS:
        raise ValueError(f"Lead not found: {lead_id}")
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status. Allowed: {sorted(ALLOWED_STATUSES)}")

    previous = LEADS[lead_id]["status"]
    LEADS[lead_id]["status"] = status

    return {
        "lead_id": lead_id,
        "previous_status": previous,
        "new_status": status,
        "updated": True,
    }


def create_support_ticket(subject: str, description: str, priority: str) -> dict[str, Any]:
    priority = priority.lower().strip()
    if priority not in {"low", "medium", "high", "urgent"}:
        raise ValueError("Priority must be low, medium, high, or urgent.")

    ticket = {
        "ticket_id": f"TKT-{len(TICKETS) + 1001}",
        "subject": subject.strip(),
        "description": description.strip(),
        "priority": priority,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    TICKETS.append(ticket)
    return ticket.copy()


def plan_instruction(instruction: str) -> dict[str, Any]:
    text = instruction.strip()
    upper = text.upper()

    sku_match = re.search(r"\b(?:LAPTOP-\d+|MOUSE-\d+|MONITOR-\d+)\b", upper)
    lead_match = re.search(r"\bLEAD-\d+\b", upper)

    # Read-only inventory lookup.
    if any(word in text.lower() for word in ("inventory", "stock", "quantity", "available")):
        if not sku_match:
            raise ValueError("Please include an SKU, e.g. LAPTOP-001.")
        return {
            "tool": "inventory_lookup",
            "arguments": {"sku": sku_match.group(0)},
            "write": False,
            "decision": "Inventory lookup requested; this is a read-only operation.",
        }

    # CRM write operation.
    if any(word in text.lower() for word in ("lead", "crm")):
        if not lead_match:
            raise ValueError("Please include a lead ID, e.g. LEAD-1001.")

        status_match = re.search(
            r"\b(new|contacted|qualified|proposal|won|lost)\b",
            text.lower(),
        )
        if not status_match:
            raise ValueError("Please specify the new lead status.")

        return {
            "tool": "update_lead_status",
            "arguments": {
                "lead_id": lead_match.group(0),
                "status": status_match.group(0),
            },
            "write": True,
            "decision": "CRM lead update requested; approval is required before execution.",
        }

    # Support-ticket write operation.
    if any(word in text.lower() for word in ("ticket", "support issue", "support request")):
        priority_match = re.search(r"\b(low|medium|high|urgent)\b", text.lower())
        priority = priority_match.group(0) if priority_match else "medium"

        subject = text[:120]
        return {
            "tool": "create_support_ticket",
            "arguments": {
                "subject": subject,
                "description": text,
                "priority": priority,
            },
            "write": True,
            "decision": "Support ticket creation requested; approval is required before execution.",
        }

    raise ValueError(
        "I could not identify an allowed operation. Try inventory lookup, "
        "lead status update, or support ticket creation."
    )


def execute_tool(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    tools = {
        "inventory_lookup": inventory_lookup,
        "update_lead_status": update_lead_status,
        "create_support_ticket": create_support_ticket,
    }
    if tool not in tools:
        raise ValueError("Tool is not permitted.")
    return tools[tool](**arguments)


@router.post("/run")
def run_agent(request: AgentRequest):
    try:
        plan = plan_instruction(request.instruction)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    cycle = [
        {"stage": "decision", "message": plan["decision"]},
        {
            "stage": "action",
            "tool": plan["tool"],
            "arguments": plan["arguments"],
        },
    ]

    if plan["write"]:
        approval_id = str(uuid.uuid4())
        PENDING[approval_id] = {
            "tool": plan["tool"],
            "arguments": plan["arguments"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        record("approval_requested", {
            "approval_id": approval_id,
            "tool": plan["tool"],
            "arguments": plan["arguments"],
        })
        cycle.append({
            "stage": "observation",
            "message": "Execution paused. Human approval is required.",
        })
        return {
            "status": "pending_approval",
            "approval_id": approval_id,
            "tool": plan["tool"],
            "cycles": cycle,
        }

    # Bounded retry loop for transient tool failures.
    last_error = None
    for attempt in range(1, 4):
        try:
            result = execute_tool(plan["tool"], plan["arguments"])
            record("tool_executed", {
                "tool": plan["tool"],
                "attempt": attempt,
                "result": result,
            })
            cycle.append({
                "stage": "observation",
                "message": "Tool execution succeeded.",
                "result": result,
            })
            return {
                "status": "completed",
                "tool": plan["tool"],
                "attempts": attempt,
                "result": result,
                "cycles": cycle,
            }
        except (ValueError, TypeError) as exc:
            last_error = str(exc)
            break
        except Exception as exc:
            last_error = str(exc)
            if attempt < 3:
                continue

    record("tool_failed", {"tool": plan["tool"], "error": last_error})
    raise HTTPException(status_code=502, detail={
        "message": "Tool execution failed.",
        "attempts": 3,
        "error": last_error,
    })


@router.post("/approve/{approval_id}")
def approve_action(approval_id: str, request: ApprovalRequest):
    pending = PENDING.pop(approval_id, None)
    if not pending:
        raise HTTPException(status_code=404, detail="Approval request not found or already handled.")

    if not request.approved:
        record("approval_rejected", {"approval_id": approval_id})
        return {"status": "rejected", "message": "The operation was not executed."}

    try:
        result = execute_tool(pending["tool"], pending["arguments"])
    except (ValueError, TypeError) as exc:
        record("approved_tool_failed", {"approval_id": approval_id, "error": str(exc)})
        raise HTTPException(status_code=422, detail=str(exc))

    record("approved_tool_executed", {
        "approval_id": approval_id,
        "tool": pending["tool"],
        "result": result,
    })
    return {
        "status": "completed",
        "tool": pending["tool"],
        "result": result,
        "observation": "Approved operation executed successfully.",
    }


@router.get("/tools")
def list_tools():
    return {
        "tools": [
            {"name": "inventory_lookup", "type": "read"},
            {"name": "update_lead_status", "type": "write", "requires_approval": True},
            {"name": "create_support_ticket", "type": "write", "requires_approval": True},
        ]
    }


@router.get("/audit")
def get_audit_log():
    return {"count": len(AUDIT_LOG), "events": AUDIT_LOG[-100:]}


@router.get("/mock/inventory/{sku}")
def mock_inventory_endpoint(sku: str):
    try:
        return inventory_lookup(sku)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/mock/leads/{lead_id}")
def mock_lead_endpoint(lead_id: str):
    lead = LEADS.get(lead_id.upper())
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return lead


@router.get("/mock/tickets")
def mock_tickets_endpoint():
    return {"tickets": TICKETS}
