# SafePath AI - Multi-Agent Emergency Response & Evacuation Assistance Platform

SafePath AI is an emergency-response platform built on the **Google Agent Development Kit (ADK)** and **FastAPI** with a modern **React dashboard** frontend. It serves as a mock command center and user portal for citizens and emergency authorities to coordinate safety assessment, shelter discoveries, navigation routing, medical dispatch, supply checklists, and broadcast alerts during severe disaster scenarios (floods, earthquakes, fires, etc.).

This project is built for the **"Agents for Good" track of the Kaggle AI Agents Capstone Project**.

---

## 📖 Key Capabilities

### 1. Collaborative Multi-Agent Mesh
Exposes 6 specialized AI sub-agents orchestrated by a central coordinator:
* **Disaster Assessment Agent**: Evaluates descriptions & warnings to classify incident severity.
* **Shelter Discovery Agent**: Queries open shelter coordinates and available slots.
* **Safe Route Agent**: Mapped pathways avoiding hazard road blockages.
* **Medical Assistance Agent**: Dispatches hospital registries and provides first-aid guides.
* **Emergency Supply Agent**: Compiles custom checklists based on disaster type.
* **Communication Agent**: Pre-drafts safety SMS broadcasts and logging tickets.

### 2. Privacy & Role-Based Access Security
* **User Location Consent**: Evaluated by a custom `AuditLoggerPlugin`. If a user opts out of sharing location coordinates, the platform masks/obfuscates location values before passing them to internal tools.
* **Simulated Roles**: Citizenship dashboards, Volunteer portals, Emergency Responder views, and Administrative Command lines. 
* **JSONL Threat Logging**: Writes compliance security trails into `audit_log.jsonl`.

### 3. Integrated Mock MCP Server
Provides standard tools connecting to local databases matching:
* Weather warnings (`get_weather_conditions`)
* Location pathfinding (`get_evacuation_routes`)
* Operational hospitals (`search_hospitals`)
* Shelter registries (`search_shelters`)
* Helpline directories (`get_emergency_contacts`)

---

## 📂 Project Structure

```
safepath-ai/
├── app/
│   ├── agent.py         # Multi-agent orchestrations & model fallbacks
│   ├── audit_logger.py  # Custom ADK security AuditLoggerPlugin
│   ├── fast_api_app.py  # FastAPI app serving REST APIs & mounting frontend
│   └── mcp_server.py    # Python FastMCP server with mock databases
├── frontend/            # React client Vite configuration
│   ├── src/
│   │   ├── App.tsx      # Main application view with interactive SVG map
│   │   ├── index.css    # Custom glassmorphic dark-mode CSS stylesheet
│   │   └── main.tsx
│   ├── index.html       # Configured with SEO title & description
│   └── package.json     # Node configurations
├── tests/
│   └── eval/
│       └── datasets/
│           └── safepath_eval.json  # Multi-case disaster evaluation scenarios
├── audit_log.jsonl      # Compliance security audit trails (auto-generated)
├── pyproject.toml       # Python package dependencies
└── README.md            # Product documentation
```

---

## 🚀 Running SafePath AI Locally

### Prerequisites
1. **Python 3.10+** (managed with `uv`)
2. **Node.js** (for building the frontend client)

### Step 1: Install Dependencies
Install Python dependencies and Node modules:
```bash
# In safepath-ai/
agents-cli install

# In safepath-ai/frontend/
npm install
```

### Step 2: Set Environment Variables
Configure your local API credentials inside `safepath-ai/app/.env` (and `safepath-ai/.env`):
```env
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
MODEL_NAME="gemini-2.5-flash"
PORT=8000
```

### Step 3: Build the Frontend
Compile static frontend modules:
```bash
cd frontend
npm run build
cd ..
```

### Step 4: Run the Application
Start the FastAPI server. It mounts and serves the static production UI on port `8000`:
```bash
uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000
```
Open your browser and navigate to **[http://localhost:8000/](http://localhost:8000/)**.

---

## 📊 Evaluation and Testing

To verify the agent logic against the local evaluation dataset:
```bash
agents-cli eval generate --dataset tests/eval/datasets/safepath_eval.json
agents-cli eval grade
```
*(Requires a valid `GEMINI_API_KEY` set in the environment variables).*
