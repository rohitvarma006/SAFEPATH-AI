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

"""MCP Server implementation for SafePath AI (India Version).

Exposes mock databases and services for Indian regions:
1. Weather Services (IMD Alerts)
2. Mapping Services / Safe Evacuation Routes
3. Hospital Databases (Guwahati, Mumbai, Dehradun, Chennai)
4. Shelter Databases (NDMA/State Centers)
5. Emergency Contacts (NDMA 1078, NDRF Helplines)
6. Real-time Indian Disaster News Feed
"""

import json
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SafePath-MCP-Server")

# --- Mock Databases (Indian Context) ---

SHELTERS_DB = [
    {
        "id": "shelter_1",
        "name": "Guwahati Town Hall Shelter",
        "address": "Mahatma Gandhi Road, Pan Bazar, Guwahati, Assam",
        "coordinates": {"lat": 26.1859, "lng": 91.7478},
        "distance_km": 1.5,
        "travel_time_mins": 10,
        "capacity": 300,
        "occupancy": 140,
        "status": "OPEN",
        "features": ["NDRF medical cell", "clean drinking water", "hot food rations", "boat transit point"]
    },
    {
        "id": "shelter_2",
        "name": "Sion Community Relief Camp",
        "address": "Sion East, Landmark Near Sion Fort, Mumbai, Maharashtra",
        "coordinates": {"lat": 19.0371, "lng": 72.8634},
        "distance_km": 2.2,
        "travel_time_mins": 18,
        "capacity": 600,
        "occupancy": 580,
        "status": "NEAR_CAPACITY",
        "features": ["BMC first aid", "dry snacks", "clean blankets", "charging docks"]
    },
    {
        "id": "shelter_3",
        "name": "Dehradun Sports Complex Hall",
        "address": "Rajpur Road, Near Parade Ground, Dehradun, Uttarakhand",
        "coordinates": {"lat": 30.3244, "lng": 78.0415},
        "distance_km": 3.8,
        "travel_time_mins": 25,
        "capacity": 400,
        "occupancy": 80,
        "status": "OPEN",
        "features": ["medical trauma support", "sleeping bags", "satellite phone center"]
    },
    {
        "id": "shelter_4",
        "name": "Chennai Central Indoor Stadium",
        "address": "Sydenhams Road, Periamet, Chennai, Tamil Nadu",
        "coordinates": {"lat": 13.0827, "lng": 80.2707},
        "distance_km": 4.5,
        "travel_time_mins": 22,
        "capacity": 1200,
        "occupancy": 1180,
        "status": "NEAR_CAPACITY",
        "features": ["cyclone refuge unit", "heavy blankets", "communal kitchen"]
    }
]

HOSPITALS_DB = [
    {
        "id": "hosp_1",
        "name": "Guwahati Medical College Hospital",
        "address": "GMC Hospital Road, Bhangagarh, Guwahati, Assam",
        "coordinates": {"lat": 26.1601, "lng": 91.7719},
        "distance_km": 2.5,
        "wait_time_mins": 30,
        "er_capacity_percentage": 65,
        "status": "OPERATIONAL",
        "specialities": ["trauma", "drowning_care", "pediatrics", "infectious_diseases"],
        "phone": "+91-361-2182"
    },
    {
        "id": "hosp_2",
        "name": "KEM General Hospital Mumbai",
        "address": "Acharya Donde Marg, Parel, Mumbai, Maharashtra",
        "coordinates": {"lat": 19.0028, "lng": 72.8422},
        "distance_km": 3.1,
        "wait_time_mins": 20,
        "er_capacity_percentage": 50,
        "status": "OPERATIONAL",
        "specialities": ["trauma_care", "monsoon_fevers", "burns_unit"],
        "phone": "+91-22-2410"
    },
    {
        "id": "hosp_3",
        "name": "Doon Government Hospital Dehradun",
        "address": "Ambedkar Marg, Near Dehradun Court, Dehradun, Uttarakhand",
        "coordinates": {"lat": 30.3164, "lng": 78.0321},
        "distance_km": 5.0,
        "wait_time_mins": 80,
        "er_capacity_percentage": 90,
        "status": "CRITICAL_CAPACITY",
        "specialities": ["orthopedics", "trauma_surgery", "emergency_medicine"],
        "phone": "+91-135-2659"
    },
    {
        "id": "hosp_4",
        "name": "Apollo Emergency Chennai",
        "address": "Greams Road, Thousand Lights, Chennai, Tamil Nadu",
        "coordinates": {"lat": 13.0601, "lng": 80.2505},
        "distance_km": 6.2,
        "wait_time_mins": 15,
        "er_capacity_percentage": 40,
        "status": "OPERATIONAL",
        "specialities": ["trauma", "cardiology", "pediatrics"],
        "phone": "+91-44-2829"
    }
]

