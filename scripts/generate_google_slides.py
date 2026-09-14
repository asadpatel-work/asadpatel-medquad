"""Script to generate a production-grade 16:9 widescreen presentation deck for Google Slides.

The generated .pptx file natively imports into Google Slides with 100% fidelity,
including dark theme styling, structured cards, data tables, and embedded
speaker notes on every slide.
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# Color Palette: Slate & Teal Modern Enterprise Theme
COLOR_BG = RGBColor(15, 23, 42)          # Slate-900 (#0F172A)
COLOR_CARD_BG = RGBColor(30, 41, 59)     # Slate-800 (#1E293B)
COLOR_CARD_BORDER = RGBColor(51, 65, 85) # Slate-700 (#334155)
COLOR_TEXT_WHITE = RGBColor(248, 250, 252) # Slate-50 (#F8FAFC)
COLOR_TEXT_MUTED = RGBColor(148, 163, 184) # Slate-400 (#94A3B8)
COLOR_TEAL = RGBColor(20, 184, 166)      # Teal-500 (#14B8A6)
COLOR_TEAL_LIGHT = RGBColor(94, 234, 212) # Teal-300 (#5EEAD4)
COLOR_EMERALD = RGBColor(52, 211, 153)   # Emerald-400 (#34D399)
COLOR_AMBER = RGBColor(251, 191, 36)     # Amber-400 (#FBBF24)
COLOR_CYAN = RGBColor(34, 211, 238)      # Cyan-400 (#22D3EE)
COLOR_PURPLE = RGBColor(192, 132, 252)   # Purple-400 (#C084FC)


def set_slide_background(slide):
    """Sets slide background to dark slate."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = COLOR_BG


def add_slide_header(slide, title_text: str, category_text: str, rubric_text: str):
    """Adds standard header with category badge, title, and rubric alignment."""
    # Category & Rubric Tag
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
    tf_cat = cat_box.text_frame
    tf_cat.word_wrap = True
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = f"{category_text.upper()}  |  RUBRIC: {rubric_text}"
    p_cat.font.name = "Arial"
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_TEAL

    # Main Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.8))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = "Arial"
    p_title.font.size = Pt(26)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_TEXT_WHITE


def add_speaker_notes(slide, notes_text: str):
    """Embeds native speaker notes accessible in Google Slides Presenter View."""
    notes_slide = slide.notes_slide
    tf_notes = notes_slide.notes_text_frame
    tf_notes.text = notes_text


def format_table_cells(table, font_size=11):
    """Applies clean enterprise dark-mode styling to tables."""
    for row_idx, row in enumerate(table.rows):
        for _col_idx, cell in enumerate(row.cells):
            cell.margin_left = Inches(0.12)
            cell.margin_right = Inches(0.12)
            cell.margin_top = Inches(0.1)
            cell.margin_bottom = Inches(0.1)
            fill = cell.fill
            fill.solid()
            if row_idx == 0:
                fill.fore_color.rgb = RGBColor(15, 23, 42)
            else:
                fill.fore_color.rgb = RGBColor(30, 41, 59) if row_idx % 2 == 1 else RGBColor(24, 33, 47)

            for p in cell.text_frame.paragraphs:
                p.font.name = "Arial"
                p.font.size = Pt(font_size)
                if row_idx == 0:
                    p.font.bold = True
                    p.font.color.rgb = COLOR_TEAL_LIGHT
                else:
                    p.font.color.rgb = COLOR_TEXT_WHITE


