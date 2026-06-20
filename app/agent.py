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

"""SafePath AI - Multi-Agent System (India Edition).

Orchestrates 6 specialized agents:
1. Disaster Assessment
2. Shelter Discovery
3. Safe Route
4. Medical Assistance
5. Emergency Supply
6. Communication

Bound together under a central Coordinator agent, communicating via session state
and integrated with a local MCP Server providing Indian NDMA, IMD, and SDRF database access.
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from app.audit_logger import AuditLoggerPlugin

# --- Environment & Authentication Config ---

# Handle API Key configuration
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
else:
    # Try loading Google ADC credentials if available
    try:
        import google.auth
        _, project_id = google.auth.default()
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    except Exception:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

# Choose model
model_name = os.environ.get("MODEL_NAME", "gemini-2.5-flash")
model = Gemini(model=model_name)

# --- MCP Toolset Integration ---

# Spawn our local Python MCP server via stdio
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp_server"],
        ),
        timeout=120,
    )
)

# --- Sub-Agent Definitions ---

disaster_assessment_agent = Agent(
    name="disaster_assessment_agent",
    model=model,
    description="Analyzes emergency reports in India, classifies disaster type, severity level, risk scores, and checks IMD weather warnings and NDMA real-time news alerts.",
    instruction="""You are the Disaster Assessment Agent for India.
    
Analyze the user's disaster report. Use `get_weather_conditions` to check current IMD warnings and `get_realtime_news` to fetch active NDMA alert feeds for their region (e.g. Guwahati, Mumbai, Dehradun, Chennai).
Identify:
1. Disaster Type (e.g. Flood, Monsoon waterlogging, Landslide, Cyclone)
2. Severity Level (Low, Medium, High, Critical)
3. Immediate threats (e.g. rising Brahmaputra river level in Guwahati, landslide blockage in Dehradun, high tide in Mumbai)
4. A computed risk score (1-100)

Write these findings clearly to the shared state by calling or outputting them:
- `disaster_type`
- `disaster_severity`
- `disaster_assessment` (detailed summary combining the report and latest live news warning updates)

When complete, transfer control back to the coordinator.""",
    tools=[mcp_toolset],
    output_key="disaster_assessment"
)

shelter_discovery_agent = Agent(
    name="shelter_discovery_agent",
    model=model,
    description="Finds nearby open evacuation shelters in Indian sectors, calculates distance, and selects the safest relief camp.",
    instruction="""You are the Shelter Discovery Agent for India.

Locate the closest open relief shelter for the citizen (use `search_shelters` with their city, e.g. 'Guwahati', 'Mumbai').
Filter out shelters that are FULL or closed. Check available capacity.
Recommend the safest shelter (e.g., Guwahati Town Hall Shelter, Sion Community Relief Camp), calculate travel distance, transit time, and note facilities like NDRF units, blankets, and community kitchens.

Save this shelter recommendation to state:
- `shelter_info`

When complete, transfer control back to the coordinator.""",
    tools=[mcp_toolset],
    output_key="shelter_info"
)

safe_route_agent = Agent(
    name="safe_route_agent",
    model=model,
    description="Calculates safe evacuation routes to recommended shelters in India, avoiding active water logging, highway blockages, and landslides.",
    instruction="""You are the Safe Route Agent for India.

Determine safe routes from the user's starting location to the recommended shelter (use `get_evacuation_routes` tool).
Identify road blocks, flooded underpasses, or active landslide hazards (e.g. on NH-58, S V Road, etc.).
Recommend a primary safe route (e.g., Route Alpha Elevated Bypass) and note road blocks or risk factor details.

Save this route recommendation to state:
- `route_info`

When complete, transfer control back to the coordinator.""",
    tools=[mcp_toolset],
    output_key="route_info"
)

medical_assistance_agent = Agent(
    name="medical_assistance_agent",
    model=model,
    description="Finds nearby operational Indian government and civil hospitals, lists trauma phone contacts, and provides emergency care instructions.",
    instruction="""You are the Medical Assistance Agent for India.

Check for nearby emergency medical centers using `search_hospitals` based on user city (e.g. Guwahati Medical College, KEM Hospital Mumbai).
Specify hospital capacity, wait times, contact numbers, and specialities.
Provide immediate emergency first-aid care steps tailored to their disaster type (e.g. monsoon fever triage, drowning advice for floods, mudslide trauma treatment).

