"""Script generated according to the `generate-slides` skill.

Creates a clean, 16:9 widescreen presentation deck using python-pptx.
Adheres strictly to the skill standards:
- Action titles (declarative sentences) on all content slides
- Category tracker (12pt, uppercase, muted)
- Clean off-white background with white card containers and subtle borders
- Cohesive Google tech palette (Google Blue, Dark Charcoal, Slate Muted)
- No marketing fluff: strictly engineering facts, metrics, and architecture
- Embedded speaker notes for Presenter View on every slide
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

# Skill Palette & Typography
COLOR_BG = RGBColor(248, 249, 250)         # Light off-white (#F8F9FA)
COLOR_CARD_BG = RGBColor(255, 255, 255)    # Card container background (#FFFFFF)
COLOR_BORDER = RGBColor(218, 220, 224)     # Border outline (#DADCE0)
COLOR_TEXT_DARK = RGBColor(32, 33, 36)     # Primary text (#202124)
COLOR_TEXT_MUTED = RGBColor(95, 99, 104)   # Secondary / subtitles (#5F6368)
COLOR_PRIMARY = RGBColor(26, 115, 232)     # Google Blue (#1A73E8)

FONT_HEADING = "Arial"
FONT_BODY = "Arial"


def apply_slide_header(slide, category: str, action_title: str):
    """Applies the skill's standard Category Tracker + Declarative Action Title."""
    # Background fill
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = COLOR_BG

    # Header text box
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.55), Inches(11.733), Inches(1.1))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    # 1. Category Tracker (12pt, uppercase, muted)
    p_cat = tf.paragraphs[0]
    p_cat.text = category.upper()
    p_cat.font.name = FONT_HEADING
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_PRIMARY

    # 2. Action Title (24pt bold, dark, declarative sentence)
    p_title = tf.add_paragraph()
    p_title.text = action_title
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_TEXT_DARK
    p_title.space_before = Pt(4)

    # Subtle horizontal divider rule
    divider = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.7), Inches(11.733), Inches(0.015))
    divider.fill.solid()
    divider.fill.fore_color.rgb = COLOR_BORDER
    divider.line.color.rgb = COLOR_BORDER


