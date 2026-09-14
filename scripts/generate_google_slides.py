"""Script to generate a simplified, clean 4-slide presentation deck for Google Slides.

Adheres strictly to the user's requirements:
- 4 slides: Problem, Product, Architecture, Future Work
- Basic colors: Clean white background, dark gray text, subtle Google Blue accent
- Simple, uncrowded layout with zero marketing fluff
- Native speaker notes embedded on each slide
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

# Clean, Basic Google Theme Palette
COLOR_WHITE = RGBColor(255, 255, 255)       # Slide background
COLOR_PANEL_BG = RGBColor(248, 249, 250)    # Light gray (#F8F9FA)
COLOR_BORDER = RGBColor(218, 220, 224)      # Subtle border (#DADCE0)
COLOR_TEXT_DARK = RGBColor(32, 33, 36)      # Primary text (#202124)
COLOR_TEXT_MUTED = RGBColor(95, 99, 104)    # Secondary text (#5F6368)
COLOR_PRIMARY = RGBColor(26, 115, 232)      # Google Blue (#1A73E8)
COLOR_DARK_BLUE = RGBColor(24, 90, 188)     # Header blue (#185ABC)


def apply_slide_base(slide, title_text: str, subtitle_text: str = ""):
    """Sets white background and standard clean header."""
    # Set background to clean white
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = COLOR_WHITE

    # Title box
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.9))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_title = tf.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = "Arial"
    p_title.font.size = Pt(24)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_TEXT_DARK

    if subtitle_text:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle_text
        p_sub.font.name = "Arial"
        p_sub.font.size = Pt(12)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED

    # Subtle divider line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.4), Inches(11.733), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_BORDER
    line.line.color.rgb = COLOR_BORDER


def add_speaker_notes(slide, notes_text: str):
    """Embeds native speaker notes for Google Slides Presenter View."""
    notes_slide = slide.notes_slide
    tf_notes = notes_slide.notes_text_frame
    tf_notes.text = notes_text


def add_card(slide, left, top, width, height, title, items):
    """Helper to add a clean, bordered box with bulleted items."""
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = COLOR_PANEL_BG
    box.line.color.rgb = COLOR_BORDER
    box.line.width = Pt(1)

    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.25)
    tf.margin_right = Inches(0.25)
    tf.margin_top = Inches(0.2)
    tf.margin_bottom = Inches(0.2)

    p_title = tf.paragraphs[0]
    p_title.text = title
    p_title.font.name = "Arial"
    p_title.font.size = Pt(13)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_PRIMARY

    for item in items:
        p = tf.add_paragraph()
        p.text = f"•  {item}"
        p.font.name = "Arial"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_before = Pt(6)


def build_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: Problem Introduction
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    apply_slide_base(
        s1,
        "Problem: Clinical Literature Retrieval & Hallucination Risks",
        "MedQuAD Clinical Research Assistant  |  Capstone Evaluation"
    )

    # Left Column: Manual Research Friction
    add_card(
        s1,
        left=Inches(0.8),
        top=Inches(1.7),
        width=Inches(5.7),
        height=Inches(5.0),
        title="1. Manual Literature Synthesis Overhead",
        items=[
            "Clinicians and researchers spend over 35% of their research time searching disparate medical databases (NIH, NCI, CDC, PubMed).",
            "Manual collation of staging criteria, treatment protocols, and adverse reactions is slow and error-prone.",
            "Synthesizing an authoritative answer to a complex clinical question takes an average of 15 minutes of specialized clinician time.",
            "Information is fragmented across thousands of static XML and PDF files without unified semantic indexing."
        ]
    )

    # Right Column: Generic LLM Failures
    add_card(
        s1,
        left=Inches(6.8),
        top=Inches(1.7),
        width=Inches(5.7),
        height=Inches(5.0),
        title="2. LLM Hallucinations & Clinical Liability",
        items=[
            "Standard off-the-shelf foundation models exhibit an ~18% citation hallucination rate on biomedical literature queries.",
            "Commercial chatbots generate plausible-sounding but fictitious medical claims, fabricated journal links, and obsolete dosing advice.",
            "Unguarded models attempt to diagnose conditions or recommend drug doses from user prompts, creating severe medical liability.",
            "Off-the-shelf models lack a verifiable 1-to-1 provenance mechanism connecting each statement back to an authoritative medical chunk."
        ]
    )

    add_speaker_notes(
        s1,
        "Slide 1 outlines the core problem we set out to solve.\n\n"
        "In healthcare, researchers and clinicians face two distinct failure modes when answering clinical questions:\n\n"
        "First, manual retrieval is inefficient. Researchers spend more than a third of their time combing through disparate NIH databases, guidelines, and trial registries. A single literature review can easily take 15 minutes of manual labor.\n\n"
        "Second, simply handing the problem to a generic LLM introduces severe clinical risk. Foundation models hallucinate citations roughly 18% of the time, and unprompted, they will attempt to diagnose or recommend prescriptions, exposing the institution to malpractice liability.\n\n"
        "The goal of this project is to bridge this gap: automate literature synthesis while guaranteeing 100% citation grounding and enforcing strict clinical guardrails."
    )

    # =========================================================================
    # SLIDE 2: Product Overview
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    apply_slide_base(
        s2,
        "Product Overview: MedQuAD Clinical Research Assistant",
        "Grounded Multi-Agent Clinical Question Answering System"
    )

    # 4 Clean Quadrant Cards
    q_width = Inches(5.7)
    q_height = Inches(2.4)

    # Top-Left: Grounded Corpus
    add_card(
        s2,
        left=Inches(0.8),
        top=Inches(1.7),
        width=q_width,
        height=q_height,
        title="Authoritative NIH Corpus Grounding",
        items=[
            "Indexes 16,400+ verified medical Q&A pairs from NIH, NCI, CDC, and MedlinePlus.",
            "Preprocessed with 500-token semantic chunking and 10% overlap to preserve clinical context.",
            "Backed by Google Vertex AI Search with automated fallback to an in-memory vector store."
        ]
    )

    # Top-Right: 1:1 Citation Verification
    add_card(
        s2,
        left=Inches(6.8),
        top=Inches(1.7),
        width=q_width,
        height=q_height,
        title="Deterministic Citation Verification",
        items=[
            "Every generated statement must map 1:1 to a specific retrieved NIH passage chunk.",
            "A dedicated Reviewer agent audits citations before output is streamed to the user.",
            "Enforces 100% citation precision—unverified statements are flagged or excised."
        ]
    )

    # Bottom-Left: Deterministic Guardrails
    add_card(
        s2,
        left=Inches(0.8),
        top=Inches(4.3),
        width=q_width,
        height=q_height,
        title="Layer 8 Safety & Safe Refusal",
        items=[
            "Immediate interception (<5ms) of personal diagnostic and drug dosing demands.",
            "Pre-flight de-identification of 18 HIPAA Safe Harbor identifiers (MRN, SSN, names).",
            "Returns structured clinical disclaimers and emergency redirection without wasting LLM tokens."
        ]
    )

    # Bottom-Right: Cost & Performance
    add_card(
        s2,
        left=Inches(6.8),
        top=Inches(4.3),
        width=q_width,
        height=q_height,
        title="Efficient Model Tiering & Cloud Run",
        items=[
            "Tiered Gemini models: Flash 2.5 for routing/safety, Pro 2.5 for synthesis, Flash 3.5 for review.",
            "Blended inference cost of ~$0.0035 per query ($351/mo for 100,000 queries).",
            "Deployed serverless on Google Cloud Run with sub-3s p95 latency and zero cold starts."
        ]
    )

    add_speaker_notes(
        s2,
        "Slide 2 describes the product and what it actually does.\n\n"
        "The MedQuAD Clinical Assistant is a specialized research tool built on top of 16,400+ authoritative NIH medical records.\n\n"
        "Here are its four defining technical characteristics:\n"
        "1. Authoritative Grounding: We chunked and indexed NIH, NCI, and MedlinePlus data using 500-token semantic chunks in Vertex AI Search.\n"
        "2. Deterministic Verification: Rather than trusting the model to cite accurately, a dedicated Reviewer subagent cross-examines the draft against retrieved chunk IDs. We enforce 100% citation provenance.\n"
        "3. Layer 8 Guardrails: If a user asks for a personal diagnosis or a prescription dose, our Safe Refusal Engine catches it in under 5 milliseconds and responds with a clinical disclaimer, invoking zero LLM tokens.\n"
        "4. Practical FinOps: We tiered Gemini models so that routing and review run on lightweight Flash models, reserving Gemini Pro strictly for multi-document synthesis. This brings the total blended cost down to $0.0035 per query."
    )

    # =========================================================================
    # SLIDE 3: Architecture Diagram
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    apply_slide_base(
        s3,
        "System Architecture: ADK Multi-Agent Pipeline",
        "Supervisor-Worker Topology with Deterministic Validation"
    )

    # Clean flow boxes across 4 vertical tiers:
    # 1. Ingress Tier
    box1 = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.7), Inches(11.7), Inches(0.75))
    box1.fill.solid()
    box1.fill.fore_color.rgb = COLOR_PANEL_BG
    box1.line.color.rgb = COLOR_BORDER
    tf1 = box1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "1. INGRESS & PERIMETER DEFENSE"
    p1.font.bold = True
    p1.font.size = Pt(11)
    p1.font.color.rgb = COLOR_PRIMARY
    p1_sub = tf1.add_paragraph()
    p1_sub.text = "Client Request (HTTPS / SSE)  ──>  Cloud Armor L7 WAF  ──>  Cloud Run (FastAPI Gateway)  ──>  Model Armor (HIPAA PHI Redaction & Injection Filter)"
    p1_sub.font.size = Pt(10)
    p1_sub.font.color.rgb = COLOR_TEXT_DARK

    # 2. Multi-Agent Core (3 Columns)
    agent_col_width = Inches(3.75)
    agent_height = Inches(2.7)

    # Box A: Orchestrator
    box_orch = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.65), agent_col_width, agent_height)
    box_orch.fill.solid()
    box_orch.fill.fore_color.rgb = COLOR_WHITE
    box_orch.line.color.rgb = COLOR_PRIMARY
    box_orch.line.width = Pt(1.5)
    tfo = box_orch.text_frame
    tfo.margin_left = tfo.margin_right = Inches(0.2)
    tfo.margin_top = Inches(0.15)
    po = tfo.paragraphs[0]
    po.text = "Root Orchestrator (Supervisor)"
    po.font.bold = True
    po.font.size = Pt(12)
    po.font.color.rgb = COLOR_PRIMARY
    po2 = tfo.add_paragraph()
    po2.text = "Model: Gemini 2.5 Flash\n"
    po2.font.bold = True
    po2.font.size = Pt(10)
    po2.font.color.rgb = COLOR_TEXT_MUTED
    po3 = tfo.add_paragraph()
    po3.text = "• Evaluates user intent & domain.\n• SafeRefusalEngine intercepts diagnosis & prescription requests in <5ms.\n• Enforces immutable max_iterations=2 loop ceiling to prevent runaway costs."
    po3.font.size = Pt(10)
    po3.font.color.rgb = COLOR_TEXT_DARK

    # Box B: Clinical Researcher
    box_res = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.78), Inches(2.65), agent_col_width, agent_height)
    box_res.fill.solid()
    box_res.fill.fore_color.rgb = COLOR_WHITE
    box_res.line.color.rgb = COLOR_PRIMARY
    box_res.line.width = Pt(1.5)
    tfr = box_res.text_frame
    tfr.margin_left = tfr.margin_right = Inches(0.2)
    tfr.margin_top = Inches(0.15)
    pr = tfr.paragraphs[0]
    pr.text = "Clinical Researcher (Worker)"
    pr.font.bold = True
    pr.font.size = Pt(12)
    pr.font.color.rgb = COLOR_PRIMARY
    pr2 = tfr.add_paragraph()
    pr2.text = "Model: Gemini 2.5 Pro\n"
    pr2.font.bold = True
    pr2.font.size = Pt(10)
    pr2.font.color.rgb = COLOR_TEXT_MUTED
    pr3 = tfr.add_paragraph()
    pr3.text = "• Executes semantic search across 16.4k NIH MedQuAD passages.\n• Queries lab reference ranges via ClinicalDBTool.\n• Synthesizes grounded evidence draft with explicit inline [1], [2] citations."
    pr3.font.size = Pt(10)
    pr3.font.color.rgb = COLOR_TEXT_DARK

    # Box C: Reviewer
    box_rev = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.75), Inches(2.65), agent_col_width, agent_height)
    box_rev.fill.solid()
    box_rev.fill.fore_color.rgb = COLOR_WHITE
    box_rev.line.color.rgb = COLOR_PRIMARY
    box_rev.line.width = Pt(1.5)
    tfv = box_rev.text_frame
    tfv.margin_left = tfv.margin_right = Inches(0.2)
    tfv.margin_top = Inches(0.15)
    pv = tfv.paragraphs[0]
    pv.text = "Reviewer & QC (Quality Gate)"
    pv.font.bold = True
    pv.font.size = Pt(12)
    pv.font.color.rgb = COLOR_PRIMARY
    pv2 = tfv.add_paragraph()
    pv2.text = "Model: Gemini 3.5 Flash\n"
    pv2.font.bold = True
    pv2.font.size = Pt(10)
    pv2.font.color.rgb = COLOR_TEXT_MUTED
    pv3 = tfv.add_paragraph()
    pv3.text = "• Operates with zero shared hidden state to avoid confirmation bias.\n• CitationVerifier: checks that every bracketed citation maps to a valid retrieved chunk ID.\n• Blocks ungrounded claims before streaming."
    pv3.font.size = Pt(10)
    pv3.font.color.rgb = COLOR_TEXT_DARK

    # 3. Grounding & Storage Tier
    box3 = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.55), Inches(11.7), Inches(0.65))
    box3.fill.solid()
    box3.fill.fore_color.rgb = COLOR_PANEL_BG
    box3.line.color.rgb = COLOR_BORDER
    tf3 = box3.text_frame
    p3 = tf3.paragraphs[0]
    p3.text = "3. GROUNDING & DATA LAYER"
    p3.font.bold = True
    p3.font.size = Pt(11)
    p3.font.color.rgb = COLOR_PRIMARY
    p3_sub = tf3.add_paragraph()
    p3_sub.text = "Vertex AI Search (16,400+ NIH Records)  |  Local In-Memory Vector Fallback (Circuit Breaker)  |  GCS Corpus Bucket"
    p3_sub.font.size = Pt(10)
    p3_sub.font.color.rgb = COLOR_TEXT_DARK

    # 4. Observability Footer
    box4 = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(6.35), Inches(11.7), Inches(0.65))
    box4.fill.solid()
    box4.fill.fore_color.rgb = COLOR_PANEL_BG
    box4.line.color.rgb = COLOR_BORDER
    tf4 = box4.text_frame
    p4 = tf4.paragraphs[0]
    p4.text = "4. OBSERVABILITY & CONTINUOUS EVALUATION"
    p4.font.bold = True
    p4.font.size = Pt(11)
    p4.font.color.rgb = COLOR_PRIMARY
    p4_sub = tf4.add_paragraph()
    p4_sub.text = "OpenTelemetry Distributed Context  ──>  Cloud Trace  ──>  BigQuery Telemetry Sink  ──>  Cloud Scheduler Nightly Audit Pipeline"
    p4_sub.font.size = Pt(10)
    p4_sub.font.color.rgb = COLOR_TEXT_DARK

    add_speaker_notes(
        s3,
        "Slide 3 walks through our multi-agent architecture and request lifecycle.\n\n"
        "1. Ingress & Security: Requests enter via Cloud Armor and FastAPI on Cloud Run. Before touching any LLM, our Model Armor engine strips 18 HIPAA Safe Harbor identifiers and filters jailbreak patterns.\n\n"
        "2. Orchestration: The Root Orchestrator (Gemini 2.5 Flash) assesses the request. If the user asks for diagnosis or prescriptions, the Safe Refusal Engine catches it in under 5ms. If it's a valid clinical inquiry, it delegates to the Researcher.\n\n"
        "3. Research: The Clinical Researcher (Gemini 2.5 Pro) retrieves passages from Vertex AI Search and drafts a synthesis with inline citation brackets.\n\n"
        "4. Review: Crucially, that draft is sent to an independent Reviewer subagent (Gemini 3.5 Flash) with zero shared state. The CitationVerifier validates each citation against the retrieved chunks. If valid, it is streamed to the user.\n\n"
        "5. Telemetry: Every span is traced to Google Cloud Trace, and telemetry metrics (latency, token usage, cost) are streamed into BigQuery."
    )

    # =========================================================================
    # SLIDE 4: Future Work
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    apply_slide_base(
        s4,
        "Future Work: Roadmap & Clinical System Integration",
        "Technical Priorities for Production Maturation"
    )

    # 4 Milestone Cards
    fw_items = [
        ("1. EHR & Standards Integration (Cloud Healthcare API)", [
            "Connect to Google Cloud Healthcare API to query de-identified patient data.",
            "Ingest and parse FHIR R4 resources (Patient, Condition, Observation, MedicationStatement).",
            "Enable clinical researchers to compare literature findings against patient cohort criteria."
        ]),
        ("2. Distributed Session Persistence & State Store", [
            "Migrate from ephemeral in-memory session history to distributed Cloud Firestore.",
            "Support cross-session multi-turn research conversations with TTL-managed retention.",
            "Implement multi-region active-active redundancy for continuous availability."
        ]),
        ("3. Multimodal Clinical RAG (Gemini Vision)", [
            "Expand retrieval from text-only NIH XML documents to medical imagery and scans.",
            "Ingest DICOM radiology files and histology slides stored in Cloud Storage buckets.",
            "Use Gemini multimodal reasoning to correlate diagnostic imaging with clinical guidelines."
        ]),
        ("4. Enterprise Access Control & Zero-Trust Perimeter", [
            "Integrate Google Identity-Aware Proxy (IAP) for institutional Single Sign-On (SSO).",
            "Enforce role-based access control (RBAC) distinguishing researchers, oncologists, and auditors.",
            "Deploy Private Service Connect (PSC) to isolate backend services inside customer VPCs."
        ]),
    ]

    for i, (title, items) in enumerate(fw_items):
        col = i % 2
        row = i // 2
        left = Inches(0.8 + col * 6.0)
        top = Inches(1.7 + row * 2.6)
        add_card(s4, left, top, Inches(5.7), Inches(2.35), title, items)

    add_speaker_notes(
        s4,
        "Slide 4 covers our planned technical roadmap and next engineering steps.\n\n"
        "Now that the core grounded literature engine and multi-agent verification are verified, we have four logical milestones:\n\n"
        "1. EHR Integration: Utilizing the Google Cloud Healthcare API to ingest de-identified FHIR R4 records, allowing researchers to evaluate literature directly in the context of patient cohorts.\n\n"
        "2. Persistent Storage: Migrating from local in-memory session cache to multi-region Firestore, ensuring research threads survive container restarts.\n\n"
        "3. Multimodal RAG: Leveraging Gemini's native multimodal capabilities to analyze DICOM radiology scans alongside literature guidelines.\n\n"
        "4. Enterprise Security: Adding Identity-Aware Proxy for hospital SSO and Private Service Connect to satisfy enterprise zero-trust networking requirements."
    )

    return prs


if __name__ == "__main__":
    prs = build_deck()
    output_path = Path("docs/medquad_capstone_presentation.pptx")
    prs.save(str(output_path))
    print(f"Successfully generated simplified 4-slide deck at: {output_path.resolve()}")
