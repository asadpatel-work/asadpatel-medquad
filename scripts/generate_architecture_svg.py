"""
Generate MedQuAD Architecture Diagram in SVG and PNG formats for Google Drawings / Google Docs import.
Adheres to:
- Minimal detail in each component box (just Component Name & Service/Model)
- High detail on interconnecting protocol/payload arrows
- Google Workspace & Cloud color palette
"""

import os
import subprocess

SVG_CONTENT = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 640" width="100%" height="100%" style="background-color: #FFFFFF; font-family: 'Google Sans', Roboto, -apple-system, BlinkMacSystemFont, Arial, sans-serif;">
  <defs>
    <!-- Drop Shadow Filter -->
    <filter id="card-shadow" x="-4%" y="-4%" width="108%" height="110%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.06"/>
    </filter>
    <filter id="accent-shadow" x="-4%" y="-4%" width="108%" height="110%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#1A73E8" flood-opacity="0.12"/>
    </filter>

    <!-- Arrowhead Markers -->
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#1A73E8"/>
    </marker>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#34A853"/>
    </marker>
    <marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#EA4335"/>
    </marker>
    <marker id="arrow-muted" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#5F6368"/>
    </marker>
  </defs>

  <!-- ========================================== -->
  <!-- HEADER -->
  <!-- ========================================== -->
  <g id="header" transform="translate(40, 28)">
    <text x="0" y="0" font-size="11" font-weight="700" fill="#1A73E8" letter-spacing="1">SYSTEM ARCHITECTURE</text>
    <text x="0" y="24" font-size="18" font-weight="700" fill="#202124">MedQuAD Multi-Agent Clinical Research Platform</text>
    <text x="0" y="42" font-size="12" font-weight="400" fill="#5F6368">Decoupled Supervisor-Worker Pattern with Deterministic Grounding &amp; Dual-Layer Perimeter Defense</text>
    <line x1="0" y1="54" x2="1020" y2="54" stroke="#E0E3E7" stroke-width="1"/>
  </g>

  <!-- ========================================== -->
  <!-- TIER 1: INGRESS & PERIMETER DEFENSE -->
  <!-- ========================================== -->
  <g id="tier-1" transform="translate(40, 100)">
    <!-- Container -->
    <rect x="0" y="0" width="1020" height="110" rx="10" ry="10" fill="#F8F9FA" stroke="#E0E3E7" stroke-width="1"/>
    <text x="18" y="22" font-size="10" font-weight="700" fill="#5F6368" letter-spacing="0.5">TIER 1: INGRESS &amp; PERIMETER DEFENSE</text>

    <!-- 1. Clinician UI -->
    <g transform="translate(18, 36)" filter="url(#card-shadow)">
      <rect width="115" height="56" rx="8" ry="8" fill="#E8F0FE" stroke="#1A73E8" stroke-width="1.5"/>
      <text x="57" y="25" font-size="12" font-weight="700" fill="#1A73E8" text-anchor="middle">Clinician UI</text>
      <text x="57" y="42" font-size="10" font-weight="500" fill="#4285F4" text-anchor="middle">React 18 / REST API</text>
    </g>

    <!-- Arrow: UI -> Cloud Armor -->
    <line x1="133" y1="64" x2="183" y2="64" stroke="#1A73E8" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
    <rect x="135" y="42" width="46" height="14" rx="4" ry="4" fill="#FFFFFF" stroke="#E0E3E7" stroke-width="0.5"/>
    <text x="158" y="52" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">1. HTTPS</text>

    <!-- 2. Cloud Armor -->
    <g transform="translate(183, 36)" filter="url(#card-shadow)">
      <rect width="125" height="56" rx="8" ry="8" fill="#FFFFFF" stroke="#DADCE0" stroke-width="1"/>
      <text x="62" y="25" font-size="12" font-weight="700" fill="#202124" text-anchor="middle">Cloud Armor</text>
      <text x="62" y="42" font-size="10" font-weight="500" fill="#5F6368" text-anchor="middle">L7 WAF &amp; DDoS</text>
    </g>

    <!-- Arrow: Cloud Armor -> Cloud Run -->
    <line x1="308" y1="64" x2="358" y2="64" stroke="#1A73E8" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
    <rect x="310" y="42" width="46" height="14" rx="4" ry="4" fill="#FFFFFF" stroke="#E0E3E7" stroke-width="0.5"/>
    <text x="333" y="52" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">2. Clean</text>

    <!-- 3. Cloud Run Gateway -->
    <g transform="translate(358, 36)" filter="url(#card-shadow)">
      <rect width="140" height="56" rx="8" ry="8" fill="#FFFFFF" stroke="#DADCE0" stroke-width="1"/>
      <text x="70" y="25" font-size="12" font-weight="700" fill="#202124" text-anchor="middle">Cloud Run Gateway</text>
      <text x="70" y="42" font-size="10" font-weight="500" fill="#5F6368" text-anchor="middle">FastAPI Microservice</text>
    </g>

    <!-- Arrow: Cloud Run -> Model Armor -->
    <line x1="498" y1="64" x2="548" y2="64" stroke="#1A73E8" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
    <rect x="500" y="42" width="46" height="14" rx="4" ry="4" fill="#FFFFFF" stroke="#E0E3E7" stroke-width="0.5"/>
    <text x="523" y="52" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">3. Payload</text>

    <!-- 4. Model Armor -->
    <g transform="translate(548, 36)" filter="url(#card-shadow)">
      <rect width="135" height="56" rx="8" ry="8" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.5"/>
      <text x="67" y="25" font-size="12" font-weight="700" fill="#1A73E8" text-anchor="middle">Model Armor</text>
      <text x="67" y="42" font-size="10" font-weight="500" fill="#5F6368" text-anchor="middle">Layer 8 Guardrail &amp; SDP</text>
    </g>

    <!-- Arrow: Model Armor -> Safe Refusal Exit -->
    <line x1="683" y1="64" x2="748" y2="64" stroke="#EA4335" stroke-width="1.5" marker-end="url(#arrow-red)"/>
    <rect x="686" y="42" width="60" height="14" rx="4" ry="4" fill="#FFFFFF" stroke="#FCE8E6" stroke-width="0.5"/>
    <text x="716" y="52" font-size="7.5" font-weight="700" fill="#EA4335" text-anchor="middle">4a. Dosing / ER</text>

    <!-- 5. Safe Refusal Exit -->
    <g transform="translate(748, 36)" filter="url(#card-shadow)">
      <rect width="254" height="56" rx="8" ry="8" fill="#FEF2F2" stroke="#EA4335" stroke-width="1.5"/>
      <text x="127" y="25" font-size="12" font-weight="700" fill="#EA4335" text-anchor="middle">Safe Refusal Engine Exit</text>
      <text x="127" y="42" font-size="10" font-weight="500" fill="#C5221F" text-anchor="middle">Sub-5ms Refusal • Zero Model Tokens</text>
    </g>
  </g>

  <!-- ========================================== -->
  <!-- STEPPED CONNECTOR: Model Armor -> Root Orchestrator -->
  <!-- ========================================== -->
  <path d="M 615 192 L 615 220 L 140 220 L 140 250" fill="none" stroke="#34A853" stroke-width="1.5" marker-end="url(#arrow-green)"/>
  <rect x="250" y="211" width="260" height="18" rx="5" ry="5" fill="#FFFFFF" stroke="#CEEAD6" stroke-width="1"/>
  <text x="380" y="223" font-size="8.5" font-weight="700" fill="#188038" text-anchor="middle">4b. Sanitized Query (18 HIPAA PHI Identifiers Scrubbed)</text>

  <!-- ========================================== -->
  <!-- TIER 2: GOOGLE ADK MULTI-AGENT CORE -->
  <!-- ========================================== -->
  <g id="tier-2" transform="translate(40, 230)">
    <!-- Container -->
    <rect x="0" y="0" width="1020" height="150" rx="10" ry="10" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.5"/>
    <text x="18" y="22" font-size="10" font-weight="700" fill="#1A73E8" letter-spacing="0.5">TIER 2: GOOGLE ADK MULTI-AGENT CORE (DECOUPLED SUPERVISOR-WORKER PATTERN)</text>

    <!-- Agent 1: Root Orchestrator -->
    <g transform="translate(25, 45)" filter="url(#card-shadow)">
      <rect width="210" height="75" rx="8" ry="8" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.5"/>
      <rect width="210" height="32" rx="8" ry="8" fill="#E8F0FE"/>
      <rect y="24" width="210" height="8" fill="#E8F0FE"/>
      <text x="105" y="21" font-size="13" font-weight="700" fill="#1A73E8" text-anchor="middle">Root Orchestrator</text>
      <text x="105" y="55" font-size="11" font-weight="600" fill="#202124" text-anchor="middle">Gemini 2.5 Flash</text>
    </g>

    <!-- Arrow: Orchestrator -> Clinical Researcher -->
    <line x1="235" y1="82" x2="350" y2="82" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arrow-blue)"/>
    <rect x="240" y="55" width="105" height="20" rx="5" ry="5" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="292" y="68" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">5. Intent + Loop Ceiling</text>

    <!-- Agent 2: Clinical Researcher -->
    <g transform="translate(350, 45)" filter="url(#card-shadow)">
      <rect width="220" height="75" rx="8" ry="8" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.5"/>
      <rect width="220" height="32" rx="8" ry="8" fill="#E8F0FE"/>
      <rect y="24" width="220" height="8" fill="#E8F0FE"/>
      <text x="110" y="21" font-size="13" font-weight="700" fill="#1A73E8" text-anchor="middle">Clinical Researcher</text>
      <text x="110" y="55" font-size="11" font-weight="600" fill="#202124" text-anchor="middle">Gemini 2.5 Pro</text>
    </g>

    <!-- Arrow: Researcher -> Reviewer -->
    <line x1="570" y1="82" x2="700" y2="82" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arrow-blue)"/>
    <rect x="580" y="55" width="110" height="20" rx="5" ry="5" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="635" y="68" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">8. Draft + [1],[2] Anchors</text>

    <!-- Agent 3: Reviewer & QC Gate -->
    <g transform="translate(700, 45)" filter="url(#accent-shadow)">
      <rect width="295" height="75" rx="8" ry="8" fill="#FFFFFF" stroke="#34A853" stroke-width="1.8"/>
      <rect width="295" height="32" rx="8" ry="8" fill="#E6F4EA"/>
      <rect y="24" width="295" height="8" fill="#E6F4EA"/>
      <text x="147" y="21" font-size="13" font-weight="700" fill="#137333" text-anchor="middle">Reviewer &amp; QC Gate</text>
      <text x="147" y="55" font-size="11" font-weight="600" fill="#202124" text-anchor="middle">Gemini 3.5 Flash &amp; CitationVerifier</text>
    </g>
  </g>

  <!-- ========================================== -->
  <!-- VERTICAL CONNECTORS: Researcher <-> Data Layer -->
  <!-- ========================================== -->
  <!-- 6. Query (Down) -->
  <line x1="425" y1="380" x2="425" y2="435" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arrow-blue)"/>
  <rect x="330" y="398" width="88" height="18" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
  <text x="374" y="410" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">6. Hybrid Query</text>

  <!-- 7. Chunks (Up) -->
  <line x1="495" y1="435" x2="495" y2="380" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arrow-blue)"/>
  <rect x="502" y="398" width="94" height="18" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
  <text x="549" y="410" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">7. Top-K Chunks</text>

  <!-- Telemetry Sink (Down dashed) -->
  <line x1="847" y1="380" x2="847" y2="435" stroke="#5F6368" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#arrow-muted)"/>
  <rect x="855" y="398" width="115" height="18" rx="4" ry="4" fill="#FFFFFF" stroke="#E0E3E7" stroke-width="0.8"/>
  <text x="912" y="410" font-size="7.5" font-weight="700" fill="#5F6368" text-anchor="middle">OTel Spans &amp; Metrics</text>

  <!-- ========================================== -->
  <!-- TIER 3: GROUNDING DATA & OBSERVABILITY SINK -->
  <!-- ========================================== -->
  <g id="tier-3" transform="translate(40, 435)">
    <!-- Container -->
    <rect x="0" y="0" width="1020" height="135" rx="10" ry="10" fill="#F8F9FA" stroke="#E0E3E7" stroke-width="1"/>
    <text x="18" y="22" font-size="10" font-weight="700" fill="#5F6368" letter-spacing="0.5">TIER 3: GROUNDING DATA STORES &amp; OBSERVABILITY SINK</text>

    <!-- Store 1: Vertex AI Search -->
    <g transform="translate(18, 36)" filter="url(#card-shadow)">
      <rect width="235" height="80" rx="8" ry="8" fill="#FFFFFF" stroke="#DADCE0" stroke-width="1"/>
      <text x="117" y="32" font-size="13" font-weight="700" fill="#1A73E8" text-anchor="middle">Vertex AI Search</text>
      <text x="117" y="55" font-size="10.5" font-weight="600" fill="#202124" text-anchor="middle">NIH MedQuAD Datastore</text>
      <text x="117" y="72" font-size="9" fill="#5F6368" text-anchor="middle">16,400+ Records • 500-Token Chunks</text>
    </g>

    <!-- Store 2: Clinical DB Tool -->
    <g transform="translate(268, 36)" filter="url(#card-shadow)">
      <rect width="235" height="80" rx="8" ry="8" fill="#FFFFFF" stroke="#DADCE0" stroke-width="1"/>
      <text x="117" y="32" font-size="13" font-weight="700" fill="#1A73E8" text-anchor="middle">Clinical DB Tool</text>
      <text x="117" y="55" font-size="10.5" font-weight="600" fill="#202124" text-anchor="middle">Biomarker &amp; Lab Thresholds</text>
      <text x="117" y="72" font-size="9" fill="#5F6368" text-anchor="middle">Diagnostic Reference Ranges</text>
    </g>

    <!-- Store 3: In-Memory Vector Fallback -->
    <g transform="translate(518, 36)" filter="url(#card-shadow)">
      <rect width="235" height="80" rx="8" ry="8" fill="#FFFFFF" stroke="#DADCE0" stroke-width="1"/>
      <text x="117" y="32" font-size="13" font-weight="700" fill="#1A73E8" text-anchor="middle">Vector DB Fallback</text>
      <text x="117" y="55" font-size="10.5" font-weight="600" fill="#202124" text-anchor="middle">Circuit Breaker Store</text>
      <text x="117" y="72" font-size="9" fill="#5F6368" text-anchor="middle">Sub-50ms Local Failover</text>
    </g>

    <!-- Store 4: Observability Sink -->
    <g transform="translate(768, 36)" filter="url(#card-shadow)">
      <rect width="235" height="80" rx="8" ry="8" fill="#FFFFFF" stroke="#DADCE0" stroke-width="1"/>
      <text x="117" y="32" font-size="13" font-weight="700" fill="#1A73E8" text-anchor="middle">Cloud Trace &amp; BigQuery</text>
      <text x="117" y="55" font-size="10.5" font-weight="600" fill="#202124" text-anchor="middle">Telemetry &amp; Audit Sink</text>
      <text x="117" y="72" font-size="9" fill="#5F6368" text-anchor="middle">Distributed Spans &amp; Audit Logs</text>
    </g>
  </g>

  <!-- Footer -->
  <text x="40" y="618" font-size="9.5" fill="#70757A">MedQuAD Enterprise Architecture • Capstone 506616 • HIPAA Safe Harbor Compliant • Google Cloud Run &amp; Vertex AI</text>
</svg>
'''

def main():
    docs_dir = "/usr/local/google/home/asadpatel/Documents/capstone/docs"
    svg_path = os.path.join(docs_dir, "architecture_diagram.svg")
    png_path = os.path.join(docs_dir, "architecture_diagram.png")

    # Write SVG
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(SVG_CONTENT.strip())
    print(f"Generated SVG: {svg_path} ({len(SVG_CONTENT)} bytes)")

    # Render high-res PNG using headless Google Chrome
    html_wrapper = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    body {{ margin: 0; padding: 0; background: white; }}
    svg {{ display: block; width: 1100px; height: 640px; }}
  </style>
</head>
<body>
{SVG_CONTENT.strip()}
</body>
</html>"""

    html_path = "/tmp/architecture_diagram_render.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_wrapper)

    cmd = [
        "/usr/bin/google-chrome",
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1100,640",
        "--screenshot=" + png_path,
        html_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Generated High-Res PNG via Chrome: {png_path} ({os.path.getsize(png_path)} bytes)")
    except Exception as e:
        print(f"Could not render PNG via Chrome: {e}")

if __name__ == "__main__":
    main()