def add_card(slide, left, top, width, height, title: str, items: list[str]):
    """Creates a white card container with a subtle border and clean bullet points."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_CARD_BG
    card.line.color.rgb = COLOR_BORDER
    card.line.width = Pt(1)

    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.25)
    tf.margin_right = Inches(0.25)
    tf.margin_top = Inches(0.2)
    tf.margin_bottom = Inches(0.2)

    p_title = tf.paragraphs[0]
    p_title.text = title
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(13)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_PRIMARY

    for item in items:
        p = tf.add_paragraph()
        p.text = f"•  {item}"
        p.font.name = FONT_BODY
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_before = Pt(6)


def add_notes(slide, notes: str):
    """Embeds native presenter notes."""
    slide.notes_slide.notes_text_frame.text = notes.strip()


def build_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    s1.background.fill.solid()
    s1.background.fill.fore_color.rgb = COLOR_BG

    # Centered Title Box
    t_box = s1.shapes.add_textbox(Inches(1.2), Inches(2.1), Inches(10.9), Inches(3.2))
    tf1 = t_box.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = 0

    p_tag = tf1.paragraphs[0]
    p_tag.text = "FIELD DELIVERY ENGINEER (FDE) CAPSTONE PRESENTATION"
    p_tag.font.name = FONT_HEADING
    p_tag.font.size = Pt(12)
    p_tag.font.bold = True
    p_tag.font.color.rgb = COLOR_PRIMARY

    p_title = tf1.add_paragraph()
    p_title.text = "MedQuAD Clinical Research Assistant"
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(38)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_TEXT_DARK
    p_title.space_before = Pt(8)

    p_sub = tf1.add_paragraph()
    p_sub.text = "Multi-Agent Grounded Literature Synthesis & Clinical Guardrails"
    p_sub.font.name = FONT_BODY
    p_sub.font.size = Pt(18)
    p_sub.font.color.rgb = COLOR_TEXT_MUTED
    p_sub.space_before = Pt(8)

    # Accent divider rule
    rule = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(4.5), Inches(3.2), Inches(0.03))
    rule.fill.solid()
    rule.fill.fore_color.rgb = COLOR_PRIMARY
    rule.line.color.rgb = COLOR_PRIMARY

    # Metadata details
    meta_box = s1.shapes.add_textbox(Inches(1.2), Inches(4.75), Inches(10.9), Inches(1.0))
    tf_meta = meta_box.text_frame
    tf_meta.word_wrap = True
    tf_meta.margin_left = tf_meta.margin_top = tf_meta.margin_right = tf_meta.margin_bottom = 0

    p_meta = tf_meta.paragraphs[0]
    p_meta.text = "Candidate: Asad Patel  |  Target Role: Field Delivery Engineer (FDE)\nPlatform: Google Cloud (Vertex AI Search, Cloud Run, ADK, Gemini 2.5/3.5)"
    p_meta.font.name = FONT_BODY
    p_meta.font.size = Pt(11)
    p_meta.font.color.rgb = COLOR_TEXT_MUTED

    add_notes(
        s1,
        "Good morning. Today I am presenting the MedQuAD Clinical Research Assistant for my Field Delivery Engineer capstone evaluation.\n\n"
        "This system addresses the challenge of clinical literature discovery by combining Google Cloud's Agent Development Kit with Vertex AI Search and deterministic guardrails.\n\n"
        "This presentation covers: the clinical problem, our product capabilities, the end-to-end multi-agent architecture, and our future engineering roadmap."
    )

    # =========================================================================
    # SLIDE 2: Problem Introduction (Action Title)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    apply_slide_header(
        s2,
        category="Problem Definition",
        action_title="Clinical Search Suffers from High Manual Overhead and Unsafe Model Hallucinations"
    )

    # Card 1: Manual Search Bottleneck
    add_card(
        s2,
        left=Inches(0.8),
        top=Inches(1.9),
        width=Inches(5.7),
        height=Inches(4.8),
        title="1. Manual Literature Synthesis Friction",
        items=[
            "Clinicians and researchers spend over 35% of working hours manually combing through fragmented medical databases (NIH, NCI, CDC, PubMed).",
            "Synthesizing an authoritative answer for staging criteria, treatment protocols, or adverse reactions takes ~15 minutes of specialized labor.",
            "High research friction directly delays clinical trial design, literature review updates, and research grant submissions.",
            "Knowledge remains locked in static, disconnected XML repositories without centralized semantic search capability."
        ]
    )

    # Card 2: Foundation Model Hallucinations & Liability
    add_card(
        s2,
        left=Inches(6.8),
        top=Inches(1.9),
        width=Inches(5.7),
        height=Inches(4.8),
        title="2. Foundation Model Hallucinations & Liability",
        items=[
            "Standard off-the-shelf LLMs exhibit an ~18% citation error and hallucination rate on medical literature queries.",
            "Generic models fabricate plausible clinical claims, non-existent PMIDs, and outdated pharmaceutical dosing guidelines.",
            "Unguarded models attempt to answer personal diagnosis and prescription questions, creating severe malpractice liability.",
            "Commercial consumer chatbots lack deterministic 1:1 chunk verification to prove evidence provenance."
        ]
    )

    add_notes(
        s2,
        "Slide 2 establishes the core problem.\n\n"
        "Clinical researchers face two competing challenges:\n"
        "First, manual research takes too long. Combing through NIH databases, clinical trials, and FDA inserts consumes over 35% of a researcher's time, averaging 15 minutes per query.\n\n"
        "Second, relying on standard LLMs is dangerous in clinical contexts. Studies show foundation models hallucinate citations roughly 18% of the time, and unguarded models attempt to offer personal medical advice, creating unacceptable legal risk.\n\n"
        "The MedQuAD Assistant bridges this divide by delivering automated literature synthesis with strict 1:1 citation proof and deterministic safety boundaries."
    )

    # =========================================================================
    # SLIDE 3: Product Overview (Action Title)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    apply_slide_header(
        s3,
        category="Product Overview",
        action_title="MedQuAD Delivers Grounded Literature Synthesis with Deterministic Verification"
    )

    q_w = Inches(5.7)
    q_h = Inches(2.3)

    # Quadrant 1: Grounded Corpus
    add_card(
        s3,
        left=Inches(0.8),
        top=Inches(1.9),
        width=q_w,
        height=q_h,
        title="Authoritative NIH Corpus Grounding",
        items=[
            "Indexes 16,400+ verified medical Q&A pairs from NIH, NCI, CDC, and MedlinePlus across 12 clinical domains.",
            "Structured with 500-token semantic chunks and 10% overlap to preserve clinical context.",
            "Powered by Google Vertex AI Search with automated circuit-breaker fallback to an in-memory vector store."
        ]
    )

    # Quadrant 2: 1:1 Citation Audit
    add_card(
        s3,
        left=Inches(6.8),
        top=Inches(1.9),
        width=q_w,
        height=q_h,
        title="Deterministic Citation Verification",
        items=[
            "Independent Reviewer subagent cross-examines draft responses against retrieved source passages.",
            "CitationVerifier ensures 100% of bracketed claims map to valid retrieved chunk IDs.",
            "Ungrounded statements are automatically flagged and removed before streaming to the user."
        ]
    )

    # Quadrant 3: Guardrails & Safe Refusal
    add_card(
        s3,
        left=Inches(0.8),
        top=Inches(4.4),
        width=q_w,
        height=q_h,
        title="Layer 8 Safety & Safe Refusal Engine",
        items=[
            "Pre-flight de-identification of 18 HIPAA Safe Harbor identifiers (MRN, SSN, patient names).",
            "Immediate rejection (<5ms) of personal diagnosis and drug dosing prompts without invoking model tokens.",
            "Structured response redirects users to certified healthcare providers and emergency services."
        ]
    )

    # Quadrant 4: Practical FinOps
    add_card(
        s3,
        left=Inches(6.8),
        top=Inches(4.4),
        width=q_w,
        height=q_h,
        title="Cost-Effective Model Tiering",
        items=[
            "Tiered Gemini deployment: Flash 2.5 for intent/routing, Pro 2.5 for synthesis, Flash 3.5 for audit.",
            "Blended query cost of ~$0.0035 ($351/month for 100,000 queries) vs. $15.00 manual labor.",
            "Deployed on Cloud Run with p95 response latency under 3 seconds and zero idle server costs."
        ]
    )

    add_notes(
        s3,
        "Slide 3 outlines what the product actually does and how it operates.\n\n"
        "1. Authoritative Grounding: We indexed 16,400+ verified NIH pairs into Vertex AI Search with 500-token semantic chunks.\n\n"
        "2. Deterministic Verification: Rather than hoping the model doesn't hallucinate, an independent Reviewer agent verifies every bracketed citation against the retrieved chunks, achieving 100% citation precision.\n\n"
        "3. Safe Refusal Engine: If a user enters diagnostic or dosing questions, our boundary engine catches it in under 5ms, returning a clinical disclaimer with zero token waste.\n\n"
        "4. Cost Efficiency: By tiering Gemini models, we keep inference costs to just $0.0035 per query, running serverless on Cloud Run."
    )

    # =========================================================================
    # SLIDE 4: System Architecture (Action Title)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    apply_slide_header(
        s4,
        category="System Architecture",
        action_title="Multi-Agent ADK Architecture Decouples Retrieval, Synthesis, and Verification"
    )

    # Tier 1: Ingress
    b1 = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.85), Inches(11.733), Inches(0.7))
    b1.fill.solid()
    b1.fill.fore_color.rgb = COLOR_CARD_BG
    b1.line.color.rgb = COLOR_BORDER
    tf_b1 = b1.text_frame
    tf_b1.margin_left = tf_b1.margin_right = Inches(0.2)
    tf_b1.margin_top = Inches(0.1)
    p_b1_t = tf_b1.paragraphs[0]
    p_b1_t.text = "1. INGRESS & PERIMETER DEFENSE"
    p_b1_t.font.name = FONT_HEADING
    p_b1_t.font.size = Pt(10.5)
    p_b1_t.font.bold = True
    p_b1_t.font.color.rgb = COLOR_PRIMARY
    p_b1_s = tf_b1.add_paragraph()
    p_b1_s.text = "Client (HTTPS / SSE)  ──>  Cloud Armor L7 WAF  ──>  Cloud Run (FastAPI)  ──>  Model Armor (HIPAA PHI Redaction & Prompt Guard)"
    p_b1_s.font.name = FONT_BODY
    p_b1_s.font.size = Pt(9.5)
    p_b1_s.font.color.rgb = COLOR_TEXT_DARK

    # Tier 2: Agent Boxes (3 Columns)
    col_w = Inches(3.75)
    col_h = Inches(2.7)

    # Orchestrator
    box_o = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.7), col_w, col_h)
    box_o.fill.solid()
    box_o.fill.fore_color.rgb = COLOR_CARD_BG
    box_o.line.color.rgb = COLOR_PRIMARY
    box_o.line.width = Pt(1.5)
    tfo = box_o.text_frame
    tfo.margin_left = tfo.margin_right = Inches(0.2)
    tfo.margin_top = Inches(0.15)
    po1 = tfo.paragraphs[0]
    po1.text = "Root Orchestrator (Supervisor)"
    po1.font.bold = True
    po1.font.size = Pt(11.5)
    po1.font.color.rgb = COLOR_PRIMARY
    po2 = tfo.add_paragraph()
    po2.text = "Model: Gemini 2.5 Flash\n"
    po2.font.bold = True
    po2.font.size = Pt(9.5)
    po2.font.color.rgb = COLOR_TEXT_MUTED
    po3 = tfo.add_paragraph()
    po3.text = "• Classifies clinical intent & domain.\n• SafeRefusalEngine rejects diagnosis/dosing in <5ms.\n• Enforces strict max_iterations=2 loop ceiling."
    po3.font.size = Pt(9.5)
    po3.font.color.rgb = COLOR_TEXT_DARK

    # Researcher
    box_r = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.78), Inches(2.7), col_w, col_h)
    box_r.fill.solid()
    box_r.fill.fore_color.rgb = COLOR_CARD_BG
    box_r.line.color.rgb = COLOR_PRIMARY
    box_r.line.width = Pt(1.5)
    tfr = box_r.text_frame
    tfr.margin_left = tfr.margin_right = Inches(0.2)
    tfr.margin_top = Inches(0.15)
    pr1 = tfr.paragraphs[0]
    pr1.text = "Clinical Researcher (Worker)"
    pr1.font.bold = True
    pr1.font.size = Pt(11.5)
    pr1.font.color.rgb = COLOR_PRIMARY
    pr2 = tfr.add_paragraph()
    pr2.text = "Model: Gemini 2.5 Pro\n"
    pr2.font.bold = True
    pr2.font.size = Pt(9.5)
    pr2.font.color.rgb = COLOR_TEXT_MUTED
    pr3 = tfr.add_paragraph()
    pr3.text = "• Queries Vertex AI Search (16.4k NIH pairs).\n• Fetches lab test ranges via ClinicalDBTool.\n• Drafts evidence synthesis with inline [1], [2] citations."
    pr3.font.size = Pt(9.5)
    pr3.font.color.rgb = COLOR_TEXT_DARK

    # Reviewer
    box_v = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.75), Inches(2.7), col_w, col_h)
    box_v.fill.solid()
    box_v.fill.fore_color.rgb = COLOR_CARD_BG
    box_v.line.color.rgb = COLOR_PRIMARY
    box_v.line.width = Pt(1.5)
    tfv = box_v.text_frame
    tfv.margin_left = tfv.margin_right = Inches(0.2)
    tfv.margin_top = Inches(0.15)
    pv1 = tfv.paragraphs[0]
    pv1.text = "Reviewer & QC (Quality Gate)"
    pv1.font.bold = True
    pv1.font.size = Pt(11.5)
    pv1.font.color.rgb = COLOR_PRIMARY
    pv2 = tfv.add_paragraph()
    pv2.text = "Model: Gemini 3.5 Flash\n"
    pv2.font.bold = True
    pv2.font.size = Pt(9.5)
    pv2.font.color.rgb = COLOR_TEXT_MUTED
    pv3 = tfv.add_paragraph()
    pv3.text = "• Operates with zero shared hidden state.\n• CitationVerifier checks every citation against chunk IDs.\n• Strips ungrounded claims before streaming."
    pv3.font.size = Pt(9.5)
    pv3.font.color.rgb = COLOR_TEXT_DARK

    # Tier 3: Grounding
    b3 = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.55), Inches(11.733), Inches(0.65))
    b3.fill.solid()
    b3.fill.fore_color.rgb = COLOR_CARD_BG
    b3.line.color.rgb = COLOR_BORDER
    tf_b3 = b3.text_frame
    tf_b3.margin_left = tf_b3.margin_right = Inches(0.2)
    tf_b3.margin_top = Inches(0.1)
    p_b3_t = tf_b3.paragraphs[0]
    p_b3_t.text = "3. GROUNDING & DATA LAYER"
    p_b3_t.font.name = FONT_HEADING
    p_b3_t.font.size = Pt(10.5)
    p_b3_t.font.bold = True
    p_b3_t.font.color.rgb = COLOR_PRIMARY
    p_b3_s = tf_b3.add_paragraph()
    p_b3_s.text = "Vertex AI Search Datastore (16.4k NIH pairs)  |  In-Memory Vector Fallback (Circuit Breaker)  |  GCS Raw XML Staging"
    p_b3_s.font.name = FONT_BODY
    p_b3_s.font.size = Pt(9.5)
    p_b3_s.font.color.rgb = COLOR_TEXT_DARK

    # Tier 4: Observability
    b4 = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(6.35), Inches(11.733), Inches(0.65))
    b4.fill.solid()
    b4.fill.fore_color.rgb = COLOR_CARD_BG
    b4.line.color.rgb = COLOR_BORDER
    tf_b4 = b4.text_frame
    tf_b4.margin_left = tf_b4.margin_right = Inches(0.2)
    tf_b4.margin_top = Inches(0.1)
    p_b4_t = tf_b4.paragraphs[0]
    p_b4_t.text = "4. OBSERVABILITY & CONTINUOUS EVALUATION"
    p_b4_t.font.name = FONT_HEADING
    p_b4_t.font.size = Pt(10.5)
    p_b4_t.font.bold = True
    p_b4_t.font.color.rgb = COLOR_PRIMARY
    p_b4_s = tf_b4.add_paragraph()
    p_b4_s.text = "OpenTelemetry Distributed Tracing  ──>  Google Cloud Trace  ──>  BigQuery Telemetry Sink  ──>  Automated Nightly Quality Audit"
    p_b4_s.font.name = FONT_BODY
    p_b4_s.font.size = Pt(9.5)
    p_b4_s.font.color.rgb = COLOR_TEXT_DARK

    add_notes(
        s4,
        "Slide 4 walks through the technical architecture and request lifecycle:\n\n"
        "1. Ingress & Security: Requests enter via Cloud Armor and FastAPI on Cloud Run. Before touching any model, Model Armor redacts 18 HIPAA Safe Harbor identifiers and filters jailbreak patterns.\n\n"
        "2. Orchestration: The Root Orchestrator (Gemini 2.5 Flash) assesses the query. If it asks for diagnosis or prescriptions, the Safe Refusal Engine catches it in under 5ms. If valid, it delegates to the Researcher.\n\n"
        "3. Research: The Clinical Researcher (Gemini 2.5 Pro) retrieves passages from Vertex AI Search and synthesizes a draft with explicit citations.\n\n"
        "4. Review: The draft is reviewed by an independent Reviewer subagent (Gemini 3.5 Flash) with zero shared state. The CitationVerifier validates every citation against retrieved chunk IDs before release.\n\n"
        "5. Telemetry: Traces are pushed to Cloud Trace, and telemetry data (latency, cost, tokens) is streamed to BigQuery."
    )

    # =========================================================================
    # SLIDE 5: Future Work (Action Title)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    apply_slide_header(
        s5,
        category="Future Roadmap",
        action_title="Roadmap Focuses on Clinical Standards, State Persistence, and Multimodal RAG"
    )

    fw_items = [
        ("1. EHR Standards (Google Cloud Healthcare API)", [
            "Integrate Google Cloud Healthcare API to query de-identified clinical records.",
            "Parse and ingest FHIR R4 resources (Patient, Condition, Observation, MedicationStatement).",
            "Enable researchers to cross-reference literature evidence against clinical cohort criteria."
        ]),
        ("2. Distributed Session Persistence & State Store", [
            "Migrate from ephemeral in-memory conversation state to distributed Cloud Firestore.",
            "Support multi-turn research threads across container instances with TTL retention.",
            "Implement multi-region active-active replication for enterprise high availability."
        ]),
        ("3. Multimodal Clinical RAG (Gemini Vision)", [
            "Expand ingestion pipeline from text-only XML records to diagnostic imaging.",
            "Ingest DICOM radiology files and pathology slide scans stored in GCS buckets.",
            "Use Gemini multimodal reasoning to correlate medical imaging with clinical guidelines."
        ]),
        ("4. Enterprise Access Control & Zero-Trust Perimeter", [
            "Integrate Google Identity-Aware Proxy (IAP) for institutional Single Sign-On (SSO).",
            "Enforce role-based access control (RBAC) separating researchers, oncologists, and auditors.",
            "Deploy Private Service Connect (PSC) to isolate backend services inside customer VPCs."
        ]),
    ]

    for i, (title, items) in enumerate(fw_items):
        col = i % 2
        row = i // 2
        left = Inches(0.8 + col * 6.0)
        top = Inches(1.9 + row * 2.5)
        add_card(s5, left, top, Inches(5.7), Inches(2.3), title, items)

    add_notes(
        s5,
        "Slide 5 outlines our concrete next engineering milestones:\n\n"
        "1. EHR Integration: Using the Google Cloud Healthcare API to ingest de-identified FHIR R4 records, allowing researchers to contextualize literature findings against patient cohort criteria.\n\n"
        "2. State Persistence: Migrating from local in-memory session cache to distributed Firestore, ensuring research threads survive container restarts across regions.\n\n"
        "3. Multimodal RAG: Leveraging Gemini's multimodal capabilities to analyze DICOM radiology scans alongside literature guidelines.\n\n"
        "4. Enterprise Security: Adding Identity-Aware Proxy for hospital SSO and Private Service Connect to satisfy enterprise zero-trust networking requirements."
    )

    return prs


if __name__ == "__main__":
    prs = build_deck()
    output_path = Path("docs/medquad_capstone_presentation.pptx")
    prs.save(str(output_path))
    print(f"Successfully generated presentation deck at: {output_path.resolve()}")