WEATHER_DB = {
    "guwahati": {
        "status": "RED WARNING (IMD)",
        "warning": "IMD Brahmaputra Flood Warning active. Severe water rise above danger levels reported in lower valley segments.",
        "temp": "28°C",
        "precipitation": "55mm/hr",
        "wind_speed": "18 km/h",
        "forecast": "Heavy rainfall expected to continue for the next 12 hours. High risk of low-lying water logging."
    },
    "mumbai": {
        "status": "RED WARNING (IMD)",
        "warning": "Urban Flood Warning active. High monsoon tides coinciding with heavy rainfall. Avoid low-lying underpasses.",
        "temp": "26°C",
        "precipitation": "65mm/hr",
        "wind_speed": "35 km/h",
        "forecast": "High tide warnings at coastal sectors. Heavy monsoons continuing next 8 hours."
    },
    "dehradun": {
        "status": "ORANGE WARNING (IMD)",
        "warning": "Slope instability & Cloudburst Warning active. Avoid valley terrains and fragile mountain roads.",
        "temp": "19°C",
        "precipitation": "20mm/hr",
        "wind_speed": "12 km/h",
        "forecast": "Intense lightning and localized rains. Active threat of secondary mudslides."
    },
    "chennai": {
        "status": "RED WARNING (IMD)",
        "warning": "Cyclone Alert active. Severe cyclonic waterlogging reported. NDRF teams actively pre-positioned.",
        "temp": "25°C",
        "precipitation": "80mm/hr",
        "wind_speed": "62 km/h",
        "forecast": "Cyclone landfall expected in adjacent districts. Avoid venturing outdoors."
    },
    "default": {
        "status": "STABLE",
        "warning": "No active meteorological warnings from IMD.",
        "temp": "30°C",
        "precipitation": "2mm/hr",
        "wind_speed": "10 km/h",
        "forecast": "Humid and partly cloudy conditions."
    }
}

ROUTING_DB = {
    "routes": [
        {
            "name": "Route Alpha (Express Expressway Bypass)",
            "risk_score": 10,
            "status": "SAFE",
            "eta_mins": 15,
            "distance_km": 4.5,
            "blocks": [],
            "description": "Elevated bypass route clear of active water logging and landslide blocks."
        },
        {
            "name": "Route Beta (Low Valley Underpass Link)",
            "risk_score": 90,
            "status": "BLOCKED",
            "eta_mins": 35,
            "distance_km": 6.1,
            "blocks": ["Waterlogged underpass under 4ft water", "Power grid failure near junction"],
            "description": "High risk of submersion. Severe water logging reported by local traffic wardens."
        },
        {
            "name": "Route Gamma (Outer Ridge Road)",
            "risk_score": 25,
            "status": "OPEN",
            "eta_mins": 22,
            "distance_km": 5.2,
            "blocks": ["Minor debris in left lanes"],
            "description": "Alternative path through elevated segments. Safe transit conditions."
        }
    ]
}

