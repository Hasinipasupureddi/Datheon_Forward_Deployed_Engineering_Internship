"""Plan allowlisted ERP/CRM tool calls with the local Ollama model."""

import os
import requests

from src.monitoring import record_token_usage

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "inventory_lookup",
            "description": "Look up the available quantity of an inventory item using its SKU.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string"}
                },
                "required": ["sku"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_lead_status",
            "description": "Update a CRM lead to a new sales status. This is a sensitive write and requires human approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["new", "contacted", "qualified", "proposal", "won", "lost"]
                    }
                },
                "required": ["lead_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Create a support ticket. This is a write operation and requires human approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"]
                    }
                },
                "required": ["subject", "description", "priority"]
            }
        }
    }
]

ALLOWED_TOOLS = {
    "inventory_lookup",
    "update_lead_status",
    "create_support_ticket",
}


class AgentLLMError(Exception):
    """Raised when the local model cannot produce a valid tool call."""


def validate_tool_call(name, arguments):
    """Validate the model's tool name, exact arguments, and field limits."""
    if name not in ALLOWED_TOOLS:
        raise AgentLLMError(f"Tool is not allowed: {name}")

    if not isinstance(arguments, dict):
        raise AgentLLMError("Tool arguments must be a JSON object.")

    required_fields = {
        "inventory_lookup": {"sku"},
        "update_lead_status": {"lead_id", "status"},
        "create_support_ticket": {"subject", "description", "priority"},
    }

    expected = required_fields[name]

    if set(arguments.keys()) != expected:
        raise AgentLLMError(
            f"Invalid arguments for {name}. Expected: {sorted(expected)}"
        )

    for key, value in arguments.items():
        if not isinstance(value, str) or not value.strip():
            raise AgentLLMError(f"Invalid value for argument: {key}")

    if name == "inventory_lookup":
        if len(arguments["sku"]) > 50:
            raise AgentLLMError("SKU is too long.")

    elif name == "update_lead_status":
        if len(arguments["lead_id"]) > 50:
            raise AgentLLMError("Lead ID is too long.")
        if arguments["status"].lower() not in {
            "new", "contacted", "qualified", "proposal", "won", "lost"
        }:
            raise AgentLLMError("Invalid lead status.")

    elif name == "create_support_ticket":
        if len(arguments["subject"]) > 120:
            raise AgentLLMError("Ticket subject is too long.")
        if len(arguments["description"]) > 1000:
            raise AgentLLMError("Ticket description is too long.")
        if arguments["priority"].lower() not in {
            "low", "medium", "high", "urgent"
        }:
            raise AgentLLMError("Invalid ticket priority.")

    return {
        key: value.strip()
        for key, value in arguments.items()
    }


def plan_with_llm(instruction):
    """Request one tool decision and reject malformed model output."""
    if not isinstance(instruction, str) or not 3 <= len(instruction.strip()) <= 1000:
        raise AgentLLMError("Instruction must contain 3 to 1000 characters.")

    messages = [
        {
            "role": "system",
            "content": (
                "You are an enterprise ERP and CRM assistant. "
                "Choose exactly one tool that best fulfils the user's request. "
                "Use inventory_lookup only for inventory read requests. "
                "Use update_lead_status for CRM lead status changes. "
                "Use create_support_ticket for support ticket creation. "
                "Never invent identifiers or values. "
                "If required information is missing or the request is unrelated, "
                "do not call a tool; ask a concise clarification question. "
                "Do not reveal private chain-of-thought. "
                "Return only a brief user-facing decision."
            )
        },
        {
            "role": "user",
            "content": instruction.strip()
        }
    ]

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "tools": TOOLS,
                "stream": False,
                "options": {"temperature": 0}
            },
            timeout=90
        )
        response.raise_for_status()
        data = response.json()

        record_token_usage(
            OLLAMA_MODEL,
            data.get("prompt_eval_count", 0),
            data.get("eval_count", 0),
        )

    except requests.RequestException as exc:
        raise AgentLLMError(f"Could not reach local Ollama: {exc}") from exc
    except ValueError as exc:
        raise AgentLLMError("Ollama returned an invalid response.") from exc

    message = data.get("message", {})
    content = message.get("content", "")
    tool_calls = message.get("tool_calls") or []

    if not tool_calls:
        return {
            "tool_call": None,
            "decision": content.strip() or "I need more details to choose an action."
        }

    if len(tool_calls) != 1:
        raise AgentLLMError("The agent must select exactly one tool per cycle.")

    function = tool_calls[0].get("function", {})
    name = function.get("name")
    arguments = function.get("arguments", {})

    arguments = validate_tool_call(name, arguments)

    decisions = {
        "inventory_lookup": "I will retrieve the requested inventory details.",
        "update_lead_status": "I identified a CRM lead status change. Human approval is required before updating it.",
        "create_support_ticket": "I prepared a support ticket. Human approval is required before creating it."
    }

    return {
        "tool_call": {
            "name": name,
            "arguments": arguments
        },
        "decision": decisions[name]
    }
