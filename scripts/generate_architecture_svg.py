"""
Generate MedQuAD Architecture Diagram with:
1. True Architectural Boundaries:
   - Tier 1: Ingress & Perimeter Defense (UI -> Cloud Armor L7 WAF -> Model Armor Layer 8 Guardrail -> Safe Refusal)
   - Tier 2: Google Cloud Run Serverless Container Workload (0 -> N Replicas)
     ENCLOSES: FastAPI Gateway, Root Orchestrator (Supervisor), Clinical Researcher (Worker Pool), Reviewer & QC Gate (Auditor).
     Clearly illustrates that Researcher is a Python Agent running in Cloud Run calling Gemini 2.5 Pro on Vertex AI.
   - Tier 3: Grounding Data Stores & Observability Sink (3D Database Cylinders)
2. ACTUAL OFFICIAL Google Product Logos:
   - Official Google Cloud Run logo
   - Official Google Cloud Armor logo
   - Official Google Cloud Model Armor logo
   - Official Google Gemini logo with authentic gradient
   - Official Google Cloud Vertex AI logo
   - Official Google Cloud BigQuery logo
   - Official Google Cloud Trace logo
   - Official React logo
3. Scaling Replicas:
   - Cloud Run Container Replicas (0 -> N)
   - Clinical Researcher Worker Coroutines (1 -> M)
   - Vertex AI Search sharded replicas
"""

import os
import subprocess

