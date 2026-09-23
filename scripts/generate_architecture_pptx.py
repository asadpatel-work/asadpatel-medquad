"""Generate MedQuAD Architecture Diagram in 100% Native Editable PowerPoint Shapes.

Creates docs/medquad_architecture_diagram.pptx:
- Built strictly with native PPTX shapes (rounded rectangles, text boxes, connectors).
- Every card, text label, title, subtitle, and badge is directly clickable and editable in PowerPoint/Google Slides.
- Widescreen 16:9 layout (13.333" x 7.5").
- Slide 1: Complete 3-Tier Enterprise Architecture (Ingress, Cloud Run Multi-Agent Core, Data Stores).
- Slide 2: Multi-Agent Core Deep-Dive (Google ADK Supervisor-Worker Topology & Protocol Flow).
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

# Palette
COLOR_BG = RGBColor(248, 249, 250)         # #F8F9FA
COLOR_CARD_BG = RGBColor(255, 255, 255)    # #FFFFFF
COLOR_BORDER = RGBColor(218, 220, 224)     # #DADCE0
COLOR_TEXT_DARK = RGBColor(32, 33, 36)     # #202124
COLOR_TEXT_MUTED = RGBColor(95, 99, 104)   # #5F6368
COLOR_PRIMARY = RGBColor(26, 115, 232)     # #1A73E8 (Google Blue)
COLOR_PRIMARY_LIGHT = RGBColor(232, 240, 254) # #E8F0FE
COLOR_GREEN = RGBColor(24, 128, 56)        # #188038 (Google Green)
COLOR_GREEN_LIGHT = RGBColor(230, 244, 234) # #E6F4EA
COLOR_AMBER = RGBColor(176, 96, 0)         # #B06000
COLOR_AMBER_LIGHT = RGBColor(254, 247, 224) # #FEF7E0
COLOR_RED = RGBColor(217, 48, 37)          # #D93025
COLOR_RED_LIGHT = RGBColor(252, 232, 230)  # #FCE8E6

FONT_FAMILY = "Arial"

def set_slide_background(slide):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = COLOR_BG

def add_header(slide, category: str, title: str, subtitle: str):
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(11.733), Inches(0.85))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p_cat = tf.paragraphs[0]
    p_cat.text = category.upper()
    p_cat.font.name = FONT_FAMILY
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_PRIMARY
    
    p_title = tf.add_paragraph()
    p_title.text = title
    p_title.font.name = FONT_FAMILY
    p_title.font.size = Pt(18)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_TEXT_DARK
    p_title.space_before = Pt(2)
    
    p_sub = tf.add_paragraph()
    p_sub.text = subtitle
    p_sub.font.name = FONT_FAMILY
    p_sub.font.size = Pt(9.5)
    p_sub.font.color.rgb = COLOR_TEXT_MUTED
    p_sub.space_before = Pt(2)

def add_container(slide, left, top, width, height, label: str, border_color=COLOR_BORDER, border_width=1.0, fill_color=COLOR_CARD_BG):
    container = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    container.fill.solid()
    container.fill.fore_color.rgb = fill_color
    container.line.color.rgb = border_color
    container.line.width = Pt(border_width)
    
    tf = container.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.18)
    tf.margin_top = Inches(0.08)
    tf.margin_right = Inches(0.18)
    tf.margin_bottom = 0
    
    p = tf.paragraphs[0]
    p.text = label.upper()
    p.font.name = FONT_FAMILY
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MUTED
    return container

def add_card(slide, left, top, width, height, title: str, subtitle: str, body_lines: list[str],
             border_color=COLOR_PRIMARY, border_width=1.5, fill_color=COLOR_CARD_BG,
             title_color=COLOR_PRIMARY, model_badge: str | None = None, badge_bg=COLOR_PRIMARY_LIGHT, badge_color=COLOR_PRIMARY):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = fill_color
    card.line.color.rgb = border_color
    card.line.width = Pt(border_width)
    
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.14)
    tf.margin_top = Inches(0.12)
    tf.margin_right = Inches(0.14)
    tf.margin_bottom = Inches(0.1)
    
    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.name = FONT_FAMILY
    p0.font.size = Pt(10.5)
    p0.font.bold = True
    p0.font.color.rgb = title_color
    
    if subtitle:
        p1 = tf.add_paragraph()
        p1.text = subtitle
        p1.font.name = FONT_FAMILY
        p1.font.size = Pt(8.5)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_TEXT_DARK
        p1.space_before = Pt(1)
        
    for line in body_lines:
        p = tf.add_paragraph()
        p.text = f"•  {line}"
        p.font.name = FONT_FAMILY
        p.font.size = Pt(7.5)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(2)
        
    if model_badge:
        p_badge = tf.add_paragraph()
        p_badge.text = f"[{model_badge}]"
        p_badge.font.name = FONT_FAMILY
        p_badge.font.size = Pt(8)
        p_badge.font.bold = True
        p_badge.font.color.rgb = badge_color
        p_badge.space_before = Pt(4)
        
    return card

def add_arrow_with_pill(slide, x1, y1, x2, y2, label: str, color=COLOR_PRIMARY, is_horizontal=True):
    # Draw arrow connector
    arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW if is_horizontal else MSO_SHAPE.DOWN_ARROW,
                                   min(x1, x2), min(y1, y2) if not is_horizontal else y1 - Inches(0.04),
                                   abs(x2 - x1) if is_horizontal else Inches(0.12),
                                   Inches(0.08) if is_horizontal else abs(y2 - y1))
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = color
    arrow.line.fill.background()
    
    # Pill label
    pill_w = Inches(len(label) * 0.065 + 0.25)
    pill_h = Inches(0.22)
    pill_x = (x1 + x2) / 2 - pill_w / 2
    pill_y = (y1 + y2) / 2 - pill_h / 2 - Inches(0.15) if is_horizontal else (y1 + y2) / 2 - pill_h / 2
    
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, pill_x, pill_y, pill_w, pill_h)
    pill.fill.solid()
    pill.fill.fore_color.rgb = COLOR_CARD_BG
    pill.line.color.rgb = color
    pill.line.width = Pt(0.8)
    
    tf = pill.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = label
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT_FAMILY
    p.font.size = Pt(7)
    p.font.bold = True
    p.font.color.rgb = color

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # =========================================================================
    # SLIDE 1: End-to-End System Architecture (3-Tier Native Shapes)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    
    add_header(
        s1,
        category="System Architecture",
        title="MedQuAD Multi-Agent Clinical Research Platform",
        subtitle="Google Cloud Run Serverless Workload • Google ADK Multi-Agent Topology • Vertex AI Foundation Models"
    )
    
    # -------------------------------------------------------------------------
    # TIER 1: Ingress & Perimeter Defense
    # -------------------------------------------------------------------------
    add_container(s1, Inches(0.8), Inches(1.30), Inches(11.733), Inches(1.18),
                  label="Tier 1: Ingress & Perimeter Defense (Zero-Trust Security Perimeter)",
                  border_color=COLOR_BORDER, fill_color=COLOR_BG)
                  
    # Card 1: Clinician UI
    add_card(s1, Inches(1.0), Inches(1.52), Inches(2.7), Inches(0.84),
             title="Clinician Portal (UI)",
             subtitle="React 18 SPA • Cloud Run",
             body_lines=["HTTPS / SSE streaming response", "Zero-state client memory hydration"],
             border_color=COLOR_PRIMARY, title_color=COLOR_PRIMARY)
             
    # Arrow 1: UI -> Cloud Armor
    add_arrow_with_pill(s1, Inches(3.7), Inches(1.94), Inches(4.5), Inches(1.94), label="1. TLS 1.3 / SSO")
    
    # Card 2: Cloud Armor + IAP
    add_card(s1, Inches(4.5), Inches(1.52), Inches(3.0), Inches(0.84),
             title="Cloud Armor + IAP Proxy",
             subtitle="L7 WAF & Zero-Trust SSO",
             body_lines=["OWASP Top 10 • DDoS throttling", "Cryptographic JWT token validation"],
             border_color=COLOR_PRIMARY, title_color=COLOR_TEXT_DARK)
             
    # Arrow 2: Cloud Armor -> Model Armor
    add_arrow_with_pill(s1, Inches(7.5), Inches(1.94), Inches(8.3), Inches(1.94), label="2. WAF Clean")
    
    # Card 3: Model Armor
    add_card(s1, Inches(8.3), Inches(1.52), Inches(4.0), Inches(0.84),
             title="Google Cloud Model Armor",
             subtitle="Pre-Flight Guardrail & HIPAA DLP",
             body_lines=["Masks 18 Safe Harbor PHI identifiers before tokenization", "Deterministic Safe Refusal engine: blocks personal diagnosis in <5ms ($0 token spend)"],
             border_color=COLOR_PRIMARY, title_color=COLOR_PRIMARY)
             
    # -------------------------------------------------------------------------
    # Step-down connector from Model Armor to Tier 2 Cloud Run
    # -------------------------------------------------------------------------
    # Arrow down into Cloud Run
    pill_t12 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.8), Inches(2.52), Inches(3.7), Inches(0.24))
    pill_t12.fill.solid()
    pill_t12.fill.fore_color.rgb = COLOR_GREEN_LIGHT
    pill_t12.line.color.rgb = COLOR_GREEN
    pill_t12.line.width = Pt(1)
    tf_p = pill_t12.text_frame
    tf_p.word_wrap = False
    tf_p.margin_left = tf_p.margin_top = tf_p.margin_right = tf_p.margin_bottom = 0
    p_t12 = tf_p.paragraphs[0]
    p_t12.text = "✓ Sanitized Query (18 PHI Types Scrubbed • Pre-Flight Checked)"
    p_t12.alignment = PP_ALIGN.CENTER
    p_t12.font.name = FONT_FAMILY
    p_t12.font.size = Pt(7.5)
    p_t12.font.bold = True
    p_t12.font.color.rgb = COLOR_GREEN

    # -------------------------------------------------------------------------
    # TIER 2: Google Cloud Run Serverless Workload Container
    # -------------------------------------------------------------------------
    c_t2 = add_container(s1, Inches(0.8), Inches(2.80), Inches(11.733), Inches(2.35),
                         label="Tier 2: Google Cloud Run (Serverless Workload • In-Process Google ADK Multi-Agent Runtime)",
                         border_color=COLOR_PRIMARY, border_width=1.8, fill_color=COLOR_CARD_BG)
                         
    # Autoscaling pill top-right
    badge_auto = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.6), Inches(2.88), Inches(1.7), Inches(0.22))
    badge_auto.fill.solid()
    badge_auto.fill.fore_color.rgb = COLOR_PRIMARY
    badge_auto.line.fill.background()
    p_b = badge_auto.text_frame.paragraphs[0]
    p_b.text = "Autoscaling (0 → N)"
    p_b.alignment = PP_ALIGN.CENTER
    p_b.font.name = FONT_FAMILY
    p_b.font.size = Pt(7.5)
    p_b.font.bold = True
    p_b.font.color.rgb = COLOR_CARD_BG

    # Box 1: FastAPI Gateway
    add_card(s1, Inches(1.0), Inches(3.22), Inches(2.2), Inches(1.80),
             title="FastAPI Gateway",
             subtitle="ASGI Server & Memory",
             body_lines=[
                 "Uvicorn async request loop",
                 "SessionMemory LRU cache",
                 "Multi-turn history sync",
                 "Max concurrency = 80",
                 "Zero-idle serverless host"
             ],
             border_color=COLOR_BORDER, border_width=1.0, title_color=COLOR_TEXT_DARK)

    # Arrow: Gateway -> Orchestrator
    add_arrow_with_pill(s1, Inches(3.2), Inches(4.12), Inches(3.6), Inches(4.12), label="Dispatch")

    # Box 2: Root Orchestrator
    add_card(s1, Inches(3.6), Inches(3.22), Inches(2.6), Inches(1.80),
             title="Root Orchestrator",
             subtitle="Supervisor • Google ADK",
             body_lines=[
                 "Clinical intent classification",
                 "Emergency & scope lock triage",
                 "max_iterations=2 loop ceiling",
                 "Subagent delegation routing"
             ],
             border_color=COLOR_PRIMARY, title_color=COLOR_PRIMARY,
             model_badge="Gemini 2.5 Flash • <200ms", badge_bg=COLOR_PRIMARY_LIGHT, badge_color=COLOR_PRIMARY)

    # Arrow: Orchestrator -> Researcher
    add_arrow_with_pill(s1, Inches(6.2), Inches(4.12), Inches(6.6), Inches(4.12), label="Delegate")

    # Box 3: Clinical Researcher
    add_card(s1, Inches(6.6), Inches(3.22), Inches(2.9), Inches(1.80),
             title="Clinical Researcher",
             subtitle="Worker Agent Pool",
             body_lines=[
                 "Autonomous ReAct reasoning loop",
                 "Medical entity query rewriting",
                 "Multi-tool retrieval planning",
                 "Inline [1], [2] citation drafting"
             ],
             border_color=COLOR_PRIMARY, title_color=COLOR_PRIMARY,
             model_badge="Gemini 2.5 Pro • Deep Synthesis", badge_bg=COLOR_PRIMARY_LIGHT, badge_color=COLOR_PRIMARY)

    # Arrow: Researcher -> Reviewer
    add_arrow_with_pill(s1, Inches(9.5), Inches(4.12), Inches(9.9), Inches(4.12), label="Draft")

    # Box 4: Reviewer & QC Gate
    add_card(s1, Inches(9.9), Inches(3.22), Inches(2.4), Inches(1.80),
             title="Reviewer & QC Gate",
             subtitle="Independent Auditor",
             body_lines=[
                 "Zero shared hidden state",
                 "100% 1-to-1 chunk verification",
                 "Eliminates ungrounded claims",
                 "Prescriptive tone de-escalation"
             ],
             border_color=COLOR_GREEN, border_width=1.5, title_color=COLOR_GREEN,
             model_badge="Gemini 3.5 Flash • QC Pass", badge_bg=COLOR_GREEN_LIGHT, badge_color=COLOR_GREEN)

    # -------------------------------------------------------------------------
    # Connectors between Tier 2 and Tier 3
    # -------------------------------------------------------------------------
    # Down arrow: Researcher -> Search
    arr_d = s1.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(7.5), Inches(5.18), Inches(0.12), Inches(0.24))
    arr_d.fill.solid()
    arr_d.fill.fore_color.rgb = COLOR_PRIMARY
    arr_d.line.fill.background()
    
    pill_ret = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.6), Inches(5.20), Inches(1.8), Inches(0.20))
    pill_ret.fill.solid()
    pill_ret.fill.fore_color.rgb = COLOR_CARD_BG
    pill_ret.line.color.rgb = COLOR_PRIMARY
    pill_ret.line.width = Pt(0.8)
    p_ret = pill_ret.text_frame.paragraphs[0]
    p_ret.text = "Dense Semantic Query"
    p_ret.alignment = PP_ALIGN.CENTER
    p_ret.font.name = FONT_FAMILY
    p_ret.font.size = Pt(6.8)
    p_ret.font.bold = True
    p_ret.font.color.rgb = COLOR_PRIMARY

    # Up arrow: Chunks to Researcher
    arr_u = s1.shapes.add_shape(MSO_SHAPE.UP_ARROW, Inches(8.7), Inches(5.18), Inches(0.12), Inches(0.24))
    arr_u.fill.solid()
    arr_u.fill.fore_color.rgb = COLOR_PRIMARY
    arr_u.line.fill.background()

    pill_chk = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.9), Inches(5.20), Inches(1.8), Inches(0.20))
    pill_chk.fill.solid()
    pill_chk.fill.fore_color.rgb = COLOR_CARD_BG
    pill_chk.line.color.rgb = COLOR_PRIMARY
    pill_chk.line.width = Pt(0.8)
    p_chk = pill_chk.text_frame.paragraphs[0]
    p_chk.text = "Top-K Grounded NIH Chunks"
    p_chk.alignment = PP_ALIGN.CENTER
    p_chk.font.name = FONT_FAMILY
    p_chk.font.size = Pt(6.8)
    p_chk.font.bold = True
    p_chk.font.color.rgb = COLOR_PRIMARY

    # -------------------------------------------------------------------------
    # TIER 3: Data Stores & Observability Sink
    # -------------------------------------------------------------------------
    add_container(s1, Inches(0.8), Inches(5.45), Inches(11.733), Inches(1.50),
                  label="Tier 3: Grounding Data Stores & Observability Sink",
                  border_color=COLOR_BORDER, fill_color=COLOR_BG)

    # Store 1: Vertex AI Search
    add_card(s1, Inches(1.0), Inches(5.70), Inches(2.7), Inches(1.12),
             title="Vertex AI Search",
             subtitle="Authoritative NIH MedQuAD Index",
             body_lines=[
                 "16,400+ verified clinical Q&A records",
                 "500-token semantic chunks + 10% overlap",
                 "Managed hybrid dense + lexical retrieval"
             ],
             border_color=COLOR_PRIMARY, title_color=COLOR_PRIMARY)

    # Store 2: Clinical DB Tool
    add_card(s1, Inches(3.9), Inches(5.70), Inches(2.7), Inches(1.12),
             title="Clinical Reference DB",
             subtitle="Diagnostic Biomarkers & Labs",
             body_lines=[
                 "Standard laboratory reference ranges",
                 "Diagnostic cutoffs & normal intervals",
                 "Mock EHR clinical protocol tables"
             ],
             border_color=COLOR_PRIMARY, title_color=COLOR_PRIMARY)

    # Store 3: Vector DB Fallback
    add_card(s1, Inches(6.8), Inches(5.70), Inches(2.7), Inches(1.12),
             title="Vector DB Fallback",
             subtitle="Sub-50ms Circuit Breaker Store",
             body_lines=[
                 "Local in-memory FAISS vector index",
                 "Sub-50ms fallback on Vertex 504 timeouts",
                 "Guarantees 99.9% clinical availability"
             ],
             border_color=COLOR_AMBER, border_width=1.5, title_color=COLOR_AMBER)

    # Store 4: Observability Sink
    add_card(s1, Inches(9.7), Inches(5.70), Inches(2.6), Inches(1.12),
             title="Cloud Trace & BigQuery",
             subtitle="Observability & FinOps Sink",
             body_lines=[
                 "End-to-end OpenTelemetry distributed spans",
                 "Token consumption & cost telemetry",
                 "Nightly automated clinical audit logs"
             ],
             border_color=COLOR_TEXT_MUTED, border_width=1.2, title_color=COLOR_TEXT_DARK)

    # Footer note
    tb_foot = s1.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.733), Inches(0.35))
    tf_f = tb_foot.text_frame
    tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0
    p_foot = tf_f.paragraphs[0]
    p_foot.text = "MedQuAD Architecture • 100% Native Editable Shapes • Google Cloud Field Delivery Engineering Capstone"
    p_foot.font.name = FONT_FAMILY
    p_foot.font.size = Pt(8)
    p_foot.font.color.rgb = COLOR_TEXT_MUTED

    s1.notes_slide.notes_text_frame.text = (
        "Slide 1: Concrete end-to-end architecture diagram showing the visual flow across components:\n\n"
        "1. Ingress & Perimeter Defense: Clinician queries enter via Cloud Armor and FastAPI on Cloud Run. Model Armor scrubs 18 HIPAA PHI identifiers before any tokenization occurs.\n\n"
        "2. Safe Refusal Fast-Path: If personal medical advice or dosing is detected, the boundary engine halts execution in <5ms, returning an emergency disclaimer with zero token consumption.\n\n"
        "3. Multi-Agent Orchestration: Root Orchestrator (Gemini 2.5 Flash) triages intent and routes to Clinical Researcher (Gemini 2.5 Pro) under a strict max_iterations=2 loop ceiling.\n\n"
        "4. Grounding: Researcher retrieves 500-token semantic chunks from Vertex AI Search and reference lab ranges from ClinicalDBTool.\n\n"
        "5. Independent Verification: Reviewer & QC gate (Gemini 3.5 Flash) operates with zero shared hidden state, deterministically validating 100% citation ID matching before streaming release.\n\n"
        "6. High Availability: Circuit breaker gracefully falls back to local in-memory vector store on Vertex latency spikes or 504 timeouts."
    )

    # =========================================================================
    # SLIDE 2: Multi-Agent Core Deep Dive (Google ADK Supervisor-Worker Topology)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)

    add_header(
        s2,
        category="Multi-Agent Topology Deep Dive",
        title="Google ADK Supervisor-Worker Agent Execution Flow",
        subtitle="In-Process Modular Agent Architecture with Zero Inter-Service Latency and Isolated Reviewer State"
    )

    # 3 Large Agent Detail Cards
    # Agent 1: Root Orchestrator
    add_card(s2, Inches(0.8), Inches(1.50), Inches(3.6), Inches(4.30),
             title="1. Root Orchestrator (Supervisor)",
             subtitle="Gemini 2.5 Flash • Triage & Scope Lock",
             body_lines=[
                 "Role: Top-level supervisor controlling workflow lifecycle.",
                 "Intent Classification: Categorizes clinical queries vs. administrative vs. emergency prompts in <200ms.",
                 "Safe Refusal Gate: Instantly halts personal diagnosis and dosage inquiries with standard non-prescriptive disclaimers.",
                 "Loop Guard: Enforces immutable max_iterations=2 boundary to prevent infinite agent delegation.",
                 "Session State: Hydrates conversation turn history and coordinates subagent handoffs.",
                 "Telemetry: Emits root trace span and records end-to-end turn latency."
             ],
             border_color=COLOR_PRIMARY, border_width=2.0, title_color=COLOR_PRIMARY,
             model_badge="Cost: $0.075 / 1M Input Tokens | Latency: ~180ms", badge_bg=COLOR_PRIMARY_LIGHT, badge_color=COLOR_PRIMARY)

    # Arrow 1: Orchestrator -> Researcher
    add_arrow_with_pill(s2, Inches(4.4), Inches(3.40), Inches(4.9), Inches(3.40), label="Delegate Task")

    # Agent 2: Clinical Researcher
    add_card(s2, Inches(4.9), Inches(1.50), Inches(3.8), Inches(4.30),
             title="2. Clinical Researcher (Worker)",
             subtitle="Gemini 2.5 Pro • Deep Biomedical Reasoning",
             body_lines=[
                 "Role: Autonomous research worker executing grounding loops.",
                 "Query Expansion: Extracts medical entities and synonyms to formulate high-recall search syntax.",
                 "Tool Execution: Invokes Vertex AI Search Tool (NIH Corpus) and Clinical DB Tool via Python interfaces.",
                 "Evidence Chunk Ranking: Analyzes retrieved 500-token passages for clinical relevance and contraindications.",
                 "Grounded Drafting: Synthesizes complex clinical findings with mandatory bracketed [1], [2] citation anchors.",
                 "Cost Isolation: Expensive frontier reasoning is strictly confined to multi-document synthesis."
             ],
             border_color=COLOR_PRIMARY, border_width=2.0, title_color=COLOR_PRIMARY,
             model_badge="Cost: $1.25 / 1M Input Tokens | Latency: ~1,100ms", badge_bg=COLOR_PRIMARY_LIGHT, badge_color=COLOR_PRIMARY)

    # Arrow 2: Researcher -> Reviewer
    add_arrow_with_pill(s2, Inches(8.7), Inches(3.40), Inches(9.2), Inches(3.40), label="Audit Draft")

    # Agent 3: Reviewer & QC Gate
    add_card(s2, Inches(9.2), Inches(1.50), Inches(3.3), Inches(4.30),
             title="3. Reviewer & QC Gate (Auditor)",
             subtitle="Gemini 3.5 Flash • Zero Shared Hidden State",
             body_lines=[
                 "Role: Independent clinical evidence auditor and quality gate.",
                 "State Isolation: Operates with ZERO shared reasoning state or prior turns from the Researcher.",
                 "CitationVerifier: Deterministically matches every [1], [2] citation tag to a valid retrieved chunk ID.",
                 "Hallucination Pruning: Any claim lacking explicit 1:1 passage backing is immediately stripped.",
                 "Tone Enforcement: Rewrites any accidentally prescriptive phrasing into objective scientific prose.",
                 "Release Gate: Grants cryptographic release for client SSE streaming."
             ],
             border_color=COLOR_GREEN, border_width=2.0, title_color=COLOR_GREEN,
             model_badge="Cost: $0.15 / 1M Input Tokens | Latency: ~320ms", badge_bg=COLOR_GREEN_LIGHT, badge_color=COLOR_GREEN)

    # Bottom summary box on Slide 2
    box_summary = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.00), Inches(11.733), Inches(0.95))
    box_summary.fill.solid()
    box_summary.fill.fore_color.rgb = COLOR_CARD_BG
    box_summary.line.color.rgb = COLOR_BORDER
    box_summary.line.width = Pt(1)
    tf_s = box_summary.text_frame
    tf_s.word_wrap = True
    tf_s.margin_left = Inches(0.2)
    tf_s.margin_top = Inches(0.1)
    tf_s.margin_right = Inches(0.2)
    
    p_s_t = tf_s.paragraphs[0]
    p_s_t.text = "KEY ARCHITECTURAL ADVANTAGES OF THE SUPERVISOR-WORKER TOPOLOGY"
    p_s_t.font.name = FONT_FAMILY
    p_s_t.font.size = Pt(9.5)
    p_s_t.font.bold = True
    p_s_t.font.color.rgb = COLOR_PRIMARY
    
    p_s_b = tf_s.add_paragraph()
    p_s_b.text = "1. Zero Self-Evaluation Bias: Reviewer has no memory of the Researcher's draft generation, eliminating confirmation bias.  •  2. FinOps Optimization: Blended query cost of $0.0035 (vs $0.018 for monolithic Pro).  •  3. Deterministic Safety: Sub-5ms short-circuit for off-policy queries with zero model token spend."
    p_s_b.font.name = FONT_FAMILY
    p_s_b.font.size = Pt(8.5)
    p_s_b.font.color.rgb = COLOR_TEXT_DARK
    p_s_b.space_before = Pt(3)

    s2.notes_slide.notes_text_frame.text = (
        "Slide 2: Breaks down the Google ADK Supervisor-Worker topology and explains our critical architectural decisions:\n\n"
        "1. In-Process Multi-Agent Topology: All agents run in the same Python process on Cloud Run. This eliminates network hops, reduces latency by 150-300ms per turn, and simplifies state management.\n\n"
        "2. Model Tiering for FinOps: By routing with Gemini 2.5 Flash ($0.075/1M), synthesizing with Gemini 2.5 Pro ($1.25/1M), and auditing with Gemini 3.5 Flash ($0.15/1M), we achieve an average query cost of just $0.0035 compared to $0.018 for a monolithic Pro pipeline.\n\n"
        "3. Zero Self-Evaluation Bias: The Reviewer agent operates with zero shared hidden state from the Researcher, preventing confirmation bias and ensuring strict 1:1 citation proof.\n\n"
        "4. Loop Bound: An immutable max_iterations=2 safety ceiling prevents runaway agent recursion and guarantees bounded execution time."
    )

    output_path = "docs/medquad_architecture_diagram.pptx"
    prs.save(output_path)
    print(f"Generated editable presentation: {output_path} (size: {os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    build_presentation()
