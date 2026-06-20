// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import React, { useState, useEffect, useRef } from "react";
import { 
  ShieldAlert, 
  MapPin, 
  Send, 
  Shield, 
  Activity, 
  Home, 
  HeartPulse, 
  PackageCheck, 
  MessageSquareShare, 
  Trash2, 
  RefreshCw
} from "lucide-react";

// --- Types & Interfaces ---

interface Message {
  sender: "user" | "bot";
  text: string;
  timestamp: string;
}

interface AuditLog {
  timestamp: string;
  session_id: string;
  role: string;
  event: string;
  details: Record<string, any>;
}

interface NewsAlert {
  id: string;
  title: string;
  category: string;
  source: string;
  time: string;
  description: string;
}

interface Shelter {
  id: string;
  name: string;
  address: string;
  coordinates: { lat: number; lng: number };
  distance_km: number;
  travel_time_mins: number;
  capacity: number;
  occupancy: number;
  status: string;
  features: string[];
}

interface Hospital {
  id: string;
  name: string;
  address: string;
  coordinates: { lat: number; lng: number };
  distance_km: number;
  wait_time_mins: number;
  er_capacity_percentage: number;
  status: string;
  specialities: string[];
  phone: string;
}

const BACKEND_URL = "http://localhost:8000";

// Standard Coordinate locations on our 800x500 Grid Map (India Geo Version)
const MAP_COORDINATES: Record<string, { x: number; y: number }> = {
  // Citizen Starting Points (Major Indian Cities)
  "Guwahati (Assam)": { x: 580, y: 210 },
  "Mumbai (Maharashtra)": { x: 280, y: 310 },
  "Dehradun (Uttarakhand)": { x: 390, y: 130 },
  "Chennai (Tamil Nadu)": { x: 370, y: 430 },
  "default": { x: 400, y: 250 },

  // Shelters
  "Guwahati Town Hall Shelter": { x: 595, y: 195 },
  "Sion Community Relief Camp": { x: 265, y: 325 },
  "Dehradun Sports Complex Hall": { x: 375, y: 120 },
  "Chennai Central Indoor Stadium": { x: 385, y: 415 },

  // Hospitals
  "Guwahati Medical College Hospital": { x: 605, y: 220 },
  "KEM General Hospital Mumbai": { x: 295, y: 295 },
  "Doon Government Hospital Dehradun": { x: 405, y: 140 },
  "Apollo Emergency Chennai": { x: 355, y: 440 }
};

