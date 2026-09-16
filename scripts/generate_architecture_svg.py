"""
Generate MedQuAD Architecture Diagram with:
1. Different shapes for different object types:
   - Clients: Browser / Display card
   - Security / WAF: Shield shape
   - Safe Refusal: Octagonal stop/barrier gate
   - Auto-scaling Compute: Cascading 3-layer container stack (0 -> N)
   - AI Agents: Supervisor & Scaled-up Worker pool (1 -> M)
   - Data Stores: 3D Database Cylinders with custom iconography
2. Product Logos:
   - Gemini 4-point sparkle star
   - Cloud Run container logo
   - Cloud Armor shield logo
   - Model Armor guardrail logo
   - Vertex AI Search logo
   - Clinical DB / SQL table logo
   - Vector Circuit Breaker logo
   - BigQuery & Cloud Trace logos
3. Scaling Replicas:
   - Visual multi-copy stacks for Cloud Run (0 -> N) and Clinical Researcher workers (1 -> M)
   - Replicated search datastore for Vertex AI
"""

import os
import subprocess

SVG_CONTENT = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 700" width="100%" height="100%" style="background-color: #FFFFFF; font-family: 'Google Sans', Roboto, -apple-system, BlinkMacSystemFont, Arial, sans-serif;">
  <defs>
    <!-- Drop Shadows -->
    <filter id="shadow-card" x="-4%" y="-4%" width="108%" height="114%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.07"/>
    </filter>
    <filter id="shadow-shield" x="-6%" y="-4%" width="112%" height="114%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#1A73E8" flood-opacity="0.14"/>
    </filter>
    <filter id="shadow-alert" x="-6%" y="-4%" width="112%" height="114%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#EA4335" flood-opacity="0.16"/>
    </filter>

    <!-- Arrowhead Markers -->
    <marker id="arr-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#1A73E8"/>
    </marker>
    <marker id="arr-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#34A853"/>
    </marker>
    <marker id="arr-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#EA4335"/>
    </marker>
    <marker id="arr-muted" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#5F6368"/>
    </marker>

    <!-- Gemini Sparkle Gradient -->
    <linearGradient id="gemini-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1A73E8"/>
      <stop offset="50%" stop-color="#8AB4F8"/>
      <stop offset="100%" stop-color="#4285F4"/>
    </linearGradient>

    <!-- Data Store Cylinder Gradient -->
    <linearGradient id="cylinder-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#F8F9FA"/>
      <stop offset="50%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#E8EAED"/>
    </linearGradient>

    <!-- ==================== PRODUCT & SYSTEM LOGOS ==================== -->
    <!-- Gemini 4-Point Star Logo -->
    <g id="logo-gemini">
      <path d="M 12 1 Q 12 12 1 12 Q 12 12 12 23 Q 12 12 23 12 Q 12 12 12 1 Z" fill="url(#gemini-grad)"/>
    </g>

    <!-- Cloud Run Logo -->
    <g id="logo-cloud-run">
      <path d="M 4 14 L 10 4 L 14 4 L 8 14 Z" fill="#4285F4"/>
      <path d="M 9 14 L 15 4 L 19 4 L 13 14 Z" fill="#669DF6"/>
      <path d="M 14 14 L 20 4 L 24 4 L 18 14 Z" fill="#8AB4F8"/>
      <path d="M 6 17 L 22 17 L 20 20 L 8 20 Z" fill="#3367D6"/>
    </g>

    <!-- Cloud Armor Logo -->
    <g id="logo-cloud-armor">
      <path d="M 12 2 L 22 6 L 22 13 Q 22 20 12 24 Q 2 20 2 13 L 2 6 Z" fill="#1A73E8"/>
      <path d="M 12 4.5 L 20 8 L 20 12.5 Q 20 18.5 12 22 Q 4 18.5 4 12.5 L 4 8 Z" fill="#FFFFFF"/>
      <path d="M 12 6 L 18.5 9 L 18.5 12 Q 18.5 17 12 20 Q 5.5 17 5.5 12 L 5.5 9 Z" fill="#4285F4"/>
      <path d="M 9.5 12 L 11.5 14 L 15 10.5" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </g>

    <!-- Model Armor Logo -->
    <g id="logo-model-armor">
      <path d="M 12 2 L 22 6 L 22 13 Q 22 20 12 24 Q 2 20 2 13 L 2 6 Z" fill="#1A73E8"/>
      <path d="M 12 4.5 L 20 8 L 20 12.5 Q 20 18.5 12 22 Q 4 18.5 4 12.5 L 4 8 Z" fill="#FFFFFF"/>
      <!-- Inner Sparkle Lock -->
      <path d="M 12 7 Q 12 12 7 12 Q 12 12 12 17 Q 12 12 17 12 Q 12 12 12 7 Z" fill="#1A73E8"/>
    </g>

    <!-- Vertex AI Logo -->
    <g id="logo-vertex-ai">
      <polygon points="12,2 22,8 22,18 12,24 2,18 2,8" fill="none" stroke="#4285F4" stroke-width="2"/>
      <circle cx="12" cy="13" r="3.5" fill="#34A853"/>
      <line x1="12" y1="2" x2="12" y2="9.5" stroke="#4285F4" stroke-width="1.5"/>
      <line x1="22" y1="18" x2="15.5" y2="13" stroke="#4285F4" stroke-width="1.5"/>
      <line x1="2" y1="18" x2="8.5" y2="13" stroke="#4285F4" stroke-width="1.5"/>
    </g>

    <!-- Clinical DB / Table Logo -->
    <g id="logo-clinical-db">
      <rect x="3" y="3" width="18" height="18" rx="3" ry="3" fill="#E8F0FE" stroke="#1A73E8" stroke-width="1.5"/>
      <line x1="3" y1="9" x2="21" y2="9" stroke="#1A73E8" stroke-width="1.5"/>
      <line x1="9" y1="9" x2="9" y2="21" stroke="#1A73E8" stroke-width="1.2"/>
      <line x1="15" y1="9" x2="15" y2="21" stroke="#1A73E8" stroke-width="1.2"/>
      <circle cx="6" cy="6" r="1.5" fill="#EA4335"/>
      <circle cx="12" cy="6" r="1.5" fill="#1A73E8"/>
    </g>

    <!-- Vector DB / Lightning Fallback Logo -->
    <g id="logo-vector-fallback">
      <circle cx="12" cy="12" r="10" fill="#E8F0FE" stroke="#F9AB00" stroke-width="1.5"/>
      <polygon points="13,3 6,13 11,13 10,21 18,10 13,10" fill="#F9AB00"/>
    </g>

    <!-- BigQuery Logo -->
    <g id="logo-bigquery">
      <ellipse cx="12" cy="7" rx="9" ry="3.5" fill="#669DF6"/>
      <path d="M 3 7 L 3 17 A 9 3.5 0 0 0 21 17 L 21 7 Z" fill="#4285F4"/>
      <ellipse cx="12" cy="17" rx="9" ry="3.5" fill="#3367D6"/>
      <circle cx="16" cy="15" r="4" fill="#FFFFFF"/>
      <circle cx="16" cy="15" r="2.5" fill="#EA4335"/>
      <line x1="19" y1="18" x2="22" y2="21" stroke="#3367D6" stroke-width="2" stroke-linecap="round"/>
    </g>

    <!-- Cloud Trace Logo -->
    <g id="logo-cloud-trace">
      <circle cx="5" cy="12" r="3" fill="#34A853"/>
      <circle cx="14" cy="6" r="3" fill="#4285F4"/>
      <circle cx="14" cy="18" r="3" fill="#FBBC04"/>
      <circle cx="21" cy="12" r="3" fill="#EA4335"/>
      <line x1="5" y1="12" x2="14" y2="6" stroke="#BDC1C6" stroke-width="1.5"/>
      <line x1="5" y1="12" x2="14" y2="18" stroke="#BDC1C6" stroke-width="1.5"/>
      <line x1="14" y1="6" x2="21" y2="12" stroke="#BDC1C6" stroke-width="1.5"/>
      <line x1="14" y1="18" x2="21" y2="12" stroke="#BDC1C6" stroke-width="1.5"/>
    </g>

    <!-- React / UI Logo -->
    <g id="logo-react">
      <ellipse cx="12" cy="12" rx="10" ry="4" fill="none" stroke="#00D8FF" stroke-width="1.2" transform="rotate(30 12 12)"/>
      <ellipse cx="12" cy="12" rx="10" ry="4" fill="none" stroke="#00D8FF" stroke-width="1.2" transform="rotate(90 12 12)"/>
      <ellipse cx="12" cy="12" rx="10" ry="4" fill="none" stroke="#00D8FF" stroke-width="1.2" transform="rotate(150 12 12)"/>
      <circle cx="12" cy="12" r="2" fill="#00D8FF"/>
    </g>

    <!-- Safe Refusal Barrier Logo -->
    <g id="logo-refusal">
      <polygon points="7,2 17,2 22,7 22,17 17,22 7,22 2,17 2,7" fill="#EA4335"/>
      <line x1="7" y1="12" x2="17" y2="12" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
    </g>
  </defs>

  <!-- ========================================== -->
  <!-- HEADER -->
  <!-- ========================================== -->
  <g id="header" transform="translate(40, 24)">
    <text x="0" y="0" font-size="11" font-weight="700" fill="#1A73E8" letter-spacing="1">SYSTEM ARCHITECTURE</text>
    <text x="0" y="24" font-size="19" font-weight="700" fill="#202124">MedQuAD Multi-Agent Clinical Research Platform</text>
    <text x="0" y="42" font-size="12" font-weight="400" fill="#5F6368">Decoupled Supervisor-Worker Pattern • Autoscaling Ingress &amp; Worker Pool • Layer 7 &amp; Layer 8 Defense</text>
    <line x1="0" y1="52" x2="1080" y2="52" stroke="#E0E3E7" stroke-width="1"/>
  </g>

  <!-- ========================================== -->
  <!-- TIER 1: INGRESS & PERIMETER DEFENSE -->
  <!-- ========================================== -->
  <g id="tier-1" transform="translate(40, 95)">
    <!-- Container -->
    <rect x="0" y="0" width="1080" height="135" rx="10" ry="10" fill="#F8F9FA" stroke="#E0E3E7" stroke-width="1"/>
    <text x="18" y="20" font-size="9.5" font-weight="700" fill="#5F6368" letter-spacing="0.5">TIER 1: INGRESS &amp; PERIMETER DEFENSE</text>

    <!-- 1. Clinician UI (Browser Window Shape) -->
    <g transform="translate(18, 36)" filter="url(#shadow-card)">
      <rect width="115" height="78" rx="8" ry="8" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.5"/>
      <!-- Window Titlebar -->
      <path d="M 0 8 Q 0 0 8 0 L 107 0 Q 115 0 115 8 L 115 18 L 0 18 Z" fill="#E8F0FE"/>
      <circle cx="10" cy="9" r="2.5" fill="#EA4335"/>
      <circle cx="18" cy="9" r="2.5" fill="#FBBC04"/>
      <circle cx="26" cy="9" r="2.5" fill="#34A853"/>
      <!-- Icon & Text -->
      <g transform="translate(46, 23)"><use href="#logo-react"/></g>
      <text x="57" y="56" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Clinician UI</text>
      <text x="57" y="70" font-size="9" font-weight="500" fill="#5F6368" text-anchor="middle">React 18 / REST API</text>
    </g>

    <!-- Arrow 1: UI -> Cloud Armor -->
    <line x1="133" y1="75" x2="183" y2="75" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arr-blue)"/>
    <rect x="135" y="53" width="46" height="15" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="158" y="64" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">1. HTTPS</text>

    <!-- 2. Cloud Armor (Shield Shape) -->
    <g transform="translate(183, 30)" filter="url(#shadow-shield)">
      <path d="M 12 0 L 113 0 L 125 15 L 125 58 Q 125 86 62 92 Q 0 86 0 58 L 0 15 Z" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.8"/>
      <path d="M 12 0 L 113 0 L 125 15 L 125 26 L 0 26 L 0 15 Z" fill="#E8F0FE"/>
      <g transform="translate(51, 32)"><use href="#logo-cloud-armor"/></g>
      <text x="62" y="68" font-size="11.5" font-weight="700" fill="#202124" text-anchor="middle">Cloud Armor</text>
      <text x="62" y="81" font-size="9" font-weight="600" fill="#1A73E8" text-anchor="middle">L7 WAF &amp; DDoS</text>
    </g>

    <!-- Arrow 2: Cloud Armor -> Cloud Run -->
    <line x1="308" y1="75" x2="355" y2="75" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arr-blue)"/>
    <rect x="309" y="53" width="44" height="15" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="331" y="64" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">2. Clean</text>

    <!-- 3. Cloud Run Gateway (Autoscaling Stack: 0 -> N Instances) -->
    <g transform="translate(355, 30)" filter="url(#shadow-card)">
      <!-- Card Replica 3 (Back) -->
      <rect x="12" y="4" width="138" height="78" rx="8" ry="8" fill="#E8EAED" stroke="#BDC1C6" stroke-width="1"/>
      <rect x="110" y="7" width="36" height="12" rx="3" ry="3" fill="#BDC1C6"/>
      <text x="128" y="16" font-size="6.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">Inst N</text>
      <!-- Card Replica 2 (Middle) -->
      <rect x="6" y="8" width="138" height="78" rx="8" ry="8" fill="#F1F3F4" stroke="#DADCE0" stroke-width="1"/>
      <rect x="104" y="11" width="36" height="12" rx="3" ry="3" fill="#DADCE0"/>
      <text x="122" y="20" font-size="6.5" font-weight="700" fill="#5F6368" text-anchor="middle">Inst 2</text>
      <!-- Card Replica 1 (Front) -->
      <rect x="0" y="12" width="138" height="78" rx="8" ry="8" fill="#FFFFFF" stroke="#4285F4" stroke-width="1.8"/>
      <rect x="0" y="12" width="138" height="22" rx="8" ry="8" fill="#E8F0FE"/>
      <rect x="0" y="26" width="138" height="8" fill="#E8F0FE"/>
      <!-- Scaling Badge -->
      <rect x="70" y="15" width="62" height="14" rx="3" ry="3" fill="#4285F4"/>
      <text x="101" y="25" font-size="6.8" font-weight="700" fill="#FFFFFF" text-anchor="middle">0 → N Replicas</text>
      <!-- Icon & Text -->
      <g transform="translate(8, 42)"><use href="#logo-cloud-run"/></g>
      <text x="82" y="52" font-size="11.5" font-weight="700" fill="#202124" text-anchor="middle">Cloud Run</text>
      <text x="82" y="66" font-size="9" font-weight="600" fill="#4285F4" text-anchor="middle">FastAPI Gateway</text>
      <text x="82" y="79" font-size="7.5" fill="#5F6368" text-anchor="middle">Serverless Microservice</text>
    </g>

    <!-- Arrow 3: Cloud Run -> Model Armor -->
    <line x1="505" y1="75" x2="555" y2="75" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arr-blue)"/>
    <rect x="506" y="53" width="46" height="15" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="529" y="64" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">3. Payload</text>

    <!-- 4. Model Armor (Shield Shape) -->
    <g transform="translate(555, 30)" filter="url(#shadow-shield)">
      <path d="M 12 0 L 118 0 L 130 15 L 130 58 Q 130 86 65 92 Q 0 86 0 58 L 0 15 Z" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.8"/>
      <path d="M 12 0 L 118 0 L 130 15 L 130 26 L 0 26 L 0 15 Z" fill="#E8F0FE"/>
      <g transform="translate(53, 32)"><use href="#logo-model-armor"/></g>
      <text x="65" y="68" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Model Armor</text>
      <text x="65" y="81" font-size="8.5" font-weight="600" fill="#5F6368" text-anchor="middle">Layer 8 Guardrail</text>
    </g>

    <!-- Arrow 4a: Model Armor -> Safe Refusal Exit -->
    <line x1="685" y1="75" x2="745" y2="75" stroke="#EA4335" stroke-width="1.8" marker-end="url(#arr-red)"/>
    <rect x="688" y="53" width="54" height="15" rx="4" ry="4" fill="#FFFFFF" stroke="#EA4335" stroke-width="0.8"/>
    <text x="715" y="64" font-size="7.5" font-weight="700" fill="#EA4335" text-anchor="middle">4a. Refusal</text>

    <!-- 5. Safe Refusal Engine Exit (Octagonal Stop Barrier) -->
    <g transform="translate(745, 30)" filter="url(#shadow-alert)">
      <polygon points="25,0 285,0 310,25 310,67 285,92 25,92 0,67 0,25" fill="#FEF2F2" stroke="#EA4335" stroke-width="2"/>
      <g transform="translate(20, 34)"><use href="#logo-refusal"/></g>
      <text x="172" y="42" font-size="12" font-weight="700" fill="#EA4335" text-anchor="middle">Safe Refusal Engine Exit</text>
      <text x="172" y="58" font-size="9.5" font-weight="600" fill="#C5221F" text-anchor="middle">Dosing / Personal Medical Advice Block</text>
      <text x="172" y="73" font-size="8" fill="#5F6368" text-anchor="middle">Sub-5ms Intercept • Zero Model Tokens Billed</text>
    </g>
  </g>

  <!-- ========================================== -->
  <!-- STEPPED CONNECTOR: Model Armor -> Root Orchestrator -->
  <!-- ========================================== -->
  <path d="M 620 220 L 620 248 L 145 248 L 145 280" fill="none" stroke="#34A853" stroke-width="2" marker-end="url(#arr-green)"/>
  <rect x="250" y="238" width="270" height="20" rx="5" ry="5" fill="#FFFFFF" stroke="#CEEAD6" stroke-width="1.2"/>
  <text x="385" y="252" font-size="8.5" font-weight="700" fill="#188038" text-anchor="middle">4b. Sanitized Query (18 HIPAA PHI Identifiers Scrubbed)</text>

  <!-- ========================================== -->
  <!-- TIER 2: GOOGLE ADK MULTI-AGENT CORE -->
  <!-- ========================================== -->
  <g id="tier-2" transform="translate(40, 265)">
    <!-- Container -->
    <rect x="0" y="0" width="1080" height="175" rx="10" ry="10" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.5"/>
    <text x="18" y="20" font-size="9.5" font-weight="700" fill="#1A73E8" letter-spacing="0.5">TIER 2: GOOGLE ADK MULTI-AGENT CORE (DECOUPLED SUPERVISOR-WORKER PATTERN)</text>

    <!-- Agent 1: Root Orchestrator (Supervisor) -->
    <g transform="translate(20, 42)" filter="url(#shadow-card)">
      <rect width="210" height="108" rx="10" ry="10" fill="#FFFFFF" stroke="#1A73E8" stroke-width="2"/>
      <rect width="210" height="32" rx="10" ry="10" fill="#E8F0FE"/>
      <rect y="22" width="210" height="10" fill="#E8F0FE"/>
      <!-- Logo & Header -->
      <g transform="translate(10, 5)"><use href="#logo-gemini"/></g>
      <text x="115" y="21" font-size="12" font-weight="700" fill="#1A73E8" text-anchor="middle">Root Orchestrator</text>
      <!-- Subtitle badge -->
      <rect x="45" y="40" width="120" height="18" rx="4" ry="4" fill="#F1F3F4"/>
      <text x="105" y="52" font-size="9" font-weight="700" fill="#202124" text-anchor="middle">Gemini 2.5 Flash</text>
      <text x="105" y="75" font-size="8.5" font-weight="600" fill="#1A73E8" text-anchor="middle">Supervisor Agent</text>
      <text x="105" y="91" font-size="8" fill="#5F6368" text-anchor="middle">max_iterations=2 Safety Ceiling</text>
    </g>

    <!-- Arrow 5: Orchestrator -> Clinical Researcher -->
    <line x1="230" y1="96" x2="340" y2="96" stroke="#1A73E8" stroke-width="2" marker-end="url(#arr-blue)"/>
    <rect x="238" y="74" width="94" height="17" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="285" y="86" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">5. Research Intent</text>

    <!-- Agent 2: Clinical Researcher (Scaling Worker Pool: 1 -> M concurrent) -->
    <g transform="translate(340, 32)" filter="url(#shadow-card)">
      <!-- Worker Replica 3 (Back) -->
      <rect x="14" y="2" width="230" height="108" rx="10" ry="10" fill="#E8EAED" stroke="#BDC1C6" stroke-width="1"/>
      <rect x="160" y="5" width="76" height="14" rx="3" ry="3" fill="#BDC1C6"/>
      <text x="198" y="15" font-size="7" font-weight="700" fill="#FFFFFF" text-anchor="middle">Worker M</text>
      <!-- Worker Replica 2 (Middle) -->
      <rect x="7" y="6" width="230" height="108" rx="10" ry="10" fill="#F1F3F4" stroke="#DADCE0" stroke-width="1"/>
      <rect x="153" y="9" width="76" height="14" rx="3" ry="3" fill="#DADCE0"/>
      <text x="191" y="19" font-size="7" font-weight="700" fill="#5F6368" text-anchor="middle">Worker 2</text>
      <!-- Worker Replica 1 (Front) -->
      <rect x="0" y="10" width="230" height="108" rx="10" ry="10" fill="#FFFFFF" stroke="#1A73E8" stroke-width="2"/>
      <rect x="0" y="10" width="230" height="32" rx="10" ry="10" fill="#E8F0FE"/>
      <rect x="0" y="32" width="230" height="10" fill="#E8F0FE"/>
      <!-- Scaling Pool Badge -->
      <rect x="146" y="15" width="76" height="14" rx="3" ry="3" fill="#1A73E8"/>
      <text x="184" y="25" font-size="6.8" font-weight="700" fill="#FFFFFF" text-anchor="middle">1 → M Workers</text>
      <!-- Logo & Header -->
      <g transform="translate(10, 15)"><use href="#logo-gemini"/></g>
      <text x="82" y="31" font-size="12" font-weight="700" fill="#1A73E8" text-anchor="middle">Clinical Researcher</text>
      <!-- Subtitle badge -->
      <rect x="55" y="48" width="120" height="18" rx="4" ry="4" fill="#F1F3F4"/>
      <text x="115" y="60" font-size="9" font-weight="700" fill="#202124" text-anchor="middle">Gemini 2.5 Pro</text>
      <text x="115" y="83" font-size="8.5" font-weight="600" fill="#1A73E8" text-anchor="middle">Horizontal Worker Pool</text>
      <text x="115" y="99" font-size="8" fill="#5F6368" text-anchor="middle">Multi-source Evidence Synthesis</text>
    </g>

    <!-- Arrow 8: Researcher -> Reviewer -->
    <line x1="584" y1="96" x2="695" y2="96" stroke="#1A73E8" stroke-width="2" marker-end="url(#arr-blue)"/>
    <rect x="592" y="74" width="94" height="17" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="639" y="86" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">8. Draft + [1],[2]</text>

    <!-- Agent 3: Reviewer & QC Gate (Auditor Shield Shape) -->
    <g transform="translate(695, 42)" filter="url(#shadow-shield)">
      <rect width="360" height="108" rx="10" ry="10" fill="#FFFFFF" stroke="#34A853" stroke-width="2"/>
      <rect width="360" height="32" rx="10" ry="10" fill="#E6F4EA"/>
      <rect y="22" width="360" height="10" fill="#E6F4EA"/>
      <!-- Logo & Header -->
      <g transform="translate(12, 5)"><use href="#logo-gemini"/></g>
      <text x="185" y="21" font-size="12.5" font-weight="700" fill="#137333" text-anchor="middle">Reviewer &amp; QC Gate</text>
      <!-- Subtitle badge -->
      <rect x="85" y="40" width="190" height="18" rx="4" ry="4" fill="#F1F3F4"/>
      <text x="180" y="52" font-size="9" font-weight="700" fill="#202124" text-anchor="middle">Gemini 3.5 Flash &amp; CitationVerifier</text>
      <text x="180" y="75" font-size="8.5" font-weight="600" fill="#137333" text-anchor="middle">Independent Zero-Bias Auditor</text>
      <text x="180" y="91" font-size="8" fill="#5F6368" text-anchor="middle">Deterministic 1:1 Grounding Match Verification</text>
    </g>
  </g>

  <!-- ========================================== -->
  <!-- VERTICAL CONNECTORS: Researcher <-> Data Layer -->
  <!-- ========================================== -->
  <!-- 6. Query (Down) -->
  <line x1="435" y1="440" x2="435" y2="505" stroke="#1A73E8" stroke-width="2" marker-end="url(#arr-blue)"/>
  <rect x="340" y="462" width="88" height="17" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
  <text x="384" y="474" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">6. Hybrid Query</text>

  <!-- 7. Chunks (Up) -->
  <line x1="510" y1="505" x2="510" y2="440" stroke="#1A73E8" stroke-width="2" marker-end="url(#arr-blue)"/>
  <rect x="518" y="462" width="92" height="17" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
  <text x="564" y="474" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">7. Top-K Chunks</text>

  <!-- Telemetry Sink (Down dashed) -->
  <line x1="875" y1="440" x2="875" y2="505" stroke="#5F6368" stroke-width="1.8" stroke-dasharray="4 3" marker-end="url(#arr-muted)"/>
  <rect x="882" y="462" width="112" height="17" rx="4" ry="4" fill="#FFFFFF" stroke="#DADCE0" stroke-width="0.8"/>
  <text x="938" y="474" font-size="7.5" font-weight="700" fill="#5F6368" text-anchor="middle">OTel Spans &amp; Metrics</text>

  <!-- ========================================== -->
  <!-- TIER 3: GROUNDING DATA & OBSERVABILITY SINK -->
  <!-- ========================================== -->
  <g id="tier-3" transform="translate(40, 505)">
    <!-- Container -->
    <rect x="0" y="0" width="1080" height="145" rx="10" ry="10" fill="#F8F9FA" stroke="#E0E3E7" stroke-width="1"/>
    <text x="18" y="20" font-size="9.5" font-weight="700" fill="#5F6368" letter-spacing="0.5">TIER 3: GROUNDING DATA STORES &amp; OBSERVABILITY SINK (3D DATABASE CYLINDERS)</text>

    <!-- Store 1: Vertex AI Search (Cylinder Shape + Sharded Replica Stack) -->
    <g transform="translate(18, 30)" filter="url(#shadow-card)">
      <!-- Replica Back Cylinder -->
      <ellipse cx="127" cy="12" rx="110" ry="10" fill="#E8EAED" stroke="#BDC1C6" stroke-width="1"/>
      <path d="M 17 12 L 17 92 A 110 10 0 0 0 237 92 L 237 12 Z" fill="#E8EAED" stroke="#BDC1C6" stroke-width="1"/>
      <ellipse cx="127" cy="92" rx="110" ry="10" fill="#DADCE0" stroke="#BDC1C6" stroke-width="1"/>
      <!-- Front Main Cylinder -->
      <ellipse cx="120" cy="16" rx="110" ry="10" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <path d="M 10 16 L 10 96 A 110 10 0 0 0 230 96 L 230 16 Z" fill="url(#cylinder-grad)" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="96" rx="110" ry="10" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="56" rx="110" ry="10" fill="none" stroke="#DADCE0" stroke-width="1" stroke-dasharray="3 3"/>
      <!-- Logo & Text -->
      <g transform="translate(20, 36)"><use href="#logo-vertex-ai"/></g>
      <text x="135" y="46" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Vertex AI Search</text>
      <text x="135" y="60" font-size="9" font-weight="600" fill="#202124" text-anchor="middle">NIH MedQuAD Datastore</text>
      <text x="135" y="73" font-size="8" fill="#5F6368" text-anchor="middle">16,400+ Records • Scaled Serving</text>
    </g>

    <!-- Store 2: Clinical DB Tool (Cylinder Shape + Logo) -->
    <g transform="translate(283, 30)" filter="url(#shadow-card)">
      <ellipse cx="120" cy="16" rx="110" ry="10" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <path d="M 10 16 L 10 96 A 110 10 0 0 0 230 96 L 230 16 Z" fill="url(#cylinder-grad)" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="96" rx="110" ry="10" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="56" rx="110" ry="10" fill="none" stroke="#DADCE0" stroke-width="1" stroke-dasharray="3 3"/>
      <!-- Logo & Text -->
      <g transform="translate(20, 36)"><use href="#logo-clinical-db"/></g>
      <text x="135" y="46" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Clinical DB Tool</text>
      <text x="135" y="60" font-size="9" font-weight="600" fill="#202124" text-anchor="middle">Biomarker &amp; Lab Thresholds</text>
      <text x="135" y="73" font-size="8" fill="#5F6368" text-anchor="middle">Diagnostic Reference Ranges</text>
    </g>

    <!-- Store 3: Vector DB Fallback (Cylinder Shape + Circuit Breaker Logo) -->
    <g transform="translate(548, 30)" filter="url(#shadow-card)">
      <ellipse cx="120" cy="16" rx="110" ry="10" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <path d="M 10 16 L 10 96 A 110 10 0 0 0 230 96 L 230 16 Z" fill="url(#cylinder-grad)" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="96" rx="110" ry="10" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="56" rx="110" ry="10" fill="none" stroke="#DADCE0" stroke-width="1" stroke-dasharray="3 3"/>
      <!-- Logo & Text -->
      <g transform="translate(20, 36)"><use href="#logo-vector-fallback"/></g>
      <text x="135" y="46" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Vector DB Fallback</text>
      <text x="135" y="60" font-size="9" font-weight="600" fill="#202124" text-anchor="middle">Circuit Breaker Store</text>
      <text x="135" y="73" font-size="8" fill="#5F6368" text-anchor="middle">Sub-50ms In-Memory Failover</text>
    </g>

    <!-- Store 4: Observability Sink (BigQuery & Cloud Trace) -->
    <g transform="translate(813, 30)" filter="url(#shadow-card)">
      <ellipse cx="120" cy="16" rx="110" ry="10" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <path d="M 10 16 L 10 96 A 110 10 0 0 0 230 96 L 230 16 Z" fill="url(#cylinder-grad)" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="96" rx="110" ry="10" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="56" rx="110" ry="10" fill="none" stroke="#DADCE0" stroke-width="1" stroke-dasharray="3 3"/>
      <!-- Logos & Text -->
      <g transform="translate(18, 36)"><use href="#logo-bigquery"/></g>
      <g transform="translate(200, 36)"><use href="#logo-cloud-trace"/></g>
      <text x="120" y="46" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Cloud Trace &amp; BigQuery</text>
      <text x="120" y="60" font-size="9" font-weight="600" fill="#202124" text-anchor="middle">Telemetry &amp; Audit Sink</text>
      <text x="120" y="73" font-size="8" fill="#5F6368" text-anchor="middle">Distributed Spans &amp; Eval Logs</text>
    </g>
  </g>

  <!-- Footer -->
  <text x="40" y="680" font-size="9.5" fill="#70757A">MedQuAD Enterprise Architecture • Capstone 506616 • HIPAA Safe Harbor Compliant • Google Cloud Run &amp; Vertex AI</text>
