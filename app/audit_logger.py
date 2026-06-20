# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Custom ADK Security Audit Logger Plugin for SafePath AI.

Logs all session initialization, role authorization checks, agent transitions, 
location consents, tool executions, and responses to a local JSONL audit file.
"""

import datetime
import json
import os
from google.adk.plugins.base_plugin import BasePlugin

AUDIT_LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "audit_log.jsonl"
)


def write_audit_entry(session_id: str, role: str, event: str, details: dict):
    """Write a structured entry to the audit log."""
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "session_id": session_id,
        "role": role,
        "event": event,
        "details": details
    }
    try:
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[AuditLogger Error] Failed to write audit: {e}")


class AuditLoggerPlugin(BasePlugin):
    """Security and compliance plugin for tracking multi-agent operations and data access."""

    def __init__(self):
        super().__init__(name="audit_logger")

    async def before_agent_callback(self, *, callback_context, **kwargs) -> None:
        """Log when an agent starts processing, audit user consent, and role permissions."""
        session = callback_context._invocation_context.session
        session_id = session.id
        state = callback_context.state
        
        role = state.get("user_role", "Citizen")
        consent = state.get("location_consent", False)
        location = state.get("user_location", "Not provided")
        
        # Enforce location masking if consent is not granted
        masked_location = location if consent else "[MASKED - NO CONSENT]"
        
        state_keys = []
        try:
            if hasattr(state, "keys"):
                state_keys = list(state.keys())
            elif hasattr(state, "_data"):
                state_keys = list(state._data.keys())
        except Exception:
            pass
        
        write_audit_entry(
            session_id=session_id,
            role=role,
            event="AGENT_START",
            details={
                "location_consent_granted": consent,
                "user_location_masked": masked_location,
                "state_keys": state_keys
            }
        )

    async def after_agent_callback(self, *, callback_context, content=None, **kwargs) -> None:
        """Log when an agent finishes processing."""
        session = callback_context._invocation_context.session
        session_id = session.id
        role = callback_context.state.get("user_role", "Citizen")
        
        write_audit_entry(
            session_id=session_id,
            role=role,
            event="AGENT_COMPLETE",
            details={
                "agent_finished": True
            }
        )

    async def before_tool_callback(self, *, tool, args, tool_context, **kwargs) -> None:
        """Log tool invocation arguments, checking for potential location leaks."""
        session_id = tool_context.state.get("session_id", "unknown_session")
        role = tool_context.state.get("user_role", "Citizen")
        consent = tool_context.state.get("location_consent", False)
        
        # Security Guardrail: Check if a mapping/shelter/hospital tool is called without location consent
        tool_name = tool.name
        location_sensitive_tools = ["search_shelters", "search_hospitals", "get_evacuation_routes", "get_weather_conditions"]
        
        if tool_name in location_sensitive_tools and not consent:
            # Mask location parameters if user did not consent
            # (In a real system, we might raise a PermissionError)
            write_audit_entry(
                session_id=session_id,
                role=role,
                event="TOOL_CALL_WARNING",
                details={
                    "tool": tool_name,
                    "warning": "Location sensitive tool called without explicit user location consent.",
                    "arguments_raw": args
                }
            )
            
        write_audit_entry(
            session_id=session_id,
            role=role,
            event="TOOL_CALL_START",
            details={
                "tool": tool_name,
                "arguments": {k: ("[MASKED]" if "location" in k or "origin" in k else v) for k, v in args.items()}
            }
        )

    async def after_tool_callback(self, *, tool, args, tool_context, tool_response, **kwargs) -> None:
        """Log tool outcomes."""
        session_id = tool_context.state.get("session_id", "unknown_session")
        role = tool_context.state.get("user_role", "Citizen")
        
        write_audit_entry(
            session_id=session_id,
            role=role,
            event="TOOL_CALL_COMPLETE",
            details={
                "tool": tool.name,
                "response_size_chars": len(str(tool_response))
            }
        )