export default function App() {
  const [role, setRole] = useState<string>("Citizen");
  const [session_id] = useState<string>(() => "session_" + Math.random().toString(36).substr(2, 9));
  const [message, setMessage] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "bot",
      text: "SafePath AI Emergency Response Active (India Edition). Please state your location, hazard conditions, and immediate needs so that our multi-agent system can coordinate an evacuation plan.",
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [loading, setLoading] = useState<boolean>(false);

  // User details
  const [locationConsent, setLocationConsent] = useState<boolean>(true);
  const [userLocation, setUserLocation] = useState<string>("Guwahati (Assam)");

  // Live Alerts News feed State
  const [newsAlerts, setNewsAlerts] = useState<NewsAlert[]>([]);

  // Agent State Outcomes
  const [disasterType, setDisasterType] = useState<string>("");
  const [severity, setSeverity] = useState<string>("");
  const [assessmentSummary, setAssessmentSummary] = useState<string>("");
  const [recommendedShelter, setRecommendedShelter] = useState<string>("");
  const [recommendedRoute, setRecommendedRoute] = useState<string>("");
  const [hospitalInfo, setHospitalInfo] = useState<string>("");
  const [supplyList, setSupplyList] = useState<string[]>([]);
  const [draftedSms, setDraftedSms] = useState<string>("");

  // DB States
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Sync DB structures on load & role checks
  useEffect(() => {
    fetchDBData();
  }, [role]);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const fetchDBData = async () => {
    try {
      const resShelters = await fetch(`${BACKEND_URL}/api/shelters`);
      const sheltersData = await resShelters.json();
      setShelters(sheltersData);

      const resHosp = await fetch(`${BACKEND_URL}/api/hospitals`);
      const hospData = await resHosp.json();
      setHospitals(hospData);

      const resNews = await fetch(`${BACKEND_URL}/api/news`);
      const newsData = await resNews.json();
      setNewsAlerts(newsData);

      if (role === "Authority") {
        const resAudit = await fetch(`${BACKEND_URL}/api/audit-logs`);
        const auditData = await resAudit.json();
        setAuditLogs(auditData);
      }
    } catch (err) {
      console.error("Failed to connect to FastAPI backend:", err);
    }
  };

  const handleClearLogs = async () => {
    if (!window.confirm("Are you sure you want to clear the security audit logs?")) return;
    try {
      await fetch(`${BACKEND_URL}/api/audit-logs/clear`, { method: "POST" });
      fetchDBData();
    } catch (err) {
      console.error(err);
    }
  };

  // Run the multi-agent system workflow
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMsg = message;
    setMessage("");
    setMessages(prev => [...prev, { sender: "user", text: userMsg, timestamp: new Date().toLocaleTimeString() }]);
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/api/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "default_user",
          session_id,
          message: userMsg,
          role,
          location_consent: locationConsent,
          user_location: userLocation
        })
      });

      if (!res.ok) throw new Error("Agent failed to respond");
      
      const data = await res.json();
      setMessages(prev => [...prev, { sender: "bot", text: data.response, timestamp: new Date().toLocaleTimeString() }]);

      // Extract states updated by ADK sub-agents
      const state = data.state || {};
      if (state.disaster_assessment) {
        // Parse basic details from unstructured text or state values
        setDisasterType(state.disaster_type || "Incident Detected");
        setSeverity(state.disaster_severity || "High");
        setAssessmentSummary(state.disaster_assessment);
      }
      if (state.shelter_info) {
        setRecommendedShelter(state.shelter_info);
      }
      if (state.route_info) {
        setRecommendedRoute(state.route_info);
      }
      if (state.medical_info) {
        setHospitalInfo(state.medical_info);
      }
      if (state.supply_recommendations) {
        // split supplies by list bullets if returning raw text
        const supplies = state.supply_recommendations
          .split("\n")
          .map((s: string) => s.replace(/^[-*#\s\d.]+/g, "").trim())
          .filter((s: string) => s.length > 2);
        setSupplyList(supplies);
      }
      if (state.communication_alerts) {
        setDraftedSms(state.communication_alerts);
      }

      // Re-fetch databases and logs
      fetchDBData();
    } catch (err) {
      setMessages(prev => [...prev, { 
        sender: "bot", 
        text: "Error contacting response agent network. Please verify the FastAPI backend server is active.", 
        timestamp: new Date().toLocaleTimeString() 
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Helper: extract coordinates for rendering mapping features
  const getUserPoint = () => {
    return MAP_COORDINATES[userLocation] || MAP_COORDINATES["default"];
  };

  const getShelterPoint = () => {
    // Try to match shelter name inside recommendedShelter text
    for (const name of Object.keys(MAP_COORDINATES)) {
      if (recommendedShelter.toLowerCase().includes(name.toLowerCase())) {
        return MAP_COORDINATES[name];
      }
    }
    return null;
  };

  const getHospitalPoint = () => {
    for (const name of Object.keys(MAP_COORDINATES)) {
      if (hospitalInfo.toLowerCase().includes(name.toLowerCase())) {
        return MAP_COORDINATES[name];
      }
    }
    return null;
  };

  const citizenPoint = getUserPoint();
  const shelterPoint = getShelterPoint();
  const hospitalPoint = getHospitalPoint();

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="app-header">
        <div className="brand-section">
          <ShieldAlert className="brand-logo" size={32} />
          <div className="brand-title">
            <h1>SafePath AI</h1>
            <div className="brand-subtitle">Emergency Response Dispatch Network</div>
          </div>
        </div>

        <div className="header-controls">
          <div className="role-container">
            <span className="role-label">System Access Mode:</span>
            <select 
              value={role} 
              onChange={(e) => setRole(e.target.value)}
              className="role-select"
            >
              <option value="Citizen">Citizen / User Dashboard</option>
              <option value="Volunteer">Volunteer Care Portal</option>
              <option value="Emergency Responder">Emergency First-Responder</option>
              <option value="Authority">Incident Command / Admin</option>
            </select>
          </div>
          <div className={`role-badge role-${role.toLowerCase().replace(" ", "")}`}>
            <Shield size={14} />
            {role}
          </div>
        </div>
      </header>

      {/* Real-time Indian Alert Ticker */}
      {newsAlerts.length > 0 && (
        <div className="alert-ticker-container">
          <span className="alert-ticker-title">
            <ShieldAlert size={12} className="inline-block mr-1" />
            Live alerts
          </span>
          <div className="alert-ticker-track">
            {/* Render twice for seamless looping marquee */}
            {[...newsAlerts, ...newsAlerts].map((alert, idx) => (
              <div key={idx} className="alert-ticker-item">
                <span className={`alert-ticker-badge ${alert.category.toLowerCase().replace(" ", "-")}`}>
                  {alert.category}
                </span>
                <span className="alert-ticker-source">[{alert.source}]:</span>
                <span className="alert-ticker-text">{alert.title} — {alert.description}</span>
                <span className="alert-ticker-time">{alert.time}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Grid View */}
      <div className="dashboard-grid">
        {/* Panel 1: Chat Terminal */}
        <div className="panel">
          <div className="panel-header">
            <h2><ShieldAlert size={16} /> Emergency Terminal</h2>
            <RefreshCw size={14} className="text-muted cursor-pointer" onClick={() => window.location.reload()} />
          </div>

          <div className="chat-container">
            <div className="chat-messages">
              {messages.map((msg, index) => (
                <div key={index} className={`message-bubble ${msg.sender}`}>
                  <div>{msg.text}</div>
                  <div className="message-metadata">
                    <span>{msg.sender === "user" ? role : "SafePath Coordinator"}</span>
                    <span>•</span>
                    <span>{msg.timestamp}</span>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Chat control strip */}
            <form onSubmit={handleSendMessage} className="chat-input-area">
              <div className="location-security-strip">
                <label className="location-consent-label">
                  <input 
                    type="checkbox" 
                    checked={locationConsent}
                    onChange={(e) => setLocationConsent(e.target.checked)}
                  />
                  <span className="text-secondary">Share GPS Location</span>
                </label>

                {locationConsent ? (
                  <select 
                    value={userLocation}
                    onChange={(e) => setUserLocation(e.target.value)}
                    className="location-field-compact"
                  >
                    <option value="Guwahati (Assam)">Guwahati (Assam)</option>
                    <option value="Mumbai (Maharashtra)">Mumbai (Maharashtra)</option>
                    <option value="Dehradun (Uttarakhand)">Dehradun (Uttarakhand)</option>
                    <option value="Chennai (Tamil Nadu)">Chennai (Tamil Nadu)</option>
                  </select>
                ) : (
                  <span className="text-muted text-xs">GPS Masked (Audited)</span>
                )}
              </div>

              <div className="input-row">
                <input 
                  type="text" 
                  value={message} 
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="e.g. Flood water has entered Guwahati town area, need evacuation paths..."
                  className="chat-input"
                  disabled={loading}
                />
                <button type="submit" className="send-btn" disabled={loading || !message.trim()}>
                  <Send size={16} />
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Panel 2: Center Interactive Simulated Map or Admin View */}
        {role !== "Authority" ? (
          <div className="map-container">
            {/* Google Maps Overlay UI */}
            <div className="google-maps-overlay-container">
              {/* Search Box */}
              <div className="google-maps-searchbox">
                <span className="menu-icon">☰</span>
                <input 
                  type="text" 
                  value={disasterType ? `${disasterType.toUpperCase()} EMERGENCY CELL` : "Search SafePath Map / India"} 
                  readOnly 
                />
                <span className="search-icon">🔍</span>
                <div className="divider"></div>
                <div className="directions-btn" title="Route Guidance">
                  ➤
                </div>
              </div>

              {/* Traffic/Hazards Legend */}
              <div className="google-maps-legend">
                <div className="legend-item">
                  <span className="legend-line" style={{ backgroundColor: "#4285f4", display: "inline-block" }}></span>
                  <span>Active Evac Route</span>
                </div>
                <div className="legend-item">
                  <span className="legend-line" style={{ backgroundColor: "#1a73e8", display: "inline-block" }}></span>
                  <span>Medical Route</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: "#0f9d58" }}></span>
                  <span>Relief Shelter (Green)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot" style={{ backgroundColor: "#4285f4" }}></span>
                  <span>Civil Hospital (Blue)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-line" style={{ backgroundColor: "#f2a134", display: "inline-block" }}></span>
                  <span>National Highway</span>
                </div>
              </div>

              {/* Layers card bottom left */}
              <div className="google-maps-left-controls">
                <div className="google-maps-layers-card">
                  🗺️ Layers (Hybrid)
                </div>
              </div>

              {/* Navigation widgets bottom right */}
              <div className="google-maps-right-controls">
                <div className="google-maps-btn" title="Compass">🧭</div>
                <div className="google-maps-btn pegman" title="Street View (Pegman)">👤</div>
                <div className="google-maps-btn" title="Zoom In">+</div>
                <div className="google-maps-btn" title="Zoom Out">−</div>
              </div>
            </div>

            {/* Map Overlay Stats (Floated Right to align with Searchbox) */}
            <div className="map-status-overlay" style={{ left: "auto", right: "20px", display: "flex", gap: "10px", pointerEvents: "none" }}>
              <div className="overlay-card" style={{ pointerEvents: "auto" }}>
                <div className="overlay-status-dot active"></div>
                <div>
                  <div className="overlay-title">Incident Type</div>
                  <div className="overlay-value text-accent-red">
                    {disasterType ? disasterType.toUpperCase() : "NO ACTIVE DISASTER"}
                  </div>
                </div>
              </div>

              <div className="overlay-card" style={{ pointerEvents: "auto" }}>
                <div className="overlay-title">Current Location</div>
                <div className="overlay-value">
                  {locationConsent ? userLocation : "Obfuscated Coordinates"}
                </div>
              </div>
            </div>

            {/* Interactive SVG Map (India Geo Silhouette - Google Maps Dark Style) */}
            <div className="map-svg-wrapper" style={{ padding: "0" }}>
              <svg className="svg-disaster-map" viewBox="0 0 800 500" style={{ backgroundColor: "#17263c", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.12)" }}>
                {/* Background Water Grid */}
                <defs>
                  <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
                    <path d="M 60 0 L 0 0 0 60" fill="none" stroke="rgba(255, 255, 255, 0.015)" strokeWidth="0.5" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />

                {/* Ocean Names */}
                <text x="140" y="440" fill="rgba(255, 255, 255, 0.08)" fontSize="10" fontWeight="700" letterSpacing="0.2em">ARABIAN SEA</text>
                <text x="560" y="440" fill="rgba(255, 255, 255, 0.08)" fontSize="10" fontWeight="700" letterSpacing="0.2em">BAY OF BENGAL</text>
                <text x="350" y="485" fill="rgba(255, 255, 255, 0.06)" fontSize="9" fontWeight="700" letterSpacing="0.3em">INDIAN OCEAN</text>

                {/* Realistic Google Maps Satellite & Terrain Background Underlay */}
                <image href="/india_google_map_bg.png" x="150" y="0" width="500" height="500" opacity="0.8" />

                {/* India Outline Boundary Overlay for crisp mapping */}
                <path 
                  d="M 390 40 C 375 70 340 100 320 120 C 300 140 280 170 270 200 C 260 215 240 220 230 230 C 220 240 210 250 210 265 C 210 280 230 290 250 290 C 265 290 275 310 280 330 C 290 370 310 410 335 460 C 345 480 350 485 355 485 C 360 485 365 470 370 450 C 385 410 405 375 425 340 C 445 305 475 285 490 275 C 495 270 495 260 495 250 C 495 240 510 235 520 235 C 530 235 535 250 545 255 C 555 260 575 260 590 250 C 605 240 625 210 630 195 C 635 180 620 175 600 180 C 580 185 550 180 535 190 C 525 180 520 165 515 150 C 510 165 500 170 490 175 C 470 155 440 135 425 110 C 415 90 410 65 390 40 Z" 
                  fill="none"
                  stroke="rgba(255, 255, 255, 0.15)"
                  strokeWidth="1.5"
                />

                {/* Ganges River Path (Blue Water) */}
                <path d="M 390 130 C 415 150, 440 165, 470 190 T 520 245" fill="none" stroke="#17263c" strokeWidth="4" />
                <path d="M 390 130 C 415 150, 440 165, 470 190 T 520 245" fill="none" stroke="#2b5797" strokeWidth="2" />
                {disasterType.toLowerCase().includes("flood") && userLocation === "Dehradun (Uttarakhand)" && (
                  <path d="M 390 130 C 415 150, 440 165, 470 190 T 520 245" className="map-river-flood" strokeWidth="6" />
                )}

                {/* Brahmaputra River Path (Blue Water) */}
                <path d="M 630 195 C 610 200, 580 205, 560 210 T 520 245" fill="none" stroke="#17263c" strokeWidth="4" />
                <path d="M 630 195 C 610 200, 580 205, 560 210 T 520 245" fill="none" stroke="#2b5797" strokeWidth="2" />
                {disasterType.toLowerCase().includes("flood") && userLocation === "Guwahati (Assam)" && (
                  <path d="M 630 195 C 610 200, 580 205, 560 210 T 520 245" className="map-river-flood" strokeWidth="6" />
                )}

                {/* Base National Highways (Google Maps Highway Yellow/Orange) */}
                {/* NH-44: North-South */}
                <path d="M 390 130 L 375 220 L 340 330 L 370 430" fill="none" stroke="#2c3540" strokeWidth="4" strokeLinecap="round" />
                <path d="M 390 130 L 375 220 L 340 330 L 370 430" fill="none" stroke="#f2a134" strokeWidth="2.5" strokeLinecap="round" opacity="0.8" />

                {/* NH-2: East-West */}
                <path d="M 280 310 L 340 330 L 505 250 L 580 210" fill="none" stroke="#2c3540" strokeWidth="4" strokeLinecap="round" />
                <path d="M 280 310 L 340 330 L 505 250 L 580 210" fill="none" stroke="#f2a134" strokeWidth="2.5" strokeLinecap="round" opacity="0.8" />

                {/* Major Indian Cities Labels (Google Map style gray circles & labels) */}
                <g transform="translate(370, 160)">
                  <circle cx="0" cy="0" r="3" fill="#fff" stroke="#9ca3af" strokeWidth="1" />
                  <text x="6" y="3" fill="#9ca3af" fontSize="8" fontWeight="600">New Delhi</text>
                </g>
                <g transform="translate(505, 250)">
                  <circle cx="0" cy="0" r="3" fill="#fff" stroke="#9ca3af" strokeWidth="1" />
                  <text x="6" y="3" fill="#9ca3af" fontSize="8" fontWeight="600">Kolkata</text>
                </g>
                <g transform="translate(330, 400)">
                  <circle cx="0" cy="0" r="3" fill="#fff" stroke="#9ca3af" strokeWidth="1" />
                  <text x="6" y="3" fill="#9ca3af" fontSize="8" fontWeight="600">Bengaluru</text>
                </g>

                {/* City-Specific Hazard Overlays */}
                {disasterType && (
                  <>
                    {/* Mumbai (Maharashtra) Monsoon Flooding / Storm Surge */}
                    {userLocation === "Mumbai (Maharashtra)" && (
                      <g>
                        <circle cx="280" cy="310" r="22" fill="none" stroke="#4285f4" strokeWidth="2.5" className="pulse-hazard-glow" />
                        <circle cx="280" cy="310" r="45" fill="none" stroke="#4285f4" strokeWidth="1.5" strokeDasharray="4 4" className="pulse-hazard-glow" />
                        <text x="280" y="345" textAnchor="middle" fill="#4285f4" fontSize="8" fontWeight="800" style={{ textShadow: "0 1px 2px rgba(0,0,0,0.8)" }}>STORM SURGE ACTIVE</text>
                      </g>
                    )}

                    {/* Guwahati (Assam) Brahmaputra River Basin Flooding */}
                    {userLocation === "Guwahati (Assam)" && (
                      <g>
                        <circle cx="580" cy="210" r="25" fill="none" stroke="#4285f4" strokeWidth="2.5" className="pulse-hazard-glow" />
                        <text x="580" y="245" textAnchor="middle" fill="#4285f4" fontSize="8" fontWeight="800" style={{ textShadow: "0 1px 2px rgba(0,0,0,0.8)" }}>BASIN FLOOD ACTIVE</text>
                      </g>
                    )}

                    {/* Dehradun (Uttarakhand) Landslide Hazard Blockage */}
                    {userLocation === "Dehradun (Uttarakhand)" && (
                      <g transform="translate(390, 130)">
                        <circle cx="0" cy="0" r="20" fill="none" stroke="var(--accent-red)" strokeWidth="2" className="pulse-hazard-glow" />
                        <polygon points="-6,5 6,5 0,-8" fill="var(--accent-red)" className="hazard-icon-pulse" />
                        <text x="0" y="25" textAnchor="middle" fill="var(--accent-red)" fontSize="8" fontWeight="800" style={{ textShadow: "0 1px 2px rgba(0,0,0,0.8)" }}>LANDSLIDE BLOCK</text>
                      </g>
                    )}

                    {/* Chennai (Tamil Nadu) Cyclone Wind spiral */}
                    {userLocation === "Chennai (Tamil Nadu)" && (
                      <g>
                        <circle cx="370" cy="430" r="25" fill="none" stroke="var(--accent-green)" strokeWidth="2.5" strokeDasharray="8 4" className="cyclone-ring" />
                        <circle cx="370" cy="430" r="40" fill="none" stroke="var(--accent-green)" strokeWidth="1.5" strokeDasharray="12 6" className="cyclone-ring-2" />
                        <text x="370" y="468" textAnchor="middle" fill="var(--accent-green)" fontSize="8" fontWeight="800" style={{ textShadow: "0 1px 2px rgba(0,0,0,0.8)" }}>CYCLONE CELL ACTIVE</text>
                      </g>
                    )}
                  </>
                )}

                {/* Evacuation Route path flow (Google Maps Navigation Blue Line) */}
                {locationConsent && citizenPoint && shelterPoint && (
                  <g>
                    {/* Shadow Border */}
                    <path 
                      d={`M ${citizenPoint.x} ${citizenPoint.y} Q 400 300 ${shelterPoint.x} ${shelterPoint.y}`} 
                      fill="none"
                      stroke="#155cb0"
                      strokeWidth="6"
                      strokeLinecap="round"
                    />
                    {/* Active Navigation line */}
                    <path 
                      d={`M ${citizenPoint.x} ${citizenPoint.y} Q 400 300 ${shelterPoint.x} ${shelterPoint.y}`} 
                      fill="none"
                      stroke="#4285f4"
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      className="map-route-evacuation" 
                    />
                  </g>
                )}

                {/* Hospital Route path flow */}
                {locationConsent && citizenPoint && hospitalPoint && (
                  <g>
                    <path 
                      d={`M ${citizenPoint.x} ${citizenPoint.y} Q 350 250 ${hospitalPoint.x} ${hospitalPoint.y}`} 
                      fill="none"
                      stroke="#0d529d"
                      strokeWidth="5"
                      strokeLinecap="round"
                    />
                    <path 
                      d={`M ${citizenPoint.x} ${citizenPoint.y} Q 350 250 ${hospitalPoint.x} ${hospitalPoint.y}`} 
                      fill="none"
                      stroke="#1a73e8"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeDasharray="6 4"
                      style={{ animation: "path-flow 3s linear infinite" }}
                    />
                  </g>
                )}

                {/* Shelter Markers as Google Maps Green Pins */}
                {shelters.map(shelter => {
                  const coord = MAP_COORDINATES[shelter.name];
                  if (!coord) return null;
                  const isSelected = recommendedShelter.includes(shelter.name);
                  const isFull = shelter.status === "FULL";
                  const pinColor = isSelected ? "#0f9d58" : (isFull ? "#d93025" : "#80868b");
                  
                  return (
                    <g key={shelter.id} transform={`translate(${coord.x}, ${coord.y})`} style={{ cursor: "pointer" }}>
                      {/* Marker shadow */}
                      <ellipse cx="0" cy="0" rx="8" ry="3" fill="rgba(0,0,0,0.4)" />
                      {/* Teardrop shape */}
                      <path 
                        d="M 0 0 C -8 -8 -13 -15 -13 -22 C -13 -30 -7 -36 0 -36 C 7 -36 13 -30 13 -22 C 13 -15 8 -8 0 0 Z" 
                        fill={pinColor} 
                        stroke="#ffffff" 
                        strokeWidth="1.5" 
                        style={{ filter: isSelected ? "drop-shadow(0 0 5px #0f9d58)" : "none" }}
                      />
                      {/* Inner circle */}
                      <circle cx="0" cy="-22" r="5" fill="#ffffff" />
                      {/* Label */}
                      <text x="0" y="16" textAnchor="middle" fill="#ffffff" fontSize="9" fontWeight="700" style={{ textShadow: "0 1px 3px rgba(0,0,0,0.8)" }}>
                        {shelter.name.replace(" Shelter", "").replace(" Relief Camp", "")}
                      </text>
                    </g>
                  );
                })}

                {/* Hospital Markers as Google Maps Blue Pins */}
                {hospitals.map(hosp => {
                  const coord = MAP_COORDINATES[hosp.name];
                  if (!coord) return null;
                  const isSelected = hospitalInfo.includes(hosp.name);
                  const isCritical = hosp.status === "CRITICAL_CAPACITY";
                  const pinColor = isSelected ? "#4285f4" : (isCritical ? "#d93025" : "#80868b");

                  return (
                    <g key={hosp.id} transform={`translate(${coord.x}, ${coord.y})`} style={{ cursor: "pointer" }}>
                      <ellipse cx="0" cy="0" rx="8" ry="3" fill="rgba(0,0,0,0.4)" />
                      <path 
                        d="M 0 0 C -8 -8 -13 -15 -13 -22 C -13 -30 -7 -36 0 -36 C 7 -36 13 -30 13 -22 C 13 -15 8 -8 0 0 Z" 
                        fill={pinColor} 
                        stroke="#ffffff" 
                        strokeWidth="1.5" 
                        style={{ filter: isSelected ? "drop-shadow(0 0 5px #4285f4)" : "none" }}
                      />
                      <circle cx="0" cy="-22" r="5" fill="#ffffff" />
                      <text x="0" y="16" textAnchor="middle" fill="#ffffff" fontSize="9" fontWeight="700" style={{ textShadow: "0 1px 3px rgba(0,0,0,0.8)" }}>
                        {hosp.name.replace(" General Hospital", "").replace(" Government Hospital", "").replace(" Emergency", "")}
                      </text>
                    </g>
                  );
                })}

                {/* Citizen Starting Marker (Google Maps Pulse Blue Dot) */}
                {locationConsent && citizenPoint && (
                  <g transform={`translate(${citizenPoint.x}, ${citizenPoint.y})`}>
                    {/* Pulsing radar circle */}
                    <circle cx="0" cy="0" r="18" fill="rgba(66, 133, 244, 0.25)" className="pulse-hazard-glow" />
                    {/* Outer glow ring */}
                    <circle cx="0" cy="0" r="8" fill="rgba(66, 133, 244, 0.4)" stroke="#ffffff" strokeWidth="1.5" />
                    {/* Inner core blue dot */}
                    <circle cx="0" cy="0" r="5" fill="#4285f4" />
                    <text x="0" y="-14" textAnchor="middle" fill="#4285f4" fontSize="9.5" fontWeight="800" style={{ textShadow: "0 1px 3px rgba(0,0,0,0.8)" }}>
                      MY LOCATION
                    </text>
                  </g>
                )}

                {/* Weather Tags next to Indian Regions (Google Maps Style) */}
                {/* Guwahati Weather */}
                <g transform="translate(605, 185)">
                  <rect x="0" y="0" width="135" height="20" rx="4" fill="#242f3e" stroke="rgba(255,255,255,0.18)" strokeWidth="1" />
                  <text x="6" y="14" fill="#fff" fontSize="8" fontWeight="800">Guwahati, AS: 🌧️ 28°C</text>
                </g>

                {/* Mumbai Weather */}
                <g transform="translate(110, 290)">
                  <rect x="0" y="0" width="135" height="20" rx="4" fill="#242f3e" stroke="rgba(255,255,255,0.18)" strokeWidth="1" />
                  <text x="6" y="14" fill="#fff" fontSize="8" fontWeight="800">Mumbai, MH: 🌧️ 26°C</text>
                </g>

                {/* Dehradun Weather */}
                <g transform="translate(425, 105)">
                  <rect x="0" y="0" width="145" height="20" rx="4" fill="#242f3e" stroke="rgba(255,255,255,0.18)" strokeWidth="1" />
                  <text x="6" y="14" fill="#fff" fontSize="8" fontWeight="800">Dehradun, UT: ⛈️ 19°C</text>
                </g>

                {/* Chennai Weather */}
                <g transform="translate(390, 445)">
                  <rect x="0" y="0" width="135" height="20" rx="4" fill="#242f3e" stroke="rgba(255,255,255,0.18)" strokeWidth="1" />
                  <text x="6" y="14" fill="#fff" fontSize="8" fontWeight="800">Chennai, TN: 🌀 25°C</text>
                </g>
              </svg>
            </div>
          </div>
        ) : (
          /* Admin Security & Auditing Panel */
          <div className="audit-logs-view">
            <div className="audit-header-row">
              <div>
                <h2>Security Compliance Registry</h2>
                <p className="text-secondary text-sm">Real-time threat and privacy audit trails logs</p>
              </div>
              <button onClick={handleClearLogs} className="audit-clear-btn">
                <Trash2 size={14} className="inline mr-2" />
                Clear Logs
              </button>
            </div>

            <table className="audit-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Session ID</th>
                  <th>Role</th>
                  <th>Event</th>
                  <th>Audit Parameters</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.length > 0 ? (
                  auditLogs.map((log, index) => (
                    <tr key={index}>
                      <td className="text-muted">{log.timestamp}</td>
                      <td>{log.session_id}</td>
                      <td>
                        <span className={`audit-role-badge role-${log.role.toLowerCase().replace(" ", "")}`}>
                          {log.role}
                        </span>
                      </td>
                      <td style={{ fontWeight: 700, color: log.event.includes("WARNING") ? "var(--accent-orange)" : "var(--text-primary)" }}>
                        {log.event}
                      </td>
                      <td>
                        <pre className="audit-details-json">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="text-center text-muted py-8">
                      No security audit logs recorded yet. Initiate chat to generate events.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Panel 3: Disaster Status & Supply Recommendations */}
        <div className="panel right">
          <div className="panel-header">
            <h2><Activity size={16} /> Dispatch Center</h2>
          </div>

          <div className="status-content">
            {/* Assessment Card */}
            <div className="status-section">
              <div className="status-title-row">
                <ShieldAlert size={14} className="text-accent-red" />
                Disaster Evaluation
              </div>
              {disasterType ? (
                <>
                  <div className="assess-badge-grid">
                    <div className="assess-badge">
                      <div className="assess-badge-label">Incident Type</div>
                      <div className="assess-badge-val text-accent-red">{disasterType}</div>
                    </div>
                    <div className="assess-badge">
                      <div className="assess-badge-label">Severity Level</div>
                      <div className="assess-badge-val text-accent-orange">{severity}</div>
                    </div>
                  </div>
                  <div className="assess-desc">
                    {assessmentSummary}
                  </div>
                </>
              ) : (
                <div className="text-muted text-sm py-4 text-center">
                  Waiting for emergency description to trigger assessment...
                </div>
              )}
            </div>

            {/* Shelters Database Status */}
            <div className="status-section">
              <div className="status-title-row">
                <Home size={14} className="text-accent-green" />
                Shelter Discovery
              </div>
              {recommendedShelter ? (
                <div>
                  <div className="db-item">
                    <div>
                      <div className="db-item-name">{recommendedShelter.split(" at ")[0]}</div>
                      <div className="db-item-sub">Evacuation shelter target</div>
                    </div>
                    <div className="db-item-metric text-accent-green">OPEN</div>
                  </div>
                  <div className="text-xs text-secondary mt-2">
                    {recommendedShelter}
                  </div>
                </div>
              ) : (
                <div className="text-muted text-sm py-4 text-center">
                  Search database via emergency chat...
                </div>
              )}
            </div>

            {/* Evacuation Route Status */}
            <div className="status-section">
              <div className="status-title-row">
                <MapPin size={14} className="text-accent-orange" />
                Safe Evacuation Path
              </div>
              {recommendedRoute ? (
                <div>
                  <div className="text-xs text-secondary mt-2">
                    {recommendedRoute}
                  </div>
                </div>
              ) : (
                <div className="text-muted text-sm py-4 text-center">
                  Path details compile with shelter discovery...
                </div>
              )}
            </div>

            {/* Medical Database Status */}
            <div className="status-section">
              <div className="status-title-row">
                <HeartPulse size={14} className="text-accent-blue" />
                Medical Dispatch
              </div>
              {hospitalInfo ? (
                <div>
                  <div className="text-xs text-secondary mt-2">
                    {hospitalInfo}
                  </div>
                </div>
              ) : (
                <div className="text-muted text-sm py-4 text-center">
                  No active medical facilities requested...
                </div>
              )}
            </div>

            {/* Supply recommendations */}
            <div className="status-section">
              <div className="status-title-row">
                <PackageCheck size={14} className="text-accent-yellow" />
                Emergency Supply Checklist
              </div>
              {supplyList.length > 0 ? (
                <div style={{ maxHeight: "150px", overflowY: "auto" }}>
                  {supplyList.map((item, idx) => (
                    <div key={idx} className="checklist-item">
                      <input type="checkbox" defaultChecked />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-muted text-sm py-4 text-center">
                  Awaiting disaster classification checklist...
                </div>
              )}
            </div>

            {/* Alerts prepared */}
            <div className="status-section">
              <div className="status-title-row">
                <MessageSquareShare size={14} />
                SMS Safety Broadcast
              </div>
              {draftedSms ? (
                <div className="text-xs bg-dark-eval p-3 rounded border border-glass border-left-3">
                  <p className="text-secondary italic">"{draftedSms.replace(/SMS\s*Ready\s*Alert:\s*/i, "")}"</p>
                </div>
              ) : (
                <div className="text-muted text-sm py-4 text-center">
                  Automatic broadcasts compile after assessment...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