</svg>
'''

def main():
    docs_dir = "/usr/local/google/home/asadpatel/Documents/capstone/docs"
    svg_path = os.path.join(docs_dir, "architecture_diagram.svg")
    png_path = os.path.join(docs_dir, "architecture_diagram.png")
    emf_path = os.path.join(docs_dir, "architecture_diagram.emf")
    wmf_path = os.path.join(docs_dir, "architecture_diagram.wmf")

    # 1. Write SVG
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(SVG_CONTENT.strip())
    print(f"Generated SVG: {svg_path} ({len(SVG_CONTENT)} bytes)")

    # 2. Render high-res PNG via headless Google Chrome
    html_wrapper = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    body {{ margin: 0; padding: 0; background: white; }}
    svg {{ display: block; width: 1160px; height: 700px; }}
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
        "--window-size=1160,700",
        "--screenshot=" + png_path,
        html_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Generated High-Res PNG: {png_path} ({os.path.getsize(png_path)} bytes)")
    except Exception as e:
        print(f"Could not render PNG: {e}")

    # 3. Convert to EMF and WMF via Inkscape in scratch
    inkscape_bin = "/usr/local/google/home/asadpatel/.gemini/antigravity-cli/brain/a8a05029-8ad8-4584-b430-e97dbcd69b22/scratch/inkscape/squashfs-root/AppRun"
    if os.path.exists(inkscape_bin):
        # Convert to EMF
        subprocess.run([inkscape_bin, svg_path, f"--export-filename={emf_path}"], capture_output=True)
        print(f"Generated EMF: {emf_path} ({os.path.getsize(emf_path)} bytes)")
        # Convert to WMF
        subprocess.run([inkscape_bin, svg_path, f"--export-filename={wmf_path}"], capture_output=True)
        print(f"Generated WMF: {wmf_path} ({os.path.getsize(wmf_path)} bytes)")
    else:
        print(f"Inkscape binary not found at {inkscape_bin}")

if __name__ == "__main__":
    main()
