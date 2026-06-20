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

"""FastAPI web server wrapping SafePath AI.

Serves the ADK agent endpoints alongside specialized REST APIs for:
1. Hospital/Shelter database reads.
2. Active audit logs retrieval.
3. Obfuscated location and security consent settings.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types
from pydantic import BaseModel

# Ensure root folder is on the python path
APP_DIR = Path(__file__).parent
ROOT_DIR = APP_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Setup logging/telemetry fallbacks
try:
    from app.app_utils.telemetry import setup_telemetry
    setup_telemetry()
except Exception:
    pass

try:
    import google.auth
    from google.cloud import logging as google_cloud_logging
    _, project_id = google.auth.default()
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Import ADK elements
from app.agent import app as adk_app, coordinator_agent
from app.mcp_server import SHELTERS_DB, HOSPITALS_DB, WEATHER_DB, CONTACTS_DB, ROUTING_DB, NEWS_DB
from app.audit_logger import AUDIT_LOG_FILE, write_audit_entry

# Initialize ADK runner
runner = InMemoryRunner(app=adk_app)

# Create FastAPI app incorporating default ADK paths
allow_origins = os.getenv("ALLOW_ORIGINS", "*").split(",")

# We wrap the ADK fast api app
app: FastAPI = get_fast_api_app(
    agents_dir=str(APP_DIR),
    web=False,
    allow_origins=allow_origins,
    otel_to_cloud=False,
)
app.title = "SafePath AI"
app.description = "Emergency Response & Multi-Agent Disaster Assistance Platform"

# Add CORS Middleware to ensure frontend can request easily
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- REST Schema Models ---

class ReportRequest(BaseModel):
    user_id: str = "default_user"
    session_id: str
    message: str
    role: str = "Citizen"
    location_consent: bool = False
    user_location: str = ""


# --- REST Endpoints ---

@app.get("/api/shelters")
def get_shelters():
    """Retrieve shelter database."""
    return SHELTERS_DB


@app.get("/api/hospitals")
def get_hospitals():
    """Retrieve hospital database."""
    return HOSPITALS_DB


@app.get("/api/weather")
def get_weather():
    """Retrieve weather data alerts."""
    return WEATHER_DB


@app.get("/api/contacts")
def get_contacts():
    """Retrieve emergency contacts registry."""
    return CONTACTS_DB


@app.get("/api/routes")
def get_routes():
    """Retrieve mapping routing databases."""
    return ROUTING_DB


@app.get("/api/news")
def get_news():
    """Retrieve live NDMA/IMD Indian warning news alerts feed."""
    return NEWS_DB


@app.get("/api/audit-logs")
def get_audit_logs():
    """Read and return security compliance audit logs from the JSONL file."""
    logs = []
    if os.path.exists(AUDIT_LOG_FILE):
        try:
            with open(AUDIT_LOG_FILE, "r") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line.strip()))
        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")
            raise HTTPException(status_code=500, detail="Failed to read audit logs")
    # Return reversed to show latest first
    return list(reversed(logs))


@app.post("/api/audit-logs/clear")
def clear_audit_logs():
    """Clear all entries in the audit log file."""
    try:
        with open(AUDIT_LOG_FILE, "w") as f:
            f.write("")
        write_audit_entry(
            session_id="system",
            role="Authority",
            event="AUDIT_CLEAR",
            details={"action": "Logs manually cleared by administrative command"}
        )
        return {"status": "success", "message": "Audit logs cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {e}")


@app.post("/api/report")
async def process_report(payload: ReportRequest):
    """Submit emergency report to the coordinator and execute sub-agents."""
    print("DEBUG: Checking environment variables during POST /api/report")
    print("DEBUG: GEMINI_API_KEY in env:", "GEMINI_API_KEY" in os.environ)
    print("DEBUG: GEMINI_API_KEY:", os.environ.get("GEMINI_API_KEY"))
    print("DEBUG: GOOGLE_API_KEY:", os.environ.get("GOOGLE_API_KEY"))
    user_id = payload.user_id

    session_id = payload.session_id
    message = payload.message
    
    # Audit role permission checks
    allowed_roles = ["Citizen", "Volunteer", "Emergency Responder", "Authority"]
    if payload.role not in allowed_roles:
        write_audit_entry(
            session_id=session_id,
            role="Unknown",
            event="AUTH_FAILURE",
            details={"requested_role": payload.role, "message": "Access denied for invalid role assignment."}
        )
        raise HTTPException(status_code=403, detail="Unauthorized role requested")

    # Access or create session
    session = await runner.session_service.get_session(
        app_name="app", user_id=user_id, session_id=session_id
    )
    if not session:
        session = await runner.session_service.create_session(
            app_name="app", user_id=user_id, session_id=session_id
        )

    # Populate state with user session metadata
    session.state["user_role"] = payload.role
    session.state["location_consent"] = payload.location_consent
    session.state["user_location"] = payload.user_location
    session.state["session_id"] = session_id

    response_text = ""
    try:
        # Run agent transactionally
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=genai_types.Content(
                role="user", parts=[genai_types.Part.from_text(text=message)]
            ),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
    except Exception as e:
        logger.error(f"Error running coordinator agent: {e}")
        write_audit_entry(
            session_id=session_id,
            role=payload.role,
            event="AGENT_CRASH",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Agent runtime failure: {e}")

    # Fetch updated session state
    updated_session = await runner.session_service.get_session(
        app_name="app", user_id=user_id, session_id=session_id
    )
    session_state = updated_session.state if updated_session else {}

    return {
        "response": response_text,
        "state": session_state
    }


# --- Mount Frontend Static Files ---
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

frontend_dist = ROOT_DIR / "frontend" / "dist"

if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))


# Main execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