SVG_CONTENT = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 720" width="100%" height="100%" style="background-color: #FFFFFF; font-family: 'Google Sans', Roboto, -apple-system, BlinkMacSystemFont, Arial, sans-serif;">
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
    <filter id="shadow-cloudrun" x="-2%" y="-2%" width="104%" height="106%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#4285F4" flood-opacity="0.15"/>
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

    <!-- Official Google Gemini Multi-Color Gradient -->
    <linearGradient id="gemini-official-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1BA1E3"/>
      <stop offset="32%" stop-color="#5468FF"/>
      <stop offset="68%" stop-color="#9855FF"/>
      <stop offset="100%" stop-color="#D552FF"/>
    </linearGradient>

    <!-- Data Store Cylinder Gradient -->
    <linearGradient id="cylinder-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#F8F9FA"/>
      <stop offset="50%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#E8EAED"/>
    </linearGradient>

    <!-- ==================== OFFICIAL GOOGLE LOGOS ==================== -->
    <!-- 1. Official Google Gemini Star -->
    <g id="logo-gemini">
      <path fill="url(#gemini-official-grad)" d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81"/>
    </g>

    <!-- 2. Official Google Cloud Run Logo -->
    <g id="logo-cloud-run">
      <polygon fill="#aecbfa" points="8.9 2.63 12.02 12 21.38 12 8.9 2.63"/>
      <polygon fill="#4285f4" points="21.38 12 12.02 12 8.9 21.38 21.38 12"/>
      <polygon fill="#4285f4" points="3.44 21.38 6.57 19.81 8.9 12 5.78 12 3.44 21.38"/>
      <polygon fill="#aecbfa" points="3.44 2.63 5.78 12 8.9 12 6.57 4.19 3.44 2.63"/>
    </g>

    <!-- 3. Official Google Cloud Armor Logo -->
    <g id="logo-cloud-armor">
      <polygon fill="#aecbfa" points="9.76 20.6 8.72 19.55 14.17 14.07 15.21 15.12 9.76 20.6"/>
      <polygon fill="#aecbfa" points="7.03 18.32 5.99 17.27 13.34 9.88 14.38 10.93 7.03 18.32"/>
      <polygon fill="#aecbfa" points="5.34 14.98 4.3 13.93 9.18 9.03 10.22 10.08 5.34 14.98"/>
      <path fill="#669df6" d="M12,3.61l6.78,3v4.55A9.71,9.71,0,0,1,12,20.48a9.7,9.7,0,0,1-6.78-9.31V6.63l6.78-3M12,2,3.75,5.68v5.49A11.17,11.17,0,0,0,11.85,22L12,22l.15,0a11.17,11.17,0,0,0,8.1-10.78V5.68L12,2Z"/>
      <circle fill="#669df6" cx="14.69" cy="14.62" r="1.42"/>
      <circle fill="#669df6" cx="13.85" cy="10.45" r="1.42"/>
      <circle fill="#669df6" cx="9.69" cy="9.6" r="1.42"/>
    </g>

    <!-- 4. Official Google Cloud Model Armor -->
    <g id="logo-model-armor">
      <polygon fill="#aecbfa" points="9.76 20.6 8.72 19.55 14.17 14.07 15.21 15.12 9.76 20.6"/>
      <polygon fill="#aecbfa" points="7.03 18.32 5.99 17.27 13.34 9.88 14.38 10.93 7.03 18.32"/>
      <path fill="#669df6" d="M12,3.61l6.78,3v4.55A9.71,9.71,0,0,1,12,20.48a9.7,9.7,0,0,1-6.78-9.31V6.63l6.78-3M12,2,3.75,5.68v5.49A11.17,11.17,0,0,0,11.85,22L12,22l.15,0a11.17,11.17,0,0,0,8.1-10.78V5.68L12,2Z"/>
      <g transform="translate(6, 6) scale(0.5)">
        <path fill="url(#gemini-official-grad)" d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81"/>
      </g>
    </g>

    <!-- 5. Official Google Cloud Vertex AI Logo -->
    <g id="logo-vertex-ai">
      <path fill="#669df6" d="M20,13.89A.77.77,0,0,0,19,13.73l-7,5.14v.22a.72.72,0,1,1,0,1.43v0a.74.74,0,0,0,.45-.15l7.41-5.47A.76.76,0,0,0,20,13.89Z"/>
      <path fill="#aecbfa" d="M12,20.52a.72.72,0,0,1,0-1.43h0v-.22L5,13.73a.76.76,0,0,0-1,.16.74.74,0,0,0,.16,1l7.41,5.47a.73.73,0,0,0,.44.15v0Z"/>
      <path fill="#4285f4" d="M12,18.34a1.47,1.47,0,1,0,1.47,1.47A1.47,1.47,0,0,0,12,18.34Zm0,2.18a.72.72,0,1,1,.72-.71A.71.71,0,0,1,12,20.52Z"/>
      <path fill="#aecbfa" d="M6,6.11a.76.76,0,0,1-.75-.75V3.48a.76.76,0,1,1,1.51,0V5.36A.76.76,0,0,1,6,6.11Z"/>
      <circle fill="#aecbfa" cx="5.98" cy="12" r="0.76"/>
      <circle fill="#aecbfa" cx="5.98" cy="9.79" r="0.76"/>
      <circle fill="#aecbfa" cx="5.98" cy="7.57" r="0.76"/>
      <path fill="#4285f4" d="M18,8.31a.76.76,0,0,1-.75-.76V5.67a.75.75,0,1,1,1.5,0V7.55A.75.75,0,0,1,18,8.31Z"/>
      <circle fill="#4285f4" cx="18.02" cy="12.01" r="0.76"/>
      <circle fill="#4285f4" cx="18.02" cy="9.76" r="0.76"/>
      <circle fill="#4285f4" cx="18.02" cy="3.48" r="0.76"/>
      <path fill="#669df6" d="M12,15a.76.76,0,0,1-.75-.75V12.34a.76.76,0,0,1,1.51,0v1.89A.76.76,0,0,1,12,15Z"/>
      <circle fill="#669df6" cx="12" cy="16.45" r="0.76"/>
      <circle fill="#669df6" cx="12" cy="10.14" r="0.76"/>
      <circle fill="#669df6" cx="12" cy="7.92" r="0.76"/>
      <path fill="#4285f4" d="M15,10.54a.76.76,0,0,1-.75-.75V7.91a.76.76,0,1,1,1.51,0V9.79A.76.76,0,0,1,15,10.54Z"/>
      <circle fill="#4285f4" cx="15.01" cy="5.69" r="0.76"/>
      <circle fill="#4285f4" cx="15.01" cy="14.19" r="0.76"/>
      <circle fill="#4285f4" cx="15.01" cy="11.97" r="0.76"/>
      <circle fill="#aecbfa" cx="8.99" cy="14.19" r="0.76"/>
      <circle fill="#aecbfa" cx="8.99" cy="7.92" r="0.76"/>
      <circle fill="#aecbfa" cx="8.99" cy="5.69" r="0.76"/>
      <path fill="#aecbfa" d="M9,12.73A.76.76,0,0,1,8.24,12V10.1a.75.75,0,1,1,1.5,0V12A.75.75,0,0,1,9,12.73Z"/>
    </g>

    <!-- 6. Official Google Cloud BigQuery Logo -->
    <g id="logo-bigquery">
      <path fill="#aecbfa" d="M6.73,10.83v2.63A4.91,4.91,0,0,0,8.44,15.2V10.83Z"/>
      <path fill="#669df6" d="M9.89,8.41v7.53A7.62,7.62,0,0,0,11,16,8,8,0,0,0,12,16V8.41Z"/>
      <path fill="#aecbfa" d="M13.64,11.86v3.29a5,5,0,0,0,1.7-1.82V11.86Z"/>
      <path fill="#4285f4" d="M17.74,16.32l-1.42,1.42a.42.42,0,0,0,0,.6l3.54,3.54a.42.42,0,0,0,.59,0l1.43-1.43a.42.42,0,0,0,0-.59l-3.54-3.54a.42.42,0,0,0-.6,0"/>
      <path fill="#669df6" d="M11,2a9,9,0,1,0,9,9,9,9,0,0,0-9-9m0,15.69A6.68,6.68,0,1,1,17.69,11,6.68,6.68,0,0,1,11,17.69"/>
    </g>

    <!-- 7. Official Google Cloud Trace Logo -->
    <g id="logo-cloud-trace">
      <polygon fill="#4285f4" points="12 14 22 14 22 10 12 10 12 14"/>
      <polygon fill="#4285f4" points="12 22 22 22 22 18 12 18 12 22"/>
      <polygon fill="#669df6" points="8 22 12 22 12 18 8 18 8 22"/>
      <rect fill="#669df6" x="2" y="2" width="6" height="4"/>
      <rect fill="#669df6" x="2" y="10" width="10" height="4"/>
    </g>

    <!-- 8. Official React Logo -->
    <g id="logo-react">
      <circle cx="12" cy="12" r="2.2" fill="#61DAFB"/>
      <ellipse cx="12" cy="12" rx="10" ry="4" fill="none" stroke="#61DAFB" stroke-width="1.2" transform="rotate(30 12 12)"/>
      <ellipse cx="12" cy="12" rx="10" ry="4" fill="none" stroke="#61DAFB" stroke-width="1.2" transform="rotate(90 12 12)"/>
      <ellipse cx="12" cy="12" rx="10" ry="4" fill="none" stroke="#61DAFB" stroke-width="1.2" transform="rotate(150 12 12)"/>
    </g>

    <!-- 9. Clinical DB / Table Logo -->
    <g id="logo-clinical-db">
      <rect x="3" y="3" width="18" height="18" rx="3" ry="3" fill="#E8F0FE" stroke="#1A73E8" stroke-width="1.5"/>
      <line x1="3" y1="9" x2="21" y2="9" stroke="#1A73E8" stroke-width="1.5"/>
      <line x1="9" y1="9" x2="9" y2="21" stroke="#1A73E8" stroke-width="1.2"/>
      <line x1="15" y1="9" x2="15" y2="21" stroke="#1A73E8" stroke-width="1.2"/>
      <circle cx="6" cy="6" r="1.5" fill="#EA4335"/>
      <circle cx="12" cy="6" r="1.5" fill="#1A73E8"/>
    </g>

    <!-- 10. Vector DB / Circuit Breaker Logo -->
    <g id="logo-vector-fallback">
      <circle cx="12" cy="12" r="10" fill="#E8F0FE" stroke="#F9AB00" stroke-width="1.5"/>
      <polygon points="13,3 6,13 11,13 10,21 18,10 13,10" fill="#F9AB00"/>
    </g>

    <!-- 11. Safe Refusal Barrier Logo -->
    <g id="logo-refusal">
      <polygon points="7,2 17,2 22,7 22,17 17,22 7,22 2,17 2,7" fill="#EA4335"/>
      <line x1="7" y1="12" x2="17" y2="12" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
    </g>
  </defs>

  <!-- ========================================== -->
  <!-- HEADER -->
  <!-- ========================================== -->
  <g id="header" transform="translate(40, 22)">
    <text x="0" y="0" font-size="11" font-weight="700" fill="#1A73E8" letter-spacing="1">SYSTEM ARCHITECTURE</text>
    <text x="0" y="24" font-size="19" font-weight="700" fill="#202124">MedQuAD Multi-Agent Clinical Research Platform</text>
    <text x="0" y="42" font-size="12" font-weight="400" fill="#5F6368">Google Cloud Run Microservice Workload • ADK Supervisor-Worker Pipeline • Vertex AI Foundation Models</text>
    <line x1="0" y1="50" x2="1100" y2="50" stroke="#E0E3E7" stroke-width="1"/>
  </g>

  <!-- ========================================== -->
  <!-- TIER 1: INGRESS & PERIMETER DEFENSE -->
  <!-- ========================================== -->
  <g id="tier-1" transform="translate(40, 85)">
    <!-- Container -->
    <rect x="0" y="0" width="1100" height="120" rx="10" ry="10" fill="#F8F9FA" stroke="#E0E3E7" stroke-width="1"/>
    <text x="18" y="18" font-size="9.5" font-weight="700" fill="#5F6368" letter-spacing="0.5">TIER 1: INGRESS &amp; PERIMETER DEFENSE</text>

    <!-- 1. Clinician UI (Browser Window Shape) -->
    <g transform="translate(18, 28)" filter="url(#shadow-card)">
      <rect width="130" height="78" rx="8" ry="8" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.5"/>
      <path d="M 0 8 Q 0 0 8 0 L 122 0 Q 130 0 130 8 L 130 18 L 0 18 Z" fill="#E8F0FE"/>
      <circle cx="10" cy="9" r="2.5" fill="#EA4335"/>
      <circle cx="18" cy="9" r="2.5" fill="#FBBC04"/>
      <circle cx="26" cy="9" r="2.5" fill="#34A853"/>
      <g transform="translate(53, 23)"><use href="#logo-react"/></g>
      <text x="65" y="56" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Clinician UI</text>
      <text x="65" y="70" font-size="9" font-weight="500" fill="#5F6368" text-anchor="middle">React 18 / REST API</text>
    </g>

    <!-- Arrow 1: UI -> Cloud Armor -->
    <line x1="148" y1="67" x2="205" y2="67" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arr-blue)"/>
    <rect x="150" y="47" width="52" height="15" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="176" y="58" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">1. HTTPS</text>

    <!-- 2. Cloud Armor (Shield Shape + Official Logo) -->
    <g transform="translate(205, 23)" filter="url(#shadow-shield)">
      <path d="M 12 0 L 123 0 L 135 15 L 135 56 Q 135 84 67 90 Q 0 84 0 56 L 0 15 Z" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.8"/>
      <path d="M 12 0 L 123 0 L 135 15 L 135 26 L 0 26 L 0 15 Z" fill="#E8F0FE"/>
      <g transform="translate(55, 30)"><use href="#logo-cloud-armor"/></g>
      <text x="67" y="66" font-size="11.5" font-weight="700" fill="#202124" text-anchor="middle">Cloud Armor</text>
      <text x="67" y="79" font-size="9" font-weight="600" fill="#1A73E8" text-anchor="middle">L7 WAF &amp; DDoS</text>
    </g>

    <!-- Arrow 2: Cloud Armor -> Model Armor -->
    <line x1="340" y1="67" x2="400" y2="67" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arr-blue)"/>
    <rect x="342" y="47" width="54" height="15" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="369" y="58" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">2. Cleaned</text>

    <!-- 3. Model Armor (Shield Shape + Official Logo) -->
    <g transform="translate(400, 23)" filter="url(#shadow-shield)">
      <path d="M 12 0 L 128 0 L 140 15 L 140 56 Q 140 84 70 90 Q 0 84 0 56 L 0 15 Z" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.8"/>
      <path d="M 12 0 L 128 0 L 140 15 L 140 26 L 0 26 L 0 15 Z" fill="#E8F0FE"/>
      <g transform="translate(58, 30)"><use href="#logo-model-armor"/></g>
      <text x="70" y="66" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Model Armor</text>
      <text x="70" y="79" font-size="8.5" font-weight="600" fill="#5F6368" text-anchor="middle">Layer 8 Guardrail</text>
    </g>

    <!-- Arrow 3a: Model Armor -> Safe Refusal Exit -->
    <line x1="540" y1="67" x2="615" y2="67" stroke="#EA4335" stroke-width="1.8" marker-end="url(#arr-red)"/>
    <rect x="546" y="47" width="62" height="15" rx="4" ry="4" fill="#FFFFFF" stroke="#EA4335" stroke-width="0.8"/>
    <text x="577" y="58" font-size="7.5" font-weight="700" fill="#EA4335" text-anchor="middle">3a. Refusal</text>

    <!-- 4. Safe Refusal Engine Exit (Octagonal Stop Barrier) -->
    <g transform="translate(615, 23)" filter="url(#shadow-alert)">
      <polygon points="25,0 460,0 485,25 485,65 460,90 25,90 0,65 0,25" fill="#FEF2F2" stroke="#EA4335" stroke-width="2"/>
      <g transform="translate(24, 33)"><use href="#logo-refusal"/></g>
      <text x="255" y="41" font-size="12" font-weight="700" fill="#EA4335" text-anchor="middle">Safe Refusal Engine Exit</text>
      <text x="255" y="57" font-size="9.5" font-weight="600" fill="#C5221F" text-anchor="middle">Dosing / Personal Medical Advice Block</text>
      <text x="255" y="72" font-size="8" fill="#5F6368" text-anchor="middle">Sub-5ms Intercept • Zero Model Tokens Billed</text>
    </g>
  </g>

  <!-- ========================================== -->
  <!-- CONNECTOR: Model Armor -> Cloud Run Container Workload -->
  <!-- ========================================== -->
  <path d="M 470 197 L 470 220 L 140 220 L 140 240" fill="none" stroke="#34A853" stroke-width="2" marker-end="url(#arr-green)"/>
  <rect x="180" y="210" width="260" height="20" rx="5" ry="5" fill="#FFFFFF" stroke="#CEEAD6" stroke-width="1.2"/>
  <text x="310" y="224" font-size="8.5" font-weight="700" fill="#188038" text-anchor="middle">3b. Sanitized Query (18 HIPAA PHI Identifiers Scrubbed)</text>

  <!-- ========================================== -->
  <!-- TIER 2: GOOGLE CLOUD RUN (SERVERLESS WORKLOAD CONTAINER) -->
  <!-- ========================================== -->
  <g id="tier-2" transform="translate(40, 240)" filter="url(#shadow-cloudrun)">
    <!-- Container Replica 3 (Back) -->
    <rect x="16" y="0" width="1100" height="235" rx="12" ry="12" fill="#E8EAED" stroke="#BDC1C6" stroke-width="1.2"/>
    <rect x="1000" y="4" width="96" height="15" rx="3" ry="3" fill="#BDC1C6"/>
    <text x="1048" y="15" font-size="7" font-weight="700" fill="#FFFFFF" text-anchor="middle">Container Inst N</text>

    <!-- Container Replica 2 (Middle) -->
    <rect x="8" y="6" width="1100" height="235" rx="12" ry="12" fill="#F1F3F4" stroke="#DADCE0" stroke-width="1.2"/>
    <rect x="992" y="10" width="96" height="15" rx="3" ry="3" fill="#DADCE0"/>
    <text x="1040" y="21" font-size="7" font-weight="700" fill="#5F6368" text-anchor="middle">Container Inst 2</text>

    <!-- Container Replica 1 (Front Active Service) -->
    <rect x="0" y="12" width="1100" height="235" rx="12" ry="12" fill="#FFFFFF" stroke="#4285F4" stroke-width="2.2"/>
    
    <!-- Cloud Run Header Banner -->
    <path d="M 0 24 Q 0 12 12 12 L 1088 12 Q 1100 12 1100 24 L 1100 48 L 0 48 Z" fill="#E8F0FE"/>
    <g transform="translate(16, 18)"><use href="#logo-cloud-run"/></g>
    <text x="48" y="32" font-size="11" font-weight="700" fill="#1A73E8" letter-spacing="0.5">TIER 2: GOOGLE CLOUD RUN (SERVERLESS CONTAINER WORKLOAD • 0 → N REPLICAS)</text>
    <text x="48" y="44" font-size="8.5" font-weight="500" fill="#5F6368">FastAPI ASGI Microservice Packaging the Google ADK Multi-Agent Core in Python 3.11</text>
    
    <!-- Autoscaling Badge -->
    <rect x="980" y="18" width="108" height="20" rx="4" ry="4" fill="#1A73E8"/>
    <text x="1034" y="32" font-size="8" font-weight="700" fill="#FFFFFF" text-anchor="middle">Autoscaling (0 → N)</text>

    <!-- ==================== INSIDE CLOUD RUN ==================== -->

    <!-- Component 1: FastAPI Gateway & Memory -->
    <g transform="translate(18, 62)" filter="url(#shadow-card)">
      <rect width="180" height="165" rx="8" ry="8" fill="#FFFFFF" stroke="#4285F4" stroke-width="1.5"/>
      <rect width="180" height="28" rx="8" ry="8" fill="#F8F9FA"/>
      <rect y="18" width="180" height="10" fill="#F8F9FA"/>
      <text x="90" y="19" font-size="11" font-weight="700" fill="#202124" text-anchor="middle">FastAPI Gateway</text>
      <!-- Details -->
      <rect x="12" y="38" width="156" height="34" rx="4" ry="4" fill="#F1F3F4"/>
      <text x="90" y="52" font-size="8.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Uvicorn ASGI Event Loop</text>
      <text x="90" y="64" font-size="7.5" fill="#5F6368" text-anchor="middle">Non-blocking async/await</text>
      
      <rect x="12" y="80" width="156" height="42" rx="4" ry="4" fill="#F8F9FA" stroke="#DADCE0" stroke-width="0.8"/>
      <text x="90" y="95" font-size="8.5" font-weight="700" fill="#202124" text-anchor="middle">Session Memory</text>
      <text x="90" y="108" font-size="7.5" fill="#5F6368" text-anchor="middle">Multi-turn History Context</text>
      <text x="90" y="118" font-size="7" fill="#188038" text-anchor="middle">LRU Cache + BigQuery Sync</text>
      
      <text x="90" y="145" font-size="8" font-weight="600" fill="#4285F4" text-anchor="middle">concurrency=80 per Inst</text>
    </g>

    <!-- Arrow 4: Gateway -> Root Orchestrator -->
    <line x1="198" y1="144" x2="248" y2="144" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arr-blue)"/>
    <rect x="200" y="124" width="48" height="15" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="224" y="135" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">4. Dispatch</text>

    <!-- Component 2: Root Orchestrator (Supervisor Agent) -->
    <g transform="translate(248, 62)" filter="url(#shadow-card)">
      <rect width="230" height="165" rx="8" ry="8" fill="#FFFFFF" stroke="#1A73E8" stroke-width="1.8"/>
      <rect width="230" height="28" rx="8" ry="8" fill="#E8F0FE"/>
      <rect y="18" width="230" height="10" fill="#E8F0FE"/>
      <text x="115" y="19" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Root Orchestrator (Python)</text>
      
      <!-- Python Service Tag -->
      <rect x="15" y="38" width="200" height="42" rx="4" ry="4" fill="#F1F3F4"/>
      <text x="115" y="52" font-size="8.5" font-weight="700" fill="#202124" text-anchor="middle">Supervisor Agent Logic</text>
      <text x="115" y="64" font-size="7.5" fill="#5F6368" text-anchor="middle">backend/agents/orchestrator.py</text>
      <text x="115" y="74" font-size="7.5" font-weight="600" fill="#1A73E8" text-anchor="middle">max_iterations=2 Safety Ceiling</text>

      <!-- External LLM Call Pill -->
      <rect x="15" y="90" width="200" height="60" rx="6" ry="6" fill="#F8F9FA" stroke="#D2E3FC" stroke-width="1.2"/>
      <text x="115" y="105" font-size="7.5" font-weight="700" fill="#5F6368" text-anchor="middle">EXTERNAL INFERENCE CALL</text>
      <g transform="translate(25, 116)"><use href="#logo-gemini"/></g>
      <text x="125" y="128" font-size="10" font-weight="700" fill="#1A73E8" text-anchor="middle">Gemini 2.5 Flash</text>
      <text x="125" y="141" font-size="7.5" fill="#5F6368" text-anchor="middle">Vertex AI Managed Endpoint</text>
    </g>

    <!-- Arrow 5: Orchestrator -> Clinical Researcher -->
    <line x1="478" y1="144" x2="528" y2="144" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arr-blue)"/>
    <rect x="479" y="124" width="48" height="15" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="503" y="135" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">5. Intent</text>

    <!-- Component 3: Clinical Researcher (Worker Agent Pool in Python) -->
    <g transform="translate(528, 56)" filter="url(#shadow-card)">
      <!-- Worker Replica 3 (Back) -->
      <rect x="12" y="2" width="250" height="165" rx="8" ry="8" fill="#E8EAED" stroke="#BDC1C6" stroke-width="1"/>
      <rect x="180" y="5" width="76" height="12" rx="3" ry="3" fill="#BDC1C6"/>
      <text x="218" y="14" font-size="6.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">Worker M</text>
      
      <!-- Worker Replica 2 (Middle) -->
      <rect x="6" y="5" width="250" height="165" rx="8" ry="8" fill="#F1F3F4" stroke="#DADCE0" stroke-width="1"/>
      <rect x="174" y="8" width="76" height="12" rx="3" ry="3" fill="#DADCE0"/>
      <text x="212" y="17" font-size="6.5" font-weight="700" fill="#5F6368" text-anchor="middle">Worker 2</text>

      <!-- Worker Replica 1 (Front) -->
      <rect x="0" y="8" width="250" height="165" rx="8" ry="8" fill="#FFFFFF" stroke="#1A73E8" stroke-width="2"/>
      <rect x="0" y="8" width="250" height="28" rx="8" ry="8" fill="#E8F0FE"/>
      <rect x="0" y="26" width="250" height="10" fill="#E8F0FE"/>
      <!-- Scaling Pool Badge -->
      <rect x="165" y="14" width="78" height="14" rx="3" ry="3" fill="#1A73E8"/>
      <text x="204" y="24" font-size="6.8" font-weight="700" fill="#FFFFFF" text-anchor="middle">1 → M Coroutines</text>
      <text x="82" y="27" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Clinical Researcher</text>

      <!-- Python Service Tag -->
      <rect x="12" y="44" width="226" height="44" rx="4" ry="4" fill="#F1F3F4"/>
      <text x="125" y="58" font-size="8.5" font-weight="700" fill="#202124" text-anchor="middle">Python Agent Worker (Stateless)</text>
      <text x="125" y="70" font-size="7.5" fill="#5F6368" text-anchor="middle">Context Rewriting • Tool Calling Client</text>
      <text x="125" y="80" font-size="7.5" font-weight="600" fill="#1A73E8" text-anchor="middle">Runs in Cloud Run Event Loop</text>

      <!-- External LLM Call Pill -->
      <rect x="12" y="96" width="226" height="60" rx="6" ry="6" fill="#F8F9FA" stroke="#D2E3FC" stroke-width="1.2"/>
      <text x="125" y="110" font-size="7.5" font-weight="700" fill="#5F6368" text-anchor="middle">EXTERNAL INFERENCE CALL</text>
      <g transform="translate(25, 122)"><use href="#logo-gemini"/></g>
      <text x="135" y="134" font-size="10" font-weight="700" fill="#1A73E8" text-anchor="middle">Gemini 2.5 Pro</text>
      <text x="135" y="147" font-size="7.5" fill="#5F6368" text-anchor="middle">Vertex AI Managed Synthesis</text>
    </g>

    <!-- Arrow 8: Researcher -> Reviewer -->
    <line x1="778" y1="144" x2="828" y2="144" stroke="#1A73E8" stroke-width="1.8" marker-end="url(#arr-blue)"/>
    <rect x="780" y="124" width="48" height="15" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
    <text x="804" y="135" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">8. Draft</text>

    <!-- Component 4: Reviewer & QC Gate (Auditor Agent) -->
    <g transform="translate(828, 62)" filter="url(#shadow-card)">
      <rect width="254" height="165" rx="8" ry="8" fill="#FFFFFF" stroke="#34A853" stroke-width="1.8"/>
      <rect width="254" height="28" rx="8" ry="8" fill="#E6F4EA"/>
      <rect y="18" width="254" height="10" fill="#E6F4EA"/>
      <text x="127" y="19" font-size="11.5" font-weight="700" fill="#137333" text-anchor="middle">Reviewer &amp; QC Gate (Python)</text>

      <!-- Python Service Tag -->
      <rect x="12" y="38" width="230" height="42" rx="4" ry="4" fill="#F1F3F4"/>
      <text x="127" y="52" font-size="8.5" font-weight="700" fill="#202124" text-anchor="middle">Auditor Logic + CitationVerifier</text>
      <text x="127" y="64" font-size="7.5" fill="#5F6368" text-anchor="middle">backend/agents/reviewer_agent.py</text>
      <text x="127" y="74" font-size="7.5" font-weight="600" fill="#137333" text-anchor="middle">Deterministic 1:1 Grounding Match</text>

      <!-- External LLM Call Pill -->
      <rect x="12" y="90" width="230" height="60" rx="6" ry="6" fill="#F8F9FA" stroke="#CEEAD6" stroke-width="1.2"/>
      <text x="127" y="105" font-size="7.5" font-weight="700" fill="#5F6368" text-anchor="middle">EXTERNAL INFERENCE CALL</text>
      <g transform="translate(25, 116)"><use href="#logo-gemini"/></g>
      <text x="135" y="128" font-size="10" font-weight="700" fill="#137333" text-anchor="middle">Gemini 3.5 Flash</text>
      <text x="135" y="141" font-size="7.5" fill="#5F6368" text-anchor="middle">Vertex AI Zero-Bias Verification</text>
    </g>
  </g>

  <!-- ========================================== -->
  <!-- VERTICAL CONNECTORS: Cloud Run Researcher <-> Tier 3 Data Stores -->
  <!-- ========================================== -->
  <!-- 6. Query (Down) -->
  <line x1="620" y1="487" x2="620" y2="538" stroke="#1A73E8" stroke-width="2" marker-end="url(#arr-blue)"/>
  <rect x="535" y="500" width="80" height="17" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
  <text x="575" y="512" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">6. Hybrid Query</text>

  <!-- 7. Chunks (Up) -->
  <line x1="710" y1="538" x2="710" y2="487" stroke="#1A73E8" stroke-width="2" marker-end="url(#arr-blue)"/>
  <rect x="715" y="500" width="85" height="17" rx="4" ry="4" fill="#FFFFFF" stroke="#1A73E8" stroke-width="0.8"/>
  <text x="757" y="512" font-size="7.5" font-weight="700" fill="#1A73E8" text-anchor="middle">7. Top-K Chunks</text>

  <!-- Telemetry Sink (Down dashed) -->
  <line x1="970" y1="487" x2="970" y2="538" stroke="#5F6368" stroke-width="1.8" stroke-dasharray="4 3" marker-end="url(#arr-muted)"/>
  <rect x="975" y="500" width="105" height="17" rx="4" ry="4" fill="#FFFFFF" stroke="#DADCE0" stroke-width="0.8"/>
  <text x="1027" y="512" font-size="7.5" font-weight="700" fill="#5F6368" text-anchor="middle">OTel Spans &amp; Metrics</text>

  <!-- ========================================== -->
  <!-- TIER 3: GROUNDING DATA & OBSERVABILITY SINK -->
  <!-- ========================================== -->
  <g id="tier-3" transform="translate(40, 538)">
    <!-- Container -->
    <rect x="0" y="0" width="1100" height="135" rx="10" ry="10" fill="#F8F9FA" stroke="#E0E3E7" stroke-width="1"/>
    <text x="18" y="18" font-size="9.5" font-weight="700" fill="#5F6368" letter-spacing="0.5">TIER 3: GROUNDING DATA STORES &amp; OBSERVABILITY SINK (3D DATABASE CYLINDERS)</text>

    <!-- Store 1: Vertex AI Search -->
    <g transform="translate(18, 25)" filter="url(#shadow-card)">
      <!-- Replica Back Cylinder -->
      <ellipse cx="127" cy="10" rx="112" ry="9" fill="#E8EAED" stroke="#BDC1C6" stroke-width="1"/>
      <path d="M 15 10 L 15 88 A 112 9 0 0 0 239 88 L 239 10 Z" fill="#E8EAED" stroke="#BDC1C6" stroke-width="1"/>
      <ellipse cx="127" cy="88" rx="112" ry="9" fill="#DADCE0" stroke="#BDC1C6" stroke-width="1"/>
      <!-- Front Main Cylinder -->
      <ellipse cx="120" cy="14" rx="112" ry="9" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <path d="M 8 14 L 8 92 A 112 9 0 0 0 232 92 L 232 14 Z" fill="url(#cylinder-grad)" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="92" rx="112" ry="9" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="52" rx="112" ry="9" fill="none" stroke="#DADCE0" stroke-width="1" stroke-dasharray="3 3"/>
      <!-- Logo & Text -->
      <g transform="translate(20, 34)"><use href="#logo-vertex-ai"/></g>
      <text x="135" y="44" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Vertex AI Search</text>
      <text x="135" y="58" font-size="9" font-weight="600" fill="#202124" text-anchor="middle">NIH MedQuAD Datastore</text>
      <text x="135" y="70" font-size="8" fill="#5F6368" text-anchor="middle">16,400+ Records • Scaled Serving</text>
    </g>

    <!-- Store 2: Clinical DB Tool -->
    <g transform="translate(290, 25)" filter="url(#shadow-card)">
      <ellipse cx="120" cy="14" rx="112" ry="9" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <path d="M 8 14 L 8 92 A 112 9 0 0 0 232 92 L 232 14 Z" fill="url(#cylinder-grad)" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="92" rx="112" ry="9" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="52" rx="112" ry="9" fill="none" stroke="#DADCE0" stroke-width="1" stroke-dasharray="3 3"/>
      <g transform="translate(20, 34)"><use href="#logo-clinical-db"/></g>
      <text x="135" y="44" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Clinical DB Tool</text>
      <text x="135" y="58" font-size="9" font-weight="600" fill="#202124" text-anchor="middle">Biomarker &amp; Lab Thresholds</text>
      <text x="135" y="70" font-size="8" fill="#5F6368" text-anchor="middle">Diagnostic Reference Ranges</text>
    </g>

    <!-- Store 3: Vector DB Fallback -->
    <g transform="translate(562, 25)" filter="url(#shadow-card)">
      <ellipse cx="120" cy="14" rx="112" ry="9" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <path d="M 8 14 L 8 92 A 112 9 0 0 0 232 92 L 232 14 Z" fill="url(#cylinder-grad)" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="92" rx="112" ry="9" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="120" cy="52" rx="112" ry="9" fill="none" stroke="#DADCE0" stroke-width="1" stroke-dasharray="3 3"/>
      <g transform="translate(20, 34)"><use href="#logo-vector-fallback"/></g>
      <text x="135" y="44" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Vector DB Fallback</text>
      <text x="135" y="58" font-size="9" font-weight="600" fill="#202124" text-anchor="middle">Circuit Breaker Store</text>
      <text x="135" y="70" font-size="8" fill="#5F6368" text-anchor="middle">Sub-50ms In-Memory Failover</text>
    </g>

    <!-- Store 4: Observability Sink (BigQuery & Cloud Trace) -->
    <g transform="translate(834, 25)" filter="url(#shadow-card)">
      <ellipse cx="124" cy="14" rx="116" ry="9" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <path d="M 8 14 L 8 92 A 116 9 0 0 0 240 92 L 240 14 Z" fill="url(#cylinder-grad)" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="124" cy="92" rx="116" ry="9" fill="#E8F0FE" stroke="#4285F4" stroke-width="1.8"/>
      <ellipse cx="124" cy="52" rx="116" ry="9" fill="none" stroke="#DADCE0" stroke-width="1" stroke-dasharray="3 3"/>
      <!-- Logos & Text -->
      <g transform="translate(18, 34)"><use href="#logo-bigquery"/></g>
      <g transform="translate(206, 34)"><use href="#logo-cloud-trace"/></g>
      <text x="124" y="44" font-size="11.5" font-weight="700" fill="#1A73E8" text-anchor="middle">Cloud Trace &amp; BigQuery</text>
      <text x="124" y="58" font-size="9" font-weight="600" fill="#202124" text-anchor="middle">Telemetry &amp; Audit Sink</text>
      <text x="124" y="70" font-size="8" fill="#5F6368" text-anchor="middle">Distributed Spans &amp; Eval Logs</text>
    </g>
  </g>

  <!-- Footer -->
  <text x="40" y="702" font-size="9.5" fill="#70757A">MedQuAD Enterprise Architecture • Capstone 506616 • HIPAA Safe Harbor Compliant • Google Cloud Run &amp; Vertex AI</text>
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
    svg {{ display: block; width: 1180px; height: 720px; }}
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
        "--window-size=1180,720",
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