Save this medical advice and hospital details to state:
- `medical_info`

When complete, transfer control back to the coordinator.""",
    tools=[mcp_toolset],
    output_key="medical_info"
)

emergency_supply_agent = Agent(
    name="emergency_supply_agent",
    model=model,
    description="Provides lists of essential emergency supplies, dry rations, and checklists custom-tailored to Indian disaster contexts.",
    instruction="""You are the Emergency Supply Agent for India.

Recommend essential emergency response items based on the classified `disaster_type`. Tailor these to India (e.g. clean drinking water, dry food rations like biscuits/choora, first aid kits, emergency flashlights, power banks).
Provide specific quantities and a quick preparation checklist.

Save these supply checklists to state:
- `supply_recommendations`

When complete, transfer control back to the coordinator.""",
    output_key="supply_recommendations"
)

communication_agent = Agent(
    name="communication_agent",
    model=model,
    description="Generates emergency SMS broadcasts for family and formal incident reports for NDMA, SDRF and rescue dispatch teams.",
    instruction="""You are the Communication Agent for India.

Use `get_emergency_contacts` for SDMA, NDRF, and local municipal hotlines (e.g. BMC 1916, Assam control room).
Compose:
1. An SMS-ready alert message for the user's family members (needs to be concise, contain location status, recommended shelter, and state "We are safe/heading there").
2. A formal emergency incident summary for responders and NDRF relief dispatch teams (containing location, severity, family size, shelter destination, and immediate rescue requirements).

Save these messages to state:
- `communication_alerts`

When complete, transfer control back to the coordinator.""",
    tools=[mcp_toolset],
    output_key="communication_alerts"
)

# --- Coordinator Agent Definition ---

coordinator_agent = Agent(
    name="safepath_coordinator",
    model=model,
    description="Central dispatcher coordinating assessment, shelter, routing, medical, supply, and alerts for Indian disaster situations.",
    instruction="""You are the SafePath AI Coordinator, a multi-agent emergency dispatch assistant for India.
    
Your goal is to guide the user and orchestrate sub-agents to compile a complete disaster response report.

Shared State attributes:
- `disaster_assessment`: Computed by disaster_assessment_agent
- `shelter_info`: Computed by shelter_discovery_agent
- `route_info`: Computed by safe_route_agent
- `medical_info`: Computed by medical_assistance_agent
- `supply_recommendations`: Computed by emergency_supply_agent
- `communication_alerts`: Computed by communication_agent

Steps to take when a user reports a disaster:
1. Hand off to `disaster_assessment_agent` to assess the situation and read live NDMA news alerts.
2. Hand off to `shelter_discovery_agent` to search for the closest shelter.
3. Hand off to `safe_route_agent` to map out the safest route to that shelter.
4. Hand off to `medical_assistance_agent` to locate nearby hospitals and provide emergency first-aid tips.
5. Hand off to `emergency_supply_agent` to identify supply checklists.
6. Hand off to `communication_agent` to prepare alert SMS and agency logs.

After all sub-agents have run and written their findings, aggregate their data and present a comprehensive emergency response report to the citizen.
Structure your report clearly:
- **Disaster Assessment**: Type, Severity, and Dangers (mention any live IMD/NDMA warning inputs)
- **Safe Evacuation Shelter**: Recommended shelter name, address, and amenities
- **Evacuation Path**: Safest route details and risk notes
- **Emergency Medical Care**: Nearby hospital, ER status, and immediate first-aid guidance
- **Critical Supplies**: Recommended checklist
- **Alert Messages**: Pre-drafted SMS for family and details for responders (referencing municipal hotlines like BMC 1916 or ASDMA helplines)

Ensure you sound calm, authoritative, supportive, and urgent.""",
    sub_agents=[
        disaster_assessment_agent,
        shelter_discovery_agent,
        safe_route_agent,
        medical_assistance_agent,
        emergency_supply_agent,
        communication_agent,
    ]
)

# --- App Definition ---

app = App(
    root_agent=coordinator_agent,
    name="app",
    plugins=[AuditLoggerPlugin()]
)