CONTACTS_DB = {
    "guwahati": {
        "agency": "Assam State Disaster Management Cell & NDRF Guwahati",
        "hotline": "1078 or +91-361-2237221",
        "whatsapp": "+91-361-0199",
        "services": ["Flood evacuation boats", "River level monitoring", "Drinking water packets"]
    },
    "mumbai": {
        "agency": "BMC Disaster Management Cell & NDRF Maharashtra Unit",
        "hotline": "1916 or 1078",
        "whatsapp": "+91-9969-01916",
        "services": ["Water pumps deployment", "Suburban transit updates", "Triage support"]
    },
    "dehradun": {
        "agency": "Uttarakhand SDRF & Landslide Rescue Control Room",
        "hotline": "1070 or +91-135-2710334",
        "whatsapp": "+91-135-0200",
        "services": ["Rubble removal squads", "Airlift medical coordination", "Satellite links"]
    },
    "chennai": {
        "agency": "Tamil Nadu State Disaster Response Unit & NDRF Chennai Wing",
        "hotline": "1070 or 1077",
        "whatsapp": "+91-9445-869814",
        "services": ["Cyclone shelters guidance", "Submersible pump ops", "Relief kitchen centers"]
    },
    "default": {
        "agency": "NDMA National Control Cell, New Delhi",
        "hotline": "+91-11-26701728 or 1078",
        "whatsapp": "+91-11-26701000",
        "services": ["National disaster coordination", "Relief resources dispatch", "Helicopter triage links"]
    }
}

NEWS_DB = [
    {
        "id": "news_1",
        "title": "Brahmaputra River crosses danger mark in Guwahati, Assam",
        "category": "FLOOD ALERT",
        "source": "Assam State Disaster Management Authority (ASDMA)",
        "time": "Just now",
        "description": "Water levels at Guwahati Ghat rise 1.8 meters above danger limits. Low-lying sectors have initiated evacuation guidelines."
    },
    {
        "id": "news_2",
        "title": "IMD issues Red Warning for Mumbai metropolitan monsoon rains",
        "category": "WEATHER ALERT",
        "source": "India Meteorological Department (IMD)",
        "time": "10 mins ago",
        "description": "Extremely heavy rain (up to 250mm) forecast for Mumbai and coastal suburbs. High tide warning issued for afternoon hours."
    },
    {
        "id": "news_3",
        "title": "Uttarakhand NH-58 blocked near Chamoli following massive landslide",
        "category": "LANDSLIDE ALERT",
        "source": "SDRF Uttarakhand Response Cell",
        "time": "30 mins ago",
        "description": "Highway blockages reported following cloudburst in Dehradun-Joshimath sector. Clearing equipment mobilized by BRO."
    },
    {
        "id": "news_4",
        "title": "NDMA dispatches 15 additional NDRF squads to Chennai, coastal TN",
        "category": "CYCLONE PREP",
        "source": "National Disaster Management Authority (NDMA)",
        "time": "1 hour ago",
        "description": "Cyclone relief squads pre-positioned with motorboats and tree cutters along low-lying waterlogged sectors in Chennai."
    }
]


# --- Tool Definitions ---

@mcp.tool()
def get_weather_conditions(location: str, current_hazard: Optional[str] = None) -> str:
    """Retrieve current weather conditions and alerts from IMD for Indian disaster zones.

    Args:
        location: The Indian city, town, or sector coordinates (e.g. 'Guwahati', 'Mumbai', 'Chennai').
        current_hazard: Optional disaster type ('flood', 'landslide', 'cyclone', 'monsoon').

    Returns:
        JSON string containing the weather parameters, alert levels, and warning details from IMD.
    """
    loc_key = "default"
    for k in WEATHER_DB.keys():
        if k in location.lower():
            loc_key = k
            break
            
    weather_info = WEATHER_DB[loc_key].copy()
    weather_info["location"] = location
    return json.dumps(weather_info, indent=2)


@mcp.tool()
def get_evacuation_routes(origin: str, destination: str, hazards: Optional[List[str]] = None) -> str:
    """Evaluate and calculate evacuation routes avoiding road blocks and water logging.

    Args:
        origin: Starting address or city coordinates.
        destination: Intended target shelter or safe location.
        hazards: List of active hazard parameters (e.g., ['waterlogged', 'landslide_debris']).

    Returns:
        JSON string containing list of routes, each with risk score, road blocks, and status.
    """
    hazard_list = hazards or []
    routes = []
    
    for r in ROUTING_DB["routes"]:
        route_copy = r.copy()
        # Adjust risk factors based on Indian context parameters
        if route_copy["name"] == "Route Beta (Low Valley Underpass Link)" and ("flood" in origin.lower() or "waterlogged" in str(hazard_list).lower()):
            route_copy["risk_score"] = 98
            route_copy["status"] = "BLOCKED"
        routes.append(route_copy)
        
    return json.dumps({
        "origin": origin,
        "destination": destination,
        "routes": routes
    }, indent=2)