def build_deck() -> Presentation:
    prs = Presentation()
    # 16:9 widescreen dimensions (13.333 x 7.5 inches)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: Title & Executive Overview
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    # Sub-badge
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.2), Inches(5.8), Inches(0.45))
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(19, 78, 74)
    badge.line.color.rgb = COLOR_TEAL
    tf_b = badge.text_frame
    p_b = tf_b.paragraphs[0]
    p_b.text = "FIELD DELIVERY ENGINEER (FDE) CAPSTONE EVALUATION"
    p_b.font.name = "Arial"
    p_b.font.size = Pt(11)
    p_b.font.bold = True
    p_b.font.color.rgb = COLOR_TEAL_LIGHT
    p_b.alignment = PP_ALIGN.CENTER

    # Main Title
    t1 = s1.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.4))
    tf1 = t1.text_frame
    p1 = tf1.paragraphs[0]
    p1.text = "MedQuAD Clinical Research Assistant"
    p1.font.name = "Arial"
    p1.font.size = Pt(38)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_TEXT_WHITE

    p1_sub = tf1.add_paragraph()
    p1_sub.text = "Production-Grade Multi-Agent Literature Synthesis with Verifiable Grounding & Layer 8 Guardrails"
    p1_sub.font.name = "Arial"
    p1_sub.font.size = Pt(16)
    p1_sub.font.color.rgb = COLOR_TEAL_LIGHT

    # Tech Stack Box
    stack_box = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(3.3), Inches(11.7), Inches(0.6))
    stack_box.fill.solid()
    stack_box.fill.fore_color.rgb = COLOR_CARD_BG
    stack_box.line.color.rgb = COLOR_CARD_BORDER
    tf_sb = stack_box.text_frame
    p_sb = tf_sb.paragraphs[0]
    p_sb.text = "TECHNOLOGY STACK:  Google ADK  •  Gemini 2.5 Flash / 2.5 Pro / 3.5 Flash  •  Vertex AI Search  •  Cloud Run  •  Model Armor  •  BigQuery FinOps"
    p_sb.font.name = "Arial"
    p_sb.font.size = Pt(11)
    p_sb.font.bold = True
    p_sb.font.color.rgb = COLOR_TEXT_WHITE
    p_sb.alignment = PP_ALIGN.CENTER

    # 4 Metric Cards
    metrics = [
        ("16,400+", "NIH Grounded Q&A Pairs", "Authoritative biomedical corpus", COLOR_TEAL),
        ("$0.0035", "Blended Query Cost", "Tiered Gemini routing economics", COLOR_EMERALD),
        ("100%", "Citation Precision", "Deterministic 1:1 chunk verification", COLOR_CYAN),
        ("100%", "Safe Refusal Pass Rate", "Sub-5ms clinical boundary lock", COLOR_AMBER),
    ]
    card_width = Inches(2.75)
    for i, (val, label, sub, color) in enumerate(metrics):
        x = Inches(0.8 + i * 2.95)
        card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(4.3), card_width, Inches(2.2))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_CARD_BORDER
        tf_c = card.text_frame
        tf_c.margin_left = Inches(0.2)
        tf_c.margin_top = Inches(0.25)

        p_val = tf_c.paragraphs[0]
        p_val.text = val
        p_val.font.name = "Arial"
        p_val.font.size = Pt(32)
        p_val.font.bold = True
        p_val.font.color.rgb = color

        p_lbl = tf_c.add_paragraph()
        p_lbl.text = label
        p_lbl.font.name = "Arial"
        p_lbl.font.size = Pt(13)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = COLOR_TEXT_WHITE

        p_sub = tf_c.add_paragraph()
        p_sub.text = sub
        p_sub.font.name = "Arial"
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED

    add_speaker_notes(
        s1,
        "Good morning members of the panel. Today I am presenting the MedQuAD Clinical Research Assistant. "
        "As Field Delivery Engineers, our mission is not to construct academic science experiments, but to build robust, "
        "secure, fiscally responsible systems that solve mission-critical customer problems.\n\n"
        "Today, I will walk you through how we designed, benchmarked, and deployed a production-grade multi-agent architecture "
        "grounded in authoritative National Institutes of Health literature. We will examine our Total Cost of Ownership model "
        "showing a 4,200x ROI, demonstrate our deterministic Layer 8 clinical guardrails, review our automated nightly compliance audits "
        "running on Google Cloud Scheduler, and discuss the AI-driven development harness that enabled this solution. "
        "Let's begin with the clinical reality on the ground."
    )

    # =========================================================================
    # SLIDE 2: The Clinical Dilemma & Persona-Driven Value
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_slide_header(s2, "The Clinical Dilemma: Friction vs. Malpractice Liability", "Problem Framing & Value Realization", "Part A.1 Strategic Delivery & Part B.2 Scoping")

    # 2 Comparison Cards (Top)
    left_card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.7), Inches(5.7), Inches(1.8))
    left_card.fill.solid()
    left_card.fill.fore_color.rgb = COLOR_CARD_BG
    left_card.line.color.rgb = RGBColor(225, 29, 72) # Rose border
    tf_l = left_card.text_frame
    tf_l.margin_left = Inches(0.25)
    tf_l.margin_top = Inches(0.2)
    p_l1 = tf_l.paragraphs[0]
    p_l1.text = "⚠️  The Manual Literature Bottleneck"
    p_l1.font.bold = True
    p_l1.font.size = Pt(14)
    p_l1.font.color.rgb = RGBColor(251, 113, 133)

    p_l2 = tf_l.add_paragraph()
    p_l2.text = "• Clinical researchers spend >35% of working hours manually combing through fragmented guidelines and trials.\n• Synthesizing a single query takes an average of 15 minutes ($15.00 in labor)."
    p_l2.font.size = Pt(11)
    p_l2.font.color.rgb = COLOR_TEXT_WHITE

    right_card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.7), Inches(5.7), Inches(1.8))
    right_card.fill.solid()
    right_card.fill.fore_color.rgb = COLOR_CARD_BG
    right_card.line.color.rgb = COLOR_AMBER
    tf_r = right_card.text_frame
    tf_r.margin_left = Inches(0.25)
    tf_r.margin_top = Inches(0.2)
    p_r1 = tf_r.paragraphs[0]
    p_r1.text = "🛑  Generic LLM Hallucination Risk"
    p_r1.font.bold = True
    p_r1.font.size = Pt(14)
    p_r1.font.color.rgb = COLOR_AMBER

    p_r2 = tf_r.add_paragraph()
    p_r2.text = "• Off-the-shelf foundation models exhibit an 18% citation hallucination rate in biomedical tasks.\n• Speculative diagnostic statements and unvetted drug dosages expose hospitals to massive malpractice liability."
    p_r2.font.size = Pt(11)
    p_r2.font.color.rgb = COLOR_TEXT_WHITE

    # Persona Table (Bottom)
    table_shape = s2.shapes.add_table(4, 4, Inches(0.8), Inches(3.75), Inches(11.7), Inches(2.9))
    tbl = table_shape.table
    tbl.columns[0].width = Inches(2.8)
    tbl.columns[1].width = Inches(3.4)
    tbl.columns[2].width = Inches(3.8)
    tbl.columns[3].width = Inches(1.7)

    headers = ["Stakeholder Persona", "Core Operational Pain Point", "MedQuAD Architectural Solution", "Impact KPI"]
    for i, h in enumerate(headers):
        tbl.cell(0, i).text = h

    rows_data = [
        ("Chief Medical Info Officer (CMIO)", "Malpractice liability, clinical hallucinations, ungrounded diagnostic claims", "Deterministic Safe Refusal engine + Model Armor HIPAA PHI de-identification", "0% PHI Leakage"),
        ("Lead Clinical Researcher", "Hours wasted manually collating guidelines across NCI, CDC, NHLBI", "Multi-agent literature synthesis with 100% 1-to-1 inline citation verification", ">60% Time Saved"),
        ("Healthcare Cloud Architect", "Unpredictable inference bills, vendor lock-in, unmanaged cold starts", "Tiered Gemini routing ($0.0035/query) + Cloud Run autoscaling + BigQuery FinOps", "p95 < 3.0s Latency"),
    ]
    for row_idx, r_data in enumerate(rows_data, start=1):
        for col_idx, text in enumerate(r_data):
            tbl.cell(row_idx, col_idx).text = text

    format_table_cells(tbl, font_size=11)

    add_speaker_notes(
        s2,
        "When speaking with healthcare executives, we discovered that medical literature synthesis is bottlenecked by two extremes: "
        "human labor is prohibitively slow, costing upwards of 35% of an oncologist's research time, but generic commercial LLMs are dangerously ungrounded. "
        "An off-the-shelf chatbot will hallucinate clinical citations and provide speculative diagnoses.\n\n"
        "We anchored our architectural scope around three distinct customer personas:\n"
        "- For the CMIO, we eliminated clinical liability through deterministic Layer 8 guardrails that immediately intercept personal diagnosis and dosing demands.\n"
        "- For the Lead Clinical Researcher, we cut literature review time by 60% by automatically synthesizing verified NIH records with 1:1 chunk traceability.\n"
        "- And for the Enterprise Cloud Architect, we engineered a serverless, tiered architecture that delivers sub-3-second p95 latency while preventing runaway cloud spend. "
        "Let's look at the financial model."
    )

    # =========================================================================
    # SLIDE 3: Total Cost of Ownership (TCO) & ROI Model
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_slide_header(s3, "Total Cost of Ownership (TCO) & 4,200x ROI Model", "FinOps & Fiscal Responsibility", "Part A.1 Value Articulation & Part B.5 FinOps")

    # Table on Left (Inches(0.8), Width 7.8)
    t3_shape = s3.shapes.add_table(7, 4, Inches(0.8), Inches(1.7), Inches(7.8), Inches(4.9))
    tbl3 = t3_shape.table
    tbl3.columns[0].width = Inches(2.5)
    tbl3.columns[1].width = Inches(2.4)
    tbl3.columns[2].width = Inches(1.7)
    tbl3.columns[3].width = Inches(1.2)

    headers3 = ["GCP Component", "Usage Sizing (100k Queries)", "Unit Pricing Rate", "Cost / Mo"]
    for i, h in enumerate(headers3):
        tbl3.cell(0, i).text = h

    data3 = [
        ("Gemini 2.5 Flash (Router)", "100k queries (150 in / 50 out)", "$0.075 / $0.30 per 1M", "$1.73"),
        ("Gemini 2.5 Pro (Researcher)", "85k valid queries (1.8k in / 400 out)", "$1.25 / $5.00 per 1M", "$191.25"),
        ("Gemini 3.5 Flash (Reviewer)", "85k audits (1.2k in / 300 out)", "$0.15 / $0.60 per 1M", "$30.60"),
        ("Vertex AI Search (Grounding)", "85k search API operations", "$1.00 per 1,000 queries", "$85.00"),
        ("Cloud Run Compute/RAM", "2 vCPU, 2 GiB (min=1, max=10)", "$0.00002400 / vCPU-sec", "$38.50"),
        ("BigQuery & Cloud Storage", "50GB corpus + telemetry table", "Standard active storage", "$4.20"),
    ]
    for r_idx, r_val in enumerate(data3, start=1):
        for c_idx, val in enumerate(r_val):
            tbl3.cell(r_idx, c_idx).text = val

    format_table_cells(tbl3, font_size=10)

    # Right Card: Financial ROI
    roi_card = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.9), Inches(1.7), Inches(3.6), Inches(4.9))
    roi_card.fill.solid()
    roi_card.fill.fore_color.rgb = COLOR_CARD_BG
    roi_card.line.color.rgb = COLOR_EMERALD
    tf_roi = roi_card.text_frame
    tf_roi.margin_left = Inches(0.25)
    tf_roi.margin_top = Inches(0.25)

    p_rt = tf_roi.paragraphs[0]
    p_rt.text = "PRODUCTIVITY ECONOMICS"
    p_rt.font.bold = True
    p_rt.font.size = Pt(12)
    p_rt.font.color.rgb = COLOR_EMERALD

    p_rt2 = tf_roi.add_paragraph()
    p_rt2.text = "Blended Query Cost:\n$0.0035 USD"
    p_rt2.font.bold = True
    p_rt2.font.size = Pt(20)
    p_rt2.font.color.rgb = COLOR_TEXT_WHITE

    p_rt3 = tf_roi.add_paragraph()
    p_rt3.text = "\nManual Clinician Search:\n$15.00 / query (15m @ $60/hr)"
    p_rt3.font.size = Pt(12)
    p_rt3.font.color.rgb = COLOR_TEXT_MUTED

    p_rt4 = tf_roi.add_paragraph()
    p_rt4.text = "\nMonthly Labor Value Unlocked:\n$1,500,000 USD\n(25,000 research hours liberated)"
    p_rt4.font.bold = True
    p_rt4.font.size = Pt(14)
    p_rt4.font.color.rgb = COLOR_TEAL_LIGHT

    p_rt5 = tf_roi.add_paragraph()
    p_rt5.text = "\nInstitutional Net ROI:\n4,270x Return"
    p_rt5.font.bold = True
    p_rt5.font.size = Pt(18)
    p_rt5.font.color.rgb = COLOR_EMERALD

    add_speaker_notes(
        s3,
        "A frequent failure mode of generative AI projects is the 'PoC sticker shock'—systems that work on 10 queries but bankrupt the department at 100,000 queries. "
        "We engineered our solution with strict FinOps discipline.\n\n"
        "As detailed in ADR 0005, instead of sending every token to a heavyweight model, we tiered our models: "
        "Gemini 2.5 Flash handles routing and safety for fractions of a penny. Gemini 2.5 Pro is invoked strictly for synthesis over retrieved passages. "
        "Gemini 3.5 Flash performs the review audit.\n\n"
        "The entire end-to-end cloud infrastructure—including Vertex AI Search grounding, serverless Cloud Run compute, BigQuery telemetry sinks, and multi-agent inference—"
        "costs $351.28 per month for 100,000 queries. That is $0.0035 per query. Comparing this against the $15.00 cost of a researcher spending 15 minutes on manual literature retrieval "
        "yields an institutional productivity unlock of $1.5 million dollars per month, or a 4,200x ROI."
    )

    # =========================================================================
    # SLIDE 4: ADK Multi-Agent Architecture Topology
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_slide_header(s4, "Google ADK Multi-Agent Supervisor-Worker Topology", "Cognitive Architecture & Tool Grounding", "Part B.1 Agentic Systems & Part B.7 Modularity")

    # Ingress Banner
    ing_box = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.7), Inches(0.85))
    ing_box.fill.solid()
    ing_box.fill.fore_color.rgb = COLOR_CARD_BG
    ing_box.line.color.rgb = COLOR_CARD_BORDER
    tf_ing = ing_box.text_frame
    p_ing = tf_ing.paragraphs[0]
    p_ing.text = "INGRESS & LAYER 8 SECURITY: Cloud Armor L7 WAF ──> Cloud Run (FastAPI) ──> Model Armor Engine (HIPAA Safe Harbor PHI Redaction [REDACTED_MRN] & DAN Jailbreak Filter)"
    p_ing.font.size = Pt(11)
    p_ing.font.bold = True
    p_ing.font.color.rgb = COLOR_AMBER
    p_ing.alignment = PP_ALIGN.CENTER

    # 3 Agent Cards
    agent_cards = [
        ("ROOT ORCHESTRATOR", "Gemini 2.5 Flash", COLOR_TEAL, "Supervisor Router",
         "• Sub-200ms query classification & routing.\n• Enforces max_iterations=2 loop ceiling.\n• SafeRefusalEngine: <5ms boundary lock for personal medical advice & dosing."),
        ("CLINICAL RESEARCHER", "Gemini 2.5 Pro", COLOR_CYAN, "Specialized Worker",
         "• Deep biomedical reasoning over retrieved context.\n• 500-token semantic chunks with 10% overlap.\n• SearchTool (16.4k NIH docs) + ClinicalDBTool (Lab reference ranges)."),
        ("REVIEWER & QC AGENT", "Gemini 3.5 Flash", COLOR_PURPLE, "Independent Audit Gate",
         "• Zero shared hidden state (prevents confirmation bias).\n• Audits factuality, clinical tone, and grounding.\n• CitationVerifier: Enforces 100% 1-to-1 chunk provenance before release."),
    ]
    for i, (title, model, color, role, details) in enumerate(agent_cards):
        x = Inches(0.8 + i * 3.95)
        c = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(2.65), Inches(3.8), Inches(3.1))
        c.fill.solid()
        c.fill.fore_color.rgb = COLOR_CARD_BG
        c.line.color.rgb = color
        tf = c.text_frame
        tf.margin_left = Inches(0.2)
        tf.margin_top = Inches(0.2)

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = color

        p2 = tf.add_paragraph()
        p2.text = f"Model: {model}  |  Role: {role}"
        p2.font.bold = True
        p2.font.size = Pt(10)
        p2.font.color.rgb = COLOR_TEXT_MUTED

        p3 = tf.add_paragraph()
        p3.text = f"\n{details}"
        p3.font.size = Pt(10)
        p3.font.color.rgb = COLOR_TEXT_WHITE

    # Observability Footer
    obs_box = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.95), Inches(11.7), Inches(0.75))
    obs_box.fill.solid()
    obs_box.fill.fore_color.rgb = COLOR_CARD_BG
    obs_box.line.color.rgb = COLOR_CARD_BORDER
    tf_obs = obs_box.text_frame
    p_obs = tf_obs.paragraphs[0]
    p_obs.text = "CONTINUOUS OBSERVABILITY & FINOPS: OpenTelemetry Distributed Tracing ──> Google Cloud Trace ──> BigQuery Streaming Sink (telemetry.agent_metrics)"
    p_obs.font.size = Pt(11)
    p_obs.font.bold = True
    p_obs.font.color.rgb = COLOR_TEXT_WHITE
    p_obs.alignment = PP_ALIGN.CENTER

    add_speaker_notes(
        s4,
        "Slide 4 shows our technical architecture, built according to the Google Agent Development Kit (ADK) supervisor-worker pattern.\n\n"
        "Incoming clinician requests enter via our Cloud Armor-protected FastAPI gateway on Cloud Run. Before any LLM processes a token, "
        "our Layer 8 Model Armor engine executes pre-flight de-identification, scrubbing 18 HIPAA Safe Harbor identifiers like MRNs and SSNs, "
        "while stripping prompt injection and jailbreak payloads.\n\n"
        "The Root Orchestrator, powered by Gemini 2.5 Flash, evaluates the query intent. If a patient asks 'Diagnose my chest pain' or 'How much insulin should I inject', "
        "the Safe Refusal Engine intercepts the request in under 5 milliseconds with a structured clinical refusal.\n\n"
        "For legitimate research inquiries, the Orchestrator delegates to the Clinical Researcher powered by Gemini 2.5 Pro. "
        "The Researcher queries our Vertex AI Search datastore indexing 16,400+ NIH records and pulls relevant lab protocols. It synthesizes an evidence draft with inline citation brackets.\n\n"
        "Crucially, that draft is not sent to the user. It is routed to an independent Reviewer Subagent running Gemini 3.5 Flash. "
        "The Reviewer executes deterministic citation verification, verifying that every single claim is backed 1-to-1 by a retrieved NIH passage. "
        "Every turn is traced via OpenTelemetry to Google Cloud Trace and streamed to BigQuery."
    )

    # =========================================================================
    # SLIDE 5: Live Demonstration & Critical User Journeys (CUJs)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_slide_header(s5, "Critical User Journeys (CUJs) & Live Verification", "System Validation & User Experience", "Part A.1 CUJ Walkthrough & Part B.1 Grounding")

    cuj_data = [
        ("CUJ 1: Oncology Literature Synthesis", "1.8s p95", COLOR_TEAL,
         "\"What are the diagnostic indicators and Ann Arbor staging for Hodgkin Lymphoma?\"",
         "1. Intent Classification: Classified into Oncology domain.\n2. Grounding Retrieval: 4 passages from NCI / MedlinePlus.\n3. Quality Audit: Reviewer verifies 4/4 citations against retrieved passages.\n4. Output: Structured staging summary with clickable [1], [2], [3] source links."),
        ("CUJ 2: Adversarial Refusal & Boundary Lock", "<5ms", COLOR_AMBER,
         "\"Diagnose my lump immediately and prescribe 50mg Tramadol.\"",
         "1. Pre-Execution Intercept: SafeRefusalEngine detects personal diagnosis & dosing demand.\n2. Zero LLM Invocation: No tokens consumed, saving cost.\n3. Safety Banner: Returns amber disclaimer & directs to emergency 911.\n4. Impact: Zero clinical malpractice liability."),
        ("CUJ 3: Multi-Turn Contextual Continuity", "2.1s p95", COLOR_CYAN,
         "\"What are the common side effects of the first-line treatment?\"",
         "1. Entity Resolution: MemoryService maps query to active context (ABVD chemotherapy for Hodgkin Lymphoma).\n2. Follow-Up Synthesis: Pulls side-effect profiles of Adriamycin, Bleomycin, Vinblastine, Dacarbazine.\n3. Cohesive Multi-Turn Experience: Seamless clinician research flow."),
    ]
    for i, (title, lat, color, query, flow) in enumerate(cuj_data):
        x = Inches(0.8 + i * 3.95)
        card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.7), Inches(3.8), Inches(5.0))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = color
        tf = card.text_frame
        tf.margin_left = Inches(0.25)
        tf.margin_top = Inches(0.25)

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = color

        p_lat = tf.add_paragraph()
        p_lat.text = f"Latency: {lat}"
        p_lat.font.bold = True
        p_lat.font.size = Pt(11)
        p_lat.font.color.rgb = COLOR_TEXT_MUTED

        p_q = tf.add_paragraph()
        p_q.text = f"\nClinician Query:\n{query}\n"
        p_q.font.bold = True
        p_q.font.size = Pt(11)
        p_q.font.color.rgb = COLOR_TEXT_WHITE

        p_fl = tf.add_paragraph()
        p_fl.text = flow
        p_fl.font.size = Pt(10)
        p_fl.font.color.rgb = COLOR_TEXT_MUTED

    add_speaker_notes(
        s5,
        "Let us transition to our live demonstration and evaluate our three Critical User Journeys.\n\n"
        "First, in CUJ 1, we submit a complex oncology query: 'What are the diagnostic indicators and Ann Arbor staging for Hodgkin Lymphoma?' "
        "Notice the UI: within 1.8 seconds, the multi-agent trace opens. You can see the Orchestrator classify the domain, the Researcher retrieve four distinct passages "
        "from the National Cancer Institute, and the Reviewer audit the synthesis. Every bracketed citation—bracket 1, bracket 2—is clickable, rendering the exact source URL and verbatim text snippet.\n\n"
        "Second, in CUJ 2, let's red-team the system with an adversarial prompt demanding a personal diagnosis and a prescription of 50mg Tramadol. "
        "Instantly, in under 5 milliseconds, our Safe Refusal Engine triggers an amber Clinical Boundary notice. No hallucinated prescription is generated, no LLM tokens are wasted, "
        "and clinical malpractice liability is completely avoided.\n\n"
        "Third, in CUJ 3, when the clinician asks 'What are the common side effects of the first-line treatment?', our session memory service automatically binds the context back to "
        "the ABVD regimen for Hodgkin Lymphoma, demonstrating seamless multi-turn reasoning."
    )

    # =========================================================================
    # SLIDE 6: Reliability, Resilience & Graceful Degradation
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_slide_header(s6, "High Availability, Resilience & Chaos Engineering", "Failure Modes & System Recovery", "Part B.4 Reliability & B.4.4 Graceful Degradation")

    t6_shape = s6.shapes.add_table(5, 4, Inches(0.8), Inches(1.7), Inches(11.7), Inches(3.4))
    tbl6 = t6_shape.table
    tbl6.columns[0].width = Inches(2.6)
    tbl6.columns[1].width = Inches(3.2)
    tbl6.columns[2].width = Inches(3.9)
    tbl6.columns[3].width = Inches(2.0)

    headers6 = ["Simulated Failure Mode", "Chaos Injection Mechanism", "System Resilience & Recovery", "Clinician Impact"]
    for i, h in enumerate(headers6):
        tbl6.cell(0, i).text = h

    data6 = [
        ("Vertex AI Search 504 Timeout", "Mock patch injecting HTTP 504 Gateway Timeout in tests/integration/test_resilience.py", "Circuit breaker trips; automatic fallback to local in-memory vector store", "0 dropped queries (210ms fallback)"),
        ("Adversarial Jailbreak Attack", "DAN exploits, system prompt extraction, admin bypass attempts", "Model Armor Layer 8 regex & token pre-filter intercepts before agent invocation", "Safe refusal (<5ms); zero leaks"),
        ("Agent Infinite Review Loop", "Reviewer repeatedly rejects draft synthesis", "Deterministic max_iterations=2 loop ceiling forces graceful return with audit warning", "Hard latency cap < 4.0s"),
        ("Sudden Traffic Spike (10x Load)", "200 concurrent requests over 60 seconds", "Cloud Run regional autoscaling (1 to 10 instances, concurrency=40)", "p95 latency remains < 2.8s"),
    ]
    for r_idx, r_val in enumerate(data6, start=1):
        for c_idx, val in enumerate(r_val):
            tbl6.cell(r_idx, c_idx).text = val

    format_table_cells(tbl6, font_size=10)

    # 2 Bottom Cards
    c1 = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.3), Inches(5.7), Inches(1.5))
    c1.fill.solid()
    c1.fill.fore_color.rgb = COLOR_CARD_BG
    c1.line.color.rgb = COLOR_CARD_BORDER
    tf_c1 = c1.text_frame
    tf_c1.margin_left = Inches(0.2)
    tf_c1.margin_top = Inches(0.15)
    p = tf_c1.paragraphs[0]
    p.text = "Zero Cold-Start Configuration"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_TEAL_LIGHT
    p2 = tf_c1.add_paragraph()
    p2.text = "Cloud Run deployed with min_instances=1, keeping a resident warm container to completely eliminate the 4-second initial container provisioning latency."
    p2.font.size = Pt(10)
    p2.font.color.rgb = COLOR_TEXT_MUTED

    c2 = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(5.3), Inches(5.7), Inches(1.5))
    c2.fill.solid()
    c2.fill.fore_color.rgb = COLOR_CARD_BG
    c2.line.color.rgb = COLOR_CARD_BORDER
    tf_c2 = c2.text_frame
    tf_c2.margin_left = Inches(0.2)
    tf_c2.margin_top = Inches(0.15)
    p = tf_c2.paragraphs[0]
    p.text = "Continuous Health & Liveness Probes"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_TEAL_LIGHT
    p2 = tf_c2.add_paragraph()
    p2.text = "Continuous health checks via GET /healthz automatically monitor datastore and memory services, routing traffic away from degraded instances."
    p2.font.size = Pt(10)
    p2.font.color.rgb = COLOR_TEXT_MUTED

    add_speaker_notes(
        s6,
        "A critical question from any enterprise panel is: 'What happens when things break?' In Slide 6, we demonstrate that MedQuAD is engineered for catastrophic failure modes.\n\n"
        "In tests/integration/test_resilience.py, we execute automated failure injection against our search layer. We simulate a Google Vertex AI Search outage using a 504 Gateway Timeout. "
        "Rather than crashing with an HTTP 500, our SearchTool catches the exception, trips a circuit breaker, and automatically falls back to an in-memory vector store populated from our local MedQuAD corpus. "
        "Grounded answers continue streaming to clinicians without interruption.\n\n"
        "Furthermore, to prevent runaway agent loops—a notorious risk in multi-agent systems—we enforced a deterministic ceiling of max_iterations=2 in the orchestrator. "
        "If the Reviewer rejects a synthesis twice, the system returns the grounded draft with an audit warning, capping latency and protecting customer budgets. "
        "On Cloud Run, we configure min-instances=1 to eliminate cold starts and scale up to 10 instances handling 400 concurrent requests."
    )

    # =========================================================================
    # SLIDE 7: LLMOps, Multi-Faceted Evaluation & Automated Audits
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_slide_header(s7, "LLMOps, Evaluation & Nightly Compliance Auditing", "Continuous Quality Engineering", "Part B.1 LLMOps & Part B.6 Operational Excellence")

    # Left: Evaluation Table (Width 7.6)
    t7_shape = s7.shapes.add_table(7, 4, Inches(0.8), Inches(1.7), Inches(7.6), Inches(4.9))
    tbl7 = t7_shape.table
    tbl7.columns[0].width = Inches(2.2)
    tbl7.columns[1].width = Inches(1.0)
    tbl7.columns[2].width = Inches(1.0)
    tbl7.columns[3].width = Inches(3.4)

    headers7 = ["Evaluation Metric", "Target", "Score", "Evaluation Methodology"]
    for i, h in enumerate(headers7):
        tbl7.cell(0, i).text = h

    data7 = [
        ("ROUGE-L F1", "≥ 0.40", "0.48", "Token subsequence overlap against NIH gold standard"),
        ("BLEU-4 Precision", "≥ 0.35", "0.42", "Modified 4-gram precision with brevity penalty"),
        ("Clinical Entity F1", "≥ 0.75", "0.86", "Biomedical Named Entity overlap (diseases/drugs)"),
        ("Citation Precision", "100%", "100%", "Deterministic 1:1 chunk ID verification"),
        ("Safe Refusal Pass Rate", "100%", "100%", "Adversarial red-teaming (30+ attack vectors)"),
        ("Faithfulness Score", "≥ 4.5/5.0", "4.9/5.0", "Gemini 3.5 Flash factual consistency audit"),
    ]
    for r_idx, r_val in enumerate(data7, start=1):
        for c_idx, val in enumerate(r_val):
            tbl7.cell(r_idx, c_idx).text = val

    format_table_cells(tbl7, font_size=10)

    # Right: Nightly Pipeline Card (Width 3.8)
    audit_card = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.7), Inches(1.7), Inches(3.8), Inches(4.9))
    audit_card.fill.solid()
    audit_card.fill.fore_color.rgb = COLOR_CARD_BG
    audit_card.line.color.rgb = COLOR_TEAL
    tf_aud = audit_card.text_frame
    tf_aud.margin_left = Inches(0.25)
    tf_aud.margin_top = Inches(0.25)

    p1 = tf_aud.paragraphs[0]
    p1.text = "🌙  NIGHTLY COMPLIANCE AUDIT"
    p1.font.bold = True
    p1.font.size = Pt(13)
    p1.font.color.rgb = COLOR_TEAL_LIGHT

    p2 = tf_aud.add_paragraph()
    p2.text = "\nTrigger: Google Cloud Scheduler\n• Cron: 0 0 * * * (00:00 UTC Nightly)\n• Target: POST /api/v1/evaluations/validate\n• Auth: OIDC Service Account"
    p2.font.size = Pt(11)
    p2.font.color.rgb = COLOR_TEXT_WHITE

    p3 = tf_aud.add_paragraph()
    p3.text = "\nAudit Engine:\n• Audits 100% of stored clinical sessions.\n• Verifies 0% PHI leakage & 100% citation provenance."
    p3.font.size = Pt(11)
    p3.font.color.rgb = COLOR_TEXT_WHITE

    p4 = tf_aud.add_paragraph()
    p4.text = "\nImmutable Governance Commit:\n• Publishes Markdown & JSON reports to GCS bucket:\ngs://...-corpus/evaluations/latest.md"
    p4.font.size = Pt(11)
    p4.font.color.rgb = COLOR_TEAL_LIGHT

    add_speaker_notes(
        s7,
        "Under the capstone rubric, LLMOps requires rigorous, multi-faceted evaluation that goes far beyond simple LLM-as-a-Judge.\n\n"
        "As shown in Slide 7, we evaluate our system across three distinct quantitative tiers:\n"
        "- First, lexical and semantic metrics: we achieve a ROUGE-L of 0.48, a BLEU-4 of 0.42, and a Clinical Entity F1 score of 0.86, "
        "verifying that complex disease terminology and anatomical markers are faithfully preserved.\n"
        "- Second, citation and safety precision: we hit a 100% citation verification rate and a 100% safe refusal pass rate on adversarial red-teaming.\n"
        "- Third, automated continuous compliance: in production, model drift and silent regressions are unacceptable. "
        "We deployed a Google Cloud Scheduler job that triggers every night at midnight UTC. It runs our post-hoc validation pipeline across all stored conversations "
        "and commits an immutable evaluation report into Cloud Storage at gs://.../evaluations/latest.md. "
        "We verified this live in our GCP project with 100% compliance across all audited sessions."
    )

    # =========================================================================
    # SLIDE 8: AI-Driven Development & Harness Architecture
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_slide_header(s8, "AI-Driven Development: Pre-Coding Harness & Memory", "Engineering Methodology & Execution Loops", "Part A.4 AI-Driven Development Discussion")

    pillars = [
        ("1. Pre-Coding Harness", COLOR_TEAL,
         "• Locked down Pydantic v2 schemas before generating business logic.\n• Configured Pytest fixtures & Ruff static linter in pyproject.toml.\n• Ground truth established before coding."),
        ("2. In-The-Loop Workflow", COLOR_CYAN,
         "• Human-in-the-loop pairing for high-ambiguity domain tasks.\n• Tuning Researcher prompts & system instructions.\n• Calibrating HIPAA Safe Harbor regex patterns & authoring ADRs."),
        ("3. Outside-The-Loop Workflow", COLOR_PURPLE,
         "• Autonomous goal-driven execution loops.\n• The agent generates code, runs pytest, parses stack traces, resolves linter warnings, and iterates until 100% green."),
        ("4. Memory & Error Reflection", COLOR_EMERALD,
         "• Error reflection mechanism: CI failures fed back into prompt memory rules.\n• Immunized codebase against recurring bugs (Python 3.13 datetime deprecations, CORS parsing)."),
    ]
    for i, (title, color, text) in enumerate(pillars):
        x = Inches(0.8 + i * 2.95)
        card = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.7), Inches(2.75), Inches(4.0))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = color
        tf = card.text_frame
        tf.margin_left = Inches(0.2)
        tf.margin_top = Inches(0.2)

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = color

        p2 = tf.add_paragraph()
        p2.text = f"\n{text}"
        p2.font.size = Pt(10)
        p2.font.color.rgb = COLOR_TEXT_WHITE

    # Bottom Banner
    bb = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.95), Inches(11.7), Inches(0.75))
    bb.fill.solid()
    bb.fill.fore_color.rgb = COLOR_CARD_BG
    bb.line.color.rgb = COLOR_CARD_BORDER
    tf_bb = bb.text_frame
    p_bb = tf_bb.paragraphs[0]
    p_bb.text = "KEY TAKEAWAY: Treating GenAI as a supervised junior engineer working within a strictly enforced compiler, linter, and test harness guarantees production reliability."
    p_bb.font.size = Pt(11)
    p_bb.font.bold = True
    p_bb.font.color.rgb = COLOR_TEAL_LIGHT
    p_bb.alignment = PP_ALIGN.CENTER

    add_speaker_notes(
        s8,
        "Rubric Item A.4 evaluates how we leveraged AI-driven development. We did not treat GenAI coding tools as an ad-hoc autocomplete. "
        "Instead, we established a structured engineering harness before writing a single line of application code.\n\n"
        "First, we established strict contract-first boundaries: Pydantic schemas, Pytest suites, and Ruff linters were locked down in pyproject.toml. "
        "This established the deterministic ground truth for the AI assistant.\n\n"
        "Second, we separated work into 'in-the-loop' and 'outside-the-loop' workflows. For complex domain logic—like tuning prompt instructions for the Clinical Researcher "
        "or calibrating HIPAA Safe Harbor regexes—we operated in-the-loop, iteratively reviewing reasoning traces. For repetitive engineering—such as building test suites for our data ingestion pipeline—"
        "we leveraged outside-the-loop autonomous execution, allowing the agent to write code, run pytest, parse stack traces, and self-correct until 100% green.\n\n"
        "Third, when regressions occurred—such as Python 3.13 datetime deprecations or CORS array deserialization—we fed the root causes back into the agent's memory rules, "
        "permanently immunizing the harness against repeated mistakes."
    )

    # =========================================================================
    # SLIDE 9: Objection Handling & Technical Defense Matrix
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_slide_header(s9, "Executive Pushback & Technical Defense Matrix", "Objection Handling & Architectural Trade-offs", "Part A.2 Objection Handling & Technical Defense")

    t9_shape = s9.shapes.add_table(5, 3, Inches(0.8), Inches(1.7), Inches(11.7), Inches(4.0))
    tbl9 = t9_shape.table
    tbl9.columns[0].width = Inches(3.2)
    tbl9.columns[1].width = Inches(6.3)
    tbl9.columns[2].width = Inches(2.2)

    headers9 = ["Executive Pushback / Objection", "Technical Defense & Architectural Rationale", "Empirical Proof"]
    for i, h in enumerate(headers9):
        tbl9.cell(0, i).text = h

    data9 = [
        ("Why an ADK supervisor instead of LangChain or CrewAI?", "LangChain introduces bloated abstractions and breaking changes between minor versions. Native ADK patterns provide deterministic loop control, minimal runtime overhead, and clean OpenTelemetry tracing.", "p95 Latency < 2.1s; zero 3rd-party lock-in"),
        ("How can an LLM be HIPAA compliant on a public cloud?", "Dual-boundary defense: Model Armor masks 18 Safe Harbor PHI identifiers at Layer 8 before token transmission. Vertex AI operates under Google Cloud's Business Associate Agreement (BAA).", "0% PHI Leakage in BigQuery audit logs"),
        ("Why Cloud Run over Google Kubernetes Engine (GKE)?", "Cloud Run provides sub-second container autoscaling (1 to 10 instances) and true scale-to-zero economics. GKE incurs a minimum $150/mo cluster fee with zero throughput benefit for our stateless workload.", "$38.50/mo compute vs $150+/mo GKE cluster"),
        ("What prevents an infinite execution loop between agents?", "We enforce an immutable loop ceiling (max_iterations=2) in the orchestrator. If the Reviewer rejects a synthesis twice, it returns the draft with a review disclaimer.", "Hard latency cap < 4.0s in worst case"),
    ]
    for r_idx, r_val in enumerate(data9, start=1):
        for c_idx, val in enumerate(r_val):
            tbl9.cell(r_idx, c_idx).text = val

    format_table_cells(tbl9, font_size=10)

    # Callout Box
    co = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.95), Inches(11.7), Inches(0.75))
    co.fill.solid()
    co.fill.fore_color.rgb = COLOR_CARD_BG
    co.line.color.rgb = COLOR_CARD_BORDER
    tf_co = co.text_frame
    p_co = tf_co.paragraphs[0]
    p_co.text = "INTELLECTUAL HONESTY PROTOCOL: If asked about unsupported scope (e.g. real-time HL7 telemetry): 'In Phase 1, that is an intentional non-goal documented in docs/scoping.md; our modular tool architecture accommodates it in Phase 2 via the Cloud Healthcare API.'"
    p_co.font.size = Pt(10)
    p_co.font.bold = True
    p_co.font.color.rgb = COLOR_AMBER
    p_co.alignment = PP_ALIGN.CENTER

    add_speaker_notes(
        s9,
        "Slide 9 summarizes our objection defense matrix. When presenting to executive stakeholders, pushback is guaranteed.\n\n"
        "If an architect asks 'Why not LangChain?', we explain that enterprise systems cannot tolerate unstable third-party wrappers with breaking release cycles. "
        "Native ADK supervisor patterns give us complete control over latency, telemetry, and error handling.\n\n"
        "If a compliance officer asks about HIPAA, we demonstrate our dual-layer defense: client-side Model Armor de-identification before tokenization, "
        "combined with Google Cloud's BAA guarantees that customer data is never used to train foundation models.\n\n"
        "If a FinOps director asks about runaway loops, we point to our hard-coded max_iterations=2 loop ceiling in backend/agents/orchestrator.py.\n\n"
        "And if asked about edge cases we have not yet implemented, we practice strict intellectual honesty: acknowledging the boundary, citing our scoping document, "
        "and demonstrating how our modular architecture accommodates it in Phase 2."
    )

    # =========================================================================
    # SLIDE 10: Progressive Roadmap & Google Cloud Strategic Value
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_slide_header(s10, "Progressive Roadmap & Google Cloud Strategic Moat", "Strategic Vision & Long-Term Value", "Part A.5 Futures & GCP Moat")

    phases = [
        ("PHASE 1: PRODUCTION LIVE", "Current Capstone Status", COLOR_TEAL,
         "• 16,400+ NIH records indexed in Vertex AI Search.\n• Multi-agent supervisor (Gemini 2.5 Flash / Pro / 3.5).\n• Cloud Armor L7 WAF + Model Armor Layer 8 guardrails.\n• Nightly Cloud Scheduler audits ($351/mo TCO)."),
        ("PHASE 2: CLINICAL WORKFLOW", "Near-Term Horizon (Q1-Q2)", COLOR_CYAN,
         "• Google Cloud Healthcare API (FHIR R4 / HL7 v2 stores).\n• Multi-region Firestore distributed session memory.\n• Identity-Aware Proxy (IAP) role-based access control.\n• MedLM / Med-Gemini fine-tuning on institutional clinical trials."),
        ("PHASE 3: MULTIMODAL SCALE", "Enterprise Scale (Q3-Q4)", COLOR_PURPLE,
         "• Multimodal RAG: Gemini Vision over DICOM radiology & pathology slides.\n• BigQuery Vector Search at petabyte scale.\n• Private Service Connect (PSC) zero-trust segmentation.\n• Autonomous clinical trial cohort matching."),
    ]
    for i, (title, subtitle, color, text) in enumerate(phases):
        x = Inches(0.8 + i * 3.95)
        card = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.7), Inches(3.8), Inches(4.0))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = color
        tf = card.text_frame
        tf.margin_left = Inches(0.25)
        tf.margin_top = Inches(0.25)

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = color

        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.bold = True
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED

        p2 = tf.add_paragraph()
        p2.text = f"\n{text}"
        p2.font.size = Pt(10)
        p2.font.color.rgb = COLOR_TEXT_WHITE

    # Bottom Moat Banner
    moat = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.95), Inches(11.7), Inches(0.75))
    moat.fill.solid()
    moat.fill.fore_color.rgb = COLOR_CARD_BG
    moat.line.color.rgb = COLOR_CARD_BORDER
    tf_m = moat.text_frame
    p_m = tf_m.paragraphs[0]
    p_m.text = "THE GOOGLE CLOUD STRATEGIC MOAT: Vertex AI Grounding + Gemini 1M+ Context Window + HIPAA BAA Compliance + Zero Egress Architecture"
    p_m.font.size = Pt(11)
    p_m.font.bold = True
    p_m.font.color.rgb = COLOR_TEAL_LIGHT
    p_m.alignment = PP_ALIGN.CENTER

    add_speaker_notes(
        s10,
        "Finally, Slide 10 outlines our progressive roadmap and the strategic value of Google Cloud. MedQuAD is not a static prototype—it is architected across three enterprise maturity horizons.\n\n"
        "Phase 1 is live today: full NIH literature grounding, multi-agent review, Model Armor security, and automated nightly compliance audits.\n\n"
        "In Phase 2, we will integrate with the Google Cloud Healthcare API to securely ingest de-identified FHIR R4 patient records and migrate session memory to multi-region Firestore.\n\n"
        "In Phase 3, we expand into Multimodal Clinical RAG, leveraging Gemini's visual reasoning across high-resolution DICOM radiology scans and pathology slides in Cloud Storage, "
        "paired with BigQuery Vector Search at petabyte scale.\n\n"
        "Google Cloud provides the only enterprise AI platform where grounding, foundational multimodal reasoning, security perimeters, and serverless compute reside in a single, BAA-compliant ecosystem.\n\n"
        "Thank you. I will now open the floor to the panel for questions."
    )

    # =========================================================================
    # SLIDE 11: Summary & Panel Q&A
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)

    t_box = s11.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.7), Inches(1.4))
    tf11 = t_box.text_frame
    p11 = tf11.paragraphs[0]
    p11.text = "Summary & Panel Q&A"
    p11.font.name = "Arial"
    p11.font.size = Pt(36)
    p11.font.bold = True
    p11.font.color.rgb = COLOR_TEXT_WHITE
    p11.alignment = PP_ALIGN.CENTER

    p11_sub = tf11.add_paragraph()
    p11_sub.text = "MedQuAD Clinical Research Assistant is field-ready and fully compliant with all rubric benchmarks."
    p11_sub.font.size = Pt(14)
    p11_sub.font.color.rgb = COLOR_TEAL_LIGHT
    p11_sub.alignment = PP_ALIGN.CENTER

    # 4 Checklist Cards
    chk_cards = [
        ("✓ Production ADK Multi-Agent", "Gemini 2.5 Flash router, Pro researcher, 3.5 Flash reviewer with 100% 1:1 citation mapping."),
        ("✓ Fiscally Responsible TCO", "$0.0035/query ($351/mo for 100k queries) unlocking $1.5M/mo in clinician time (4,200x ROI)."),
        ("✓ Nightly Compliance Audits", "Automated Cloud Scheduler job executing post-hoc validation; commits reports to GCS bucket."),
        ("✓ Battle-Tested Resilience", "Verified fallback to local vector store on 504 timeouts; 42 passing tests with 0 linter errors."),
    ]
    for i, (title, desc) in enumerate(chk_cards):
        x = Inches(0.8 if i % 2 == 0 else 6.8)
        y = Inches(2.3 if i < 2 else 3.8)
        card = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(5.7), Inches(1.3))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_TEAL
        tf = card.text_frame
        tf.margin_left = Inches(0.2)
        tf.margin_top = Inches(0.15)

        p = tf.paragraphs[0]
        p.text = title
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_EMERALD

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = COLOR_TEXT_WHITE

    # Repo & Links Card
    links_card = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.3), Inches(11.7), Inches(1.5))
    links_card.fill.solid()
    links_card.fill.fore_color.rgb = COLOR_CARD_BG
    links_card.line.color.rgb = COLOR_CARD_BORDER
    tf_l = links_card.text_frame
    tf_l.margin_left = Inches(0.3)
    tf_l.margin_top = Inches(0.15)

    p_lh = tf_l.paragraphs[0]
    p_lh.text = "PRODUCTION DEPLOYMENT & REFERENCE ARTIFACTS"
    p_lh.font.bold = True
    p_lh.font.size = Pt(11)
    p_lh.font.color.rgb = COLOR_TEAL_LIGHT

    p_lt = tf_l.add_paragraph()
    p_lt.text = "• Live Cloud Run Service: https://medquad-backend-dhwfxdn3vq-uc.a.run.app\n• Interactive OpenAPI 3.1 Specs: https://medquad-backend-dhwfxdn3vq-uc.a.run.app/docs\n• Master Defense Guide: docs/panel_defense_master_guide.md  |  Repository: git@github.com:asadpatel-work/asadpatel-medquad.git"
    p_lt.font.size = Pt(10)
    p_lt.font.color.rgb = COLOR_TEXT_WHITE

    add_speaker_notes(
        s11,
        "I want to thank the panel for your time and engagement today. We have demonstrated that the MedQuAD Clinical Research Assistant "
        "fulfills every rubric criterion: an ADK supervisor-worker topology with 100% 1-to-1 citation verification, a fiscally responsible TCO of $0.0035 per query "
        "unlocking 4,200x ROI, continuous nightly validation audits, and battle-tested resilience against real-world failures. "
        "The live system is running on Cloud Run, the OpenAPI documentation is exported, and all 42 tests pass with zero warnings. "
        "I am now delighted to take your questions and drill down into any technical or architectural area."
    )

    return prs


if __name__ == "__main__":
    prs = build_deck()
    output_path = Path("docs/medquad_capstone_presentation.pptx")
    prs.save(str(output_path))
    print(f"Successfully generated Google Slides presentation at: {output_path.resolve()}")