@mcp.tool()
def search_hospitals(location: str, required_speciality: Optional[str] = None) -> str:
    """Search for nearby operational medical centers and government civil hospitals in India.

    Args:
        location: The patient's Indian city to calculate distance from (e.g. 'Guwahati', 'Mumbai').
        required_speciality: Required care type ('trauma', 'drowning_care', 'orthopedics', 'cardiology').

    Returns:
        JSON string with list of matching hospitals, capacity status, and phone numbers.
    """
    results = []
    for h in HOSPITALS_DB:
        hospital_copy = h.copy()
        
        # Filter matching location
        matched_loc = False
        for city in ["guwahati", "mumbai", "dehradun", "chennai"]:
            if city in hospital_copy["address"].lower() and city in location.lower():
                matched_loc = True
                break
        
        if not matched_loc and "default" not in location.lower():
            # If not direct match, calculate a mock distance scale
            hospital_copy["distance_km"] = round(hospital_copy["distance_km"] + 5.0, 1)

        # Filter by specialty
        if required_speciality:
            if required_speciality.lower() not in [s.lower() for s in hospital_copy["specialities"]]:
                continue
                
        results.append(hospital_copy)
        
    results = sorted(results, key=lambda x: x["distance_km"])
    return json.dumps({"hospitals": results}, indent=2)


@mcp.tool()
def search_shelters(location: str, minimum_capacity: int = 0) -> str:
    """Find nearby emergency evacuation shelters, occupancy, and NDRF relief amenities.

    Args:
        location: The citizen's city or sector (e.g. 'Guwahati', 'Mumbai').
        minimum_capacity: Minimum available capacity slots required.

    Returns:
        JSON string containing ranked list of safe shelters and facilities.
    """
    results = []
    for s in SHELTERS_DB:
        shelter_copy = s.copy()
        available = shelter_copy["capacity"] - shelter_copy["occupancy"]
        shelter_copy["available_slots"] = available
        
        # Check location match
        matched_loc = False
        for city in ["guwahati", "mumbai", "dehradun", "chennai"]:
            if city in shelter_copy["address"].lower() and city in location.lower():
                matched_loc = True
                break
                
        if not matched_loc and "default" not in location.lower():
            shelter_copy["distance_km"] = round(shelter_copy["distance_km"] + 6.0, 1)

        if available < minimum_capacity:
            continue
            
        results.append(shelter_copy)
        
    results = sorted(results, key=lambda x: x["distance_km"])
    return json.dumps({"shelters": results}, indent=2)


@mcp.tool()
def get_emergency_contacts(disaster_type: str) -> str:
    """Get critical NDMA, SDRF and national relief helplines based on location.

    Args:
        disaster_type: The city location or disaster context (e.g., 'Guwahati', 'Mumbai').

    Returns:
        JSON string with NDMA/SDRF hotlines and WhatsApp rescue cell channels.
    """
    dtype = "default"
    for k in CONTACTS_DB.keys():
        if k in disaster_type.lower():
            dtype = k
            break
        
    return json.dumps(CONTACTS_DB[dtype], indent=2)


@mcp.tool()
def get_realtime_news(region: str = "India") -> str:
    """Get real-time disaster alerts, weather updates, and highway blocks from NDMA and IMD.

    Args:
        region: The target state or national region (default 'India').

    Returns:
        JSON string containing a list of live emergency announcements.
    """
    results = []
    for news in NEWS_DB:
        if region.lower() == "india" or region.lower() in news["title"].lower() or region.lower() in news["description"].lower():
            results.append(news)
            
    return json.dumps({"news_feed": results or NEWS_DB}, indent=2)


if __name__ == "__main__":
    mcp.run()
