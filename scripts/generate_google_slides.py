"""Script generated according to the `generate-slides` skill.

Creates a clean, 16:9 widescreen presentation deck using python-pptx.
Adheres strictly to the skill standards:
- Action titles (declarative sentences) on all content slides
- Category tracker (12pt, uppercase, muted)
- Clean off-white background with white card containers and subtle borders
- Cohesive Google tech palette (Google Blue, Dark Charcoal, Slate Muted)
- No marketing fluff: strictly engineering facts, metrics, and architecture
- Slide 4 features an ACTUAL visual architecture diagram with boxes, containers, and directional arrows
- Embedded speaker notes for Presenter View on every slide
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.oxml import parse_xml
from pptx.util import Inches, Pt

# Skill Palette & Typography
COLOR_BG = RGBColor(248, 249, 250)         # Light off-white (#F8F9FA)
COLOR_CARD_BG = RGBColor(255, 255, 255)    # Card container background (#FFFFFF)
COLOR_BORDER = RGBColor(218, 220, 224)     # Border outline (#DADCE0)
COLOR_TEXT_DARK = RGBColor(32, 33, 36)     # Primary text (#202124)
COLOR_TEXT_MUTED = RGBColor(95, 99, 104)   # Secondary / subtitles (#5F6368)
COLOR_PRIMARY = RGBColor(26, 115, 232)     # Google Blue (#1A73E8)
COLOR_GREEN = RGBColor(52, 168, 83)        # Google Green (#34A853)
COLOR_RED = RGBColor(234, 67, 53)          # Google Red (#EA4335)
COLOR_RED_BG = RGBColor(254, 242, 242)     # Soft red background (#FEF2F2)
COLOR_BLUE_BG = RGBColor(232, 240, 254)    # Soft blue background (#E8F0FE)

FONT_HEADING = "Arial"
FONT_BODY = "Arial"


def apply_slide_header(slide, category: str, action_title: str):
    """Applies the skill's standard Category Tracker + Declarative Action Title."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = COLOR_BG

    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.55), Inches(11.733), Inches(1.1))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_cat = tf.paragraphs[0]
    p_cat.text = category.upper()
    p_cat.font.name = FONT_HEADING
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_PRIMARY

    p_title = tf.add_paragraph()
    p_title.text = action_title
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_TEXT_DARK
    p_title.space_before = Pt(4)

    divider = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.65), Inches(11.733), Inches(0.015))
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


def add_diag_box(
    slide,
    left,
    top,
    width,
    height,
    title: str,
    subtitle: str = "",
    bullets: list[str] | None = None,
    border_color=COLOR_BORDER,
    fill_color=COLOR_CARD_BG,
    title_color=COLOR_PRIMARY,
    is_rounded=True,
):
    """Draws a component box for architecture diagrams."""
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if is_rounded else MSO_SHAPE.RECTANGLE
    box = slide.shapes.add_shape(shape_type, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = fill_color
    box.line.color.rgb = border_color
    box.line.width = Pt(1.2)

    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.12)
    tf.margin_right = Inches(0.12)
    tf.margin_top = Inches(0.08)
    tf.margin_bottom = Inches(0.08)

    p_t = tf.paragraphs[0]
    p_t.text = title
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(10)
    p_t.font.bold = True
    p_t.font.color.rgb = title_color

    if subtitle:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.name = FONT_HEADING
        p_sub.font.size = Pt(8)
        p_sub.font.bold = True
        p_sub.font.color.rgb = COLOR_TEXT_MUTED

    if bullets:
        for b in bullets:
            p_b = tf.add_paragraph()
            p_b.text = f"• {b}"
            p_b.font.name = FONT_BODY
            p_b.font.size = Pt(8)
            p_b.font.color.rgb = COLOR_TEXT_DARK
            p_b.space_before = Pt(1.5)
    return box


def add_arrow_connector(
    slide,
    x1,
    y1,
    x2,
    y2,
    color=COLOR_PRIMARY,
    width=1.5,
    label="",
    label_dx=0.0,
    label_dy=-0.16,
    is_dashed=False,
):
    """Draws a clean directional line connector with an arrowhead and optional text label."""
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    conn.line.color.rgb = color
    conn.line.width = Pt(width)
    line_xml = conn._element.spPr.ln
    head_end = parse_xml(
        '<a:headEnd xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" type="triangle" w="med" len="med"/>'
    )
    line_xml.append(head_end)
    if is_dashed:
        cust_dash = parse_xml(
            '<a:prstDash xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" val="dash"/>'
        )
        line_xml.append(cust_dash)

    if label:
        mid_x = (x1 + x2) / 2 + Inches(label_dx)
        mid_y = (y1 + y2) / 2 + Inches(label_dy)
        tb = slide.shapes.add_textbox(mid_x - Inches(0.85), mid_y, Inches(1.7), Inches(0.24))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = label
        p.font.name = FONT_HEADING
        p.font.size = Pt(7.5)
        p.font.bold = True
        p.font.color.rgb = color


def add_orthogonal_arrow(
    slide,
    x1,
    y1,
    x2,
    y2,
    color=COLOR_PRIMARY,
    width=1.5,
    label="",
    label_x_offset=0.0,
):
    """Draws an orthogonal (stepped) connector with an arrowhead."""
    mid_y = (y1 + y2) / 2
    c1 = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x1, mid_y)
    c1.line.color.rgb = color
    c1.line.width = Pt(width)

    c2 = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, mid_y, x2, mid_y)
    c2.line.color.rgb = color
    c2.line.width = Pt(width)

    c3 = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x2, mid_y, x2, y2)
    c3.line.color.rgb = color
    c3.line.width = Pt(width)
    line_xml = c3._element.spPr.ln
    head_end = parse_xml(
        '<a:headEnd xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" type="triangle" w="med" len="med"/>'
    )
    line_xml.append(head_end)

    if label:
        tb = slide.shapes.add_textbox((x1 + x2) / 2 - Inches(0.85) + Inches(label_x_offset), mid_y - Inches(0.22), Inches(1.7), Inches(0.2))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = label
        p.font.name = FONT_HEADING
        p.font.size = Pt(7.5)
        p.font.bold = True
        p.font.color.rgb = color


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

    rule = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(4.5), Inches(3.2), Inches(0.03))
    rule.fill.solid()
    rule.fill.fore_color.rgb = COLOR_PRIMARY
    rule.line.color.rgb = COLOR_PRIMARY

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
    # SLIDE 4: System Architecture (ACTUAL DIAGRAM WITH BOXES & ARROWS)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    apply_slide_header(
        s4,
        category="System Architecture",
        action_title="Multi-Agent ADK Architecture Decouples Retrieval, Synthesis, and Verification"
    )

    # -------------------------------------------------------------------------
    # ROW 1: INGRESS & SECURITY BOUNDARY (Container)
    # -------------------------------------------------------------------------
    cont1 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(1.75), Inches(12.133), Inches(1.3))
    cont1.fill.solid()
    cont1.fill.fore_color.rgb = COLOR_CARD_BG
    cont1.line.color.rgb = COLOR_BORDER
    cont1.line.width = Pt(1)
    tf_c1 = cont1.text_frame
    tf_c1.margin_left = Inches(0.15)
    tf_c1.margin_top = Inches(0.06)
    p_c1 = tf_c1.paragraphs[0]
    p_c1.text = "1. INGRESS & PERIMETER SECURITY GATEWAY"
    p_c1.font.name = FONT_HEADING
    p_c1.font.size = Pt(9)
    p_c1.font.bold = True
    p_c1.font.color.rgb = COLOR_TEXT_MUTED

    # Box 1: Clinician UI
    add_diag_box(
        s4,
        left=Inches(0.8),
        top=Inches(2.02),
        width=Inches(1.5),
        height=Inches(0.9),
        title="Clinician / UI",
        subtitle="Web App & REST",
        bullets=["HTTPS / SSE", "Inline Citations"],
        border_color=COLOR_PRIMARY,
        fill_color=COLOR_BLUE_BG,
    )

    # Arrow 1: Client -> Cloud Armor
    add_arrow_connector(s4, Inches(2.3), Inches(2.47), Inches(2.65), Inches(2.47), label="1. Query")

    # Box 2: Cloud Armor
    add_diag_box(
        s4,
        left=Inches(2.65),
        top=Inches(2.02),
        width=Inches(1.5),
        height=Inches(0.9),
        title="Cloud Armor",
        subtitle="L7 WAF & DDoS",
        bullets=["IP Throttling", "Bot Defense"],
    )

    # Arrow 2: Cloud Armor -> Cloud Run
    add_arrow_connector(s4, Inches(4.15), Inches(2.47), Inches(4.5), Inches(2.47), label="2. Clean")

    # Box 3: Cloud Run
    add_diag_box(
        s4,
        left=Inches(4.5),
        top=Inches(2.02),
        width=Inches(1.7),
        height=Inches(0.9),
        title="Cloud Run Gateway",
        subtitle="FastAPI Container",
        bullets=["Auth Token Check", "Streaming Engine"],
    )

    # Arrow 3: Cloud Run -> Model Armor
    add_arrow_connector(s4, Inches(6.2), Inches(2.47), Inches(6.55), Inches(2.47), label="3. Ingest")

    # Box 4: Model Armor Guardrail
    add_diag_box(
        s4,
        left=Inches(6.55),
        top=Inches(2.02),
        width=Inches(2.1),
        height=Inches(0.9),
        title="Model Armor",
        subtitle="Layer 8 Guardrail",
        bullets=["18 HIPAA PHI De-id", "Injection Filter"],
        border_color=COLOR_PRIMARY,
    )

    # Arrow 4a: Model Armor -> Safe Refusal Exit
    add_arrow_connector(
        s4,
        Inches(8.65),
        Inches(2.47),
        Inches(9.1),
        Inches(2.47),
        color=COLOR_RED,
        label="Refusal (<5ms)",
    )

    # Box 5: Safe Refusal Exit
    add_diag_box(
        s4,
        left=Inches(9.1),
        top=Inches(2.02),
        width=Inches(3.4),
        height=Inches(0.9),
        title="Safe Refusal Engine Exit",
        subtitle="Boundary Lock: Diagnosis & Rx Dosing",
        bullets=["Returns emergency disclaimer", "Zero LLM tokens spent"],
        border_color=COLOR_RED,
        fill_color=COLOR_RED_BG,
        title_color=COLOR_RED,
    )

    # Orthogonal Arrow 4b: Model Armor down to Root Orchestrator
    add_orthogonal_arrow(
        s4,
        x1=Inches(7.6),
        y1=Inches(2.92),
        x2=Inches(2.35),
        y2=Inches(3.45),
        color=COLOR_GREEN,
        width=1.5,
        label="4. Valid Inquiry (Sanitized Query)",
        label_x_offset=0.2,
    )

    # -------------------------------------------------------------------------
    # ROW 2: GOOGLE ADK MULTI-AGENT CORE (Container)
    # -------------------------------------------------------------------------
    cont2 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(3.18), Inches(12.133), Inches(2.32))
    cont2.fill.solid()
    cont2.fill.fore_color.rgb = COLOR_CARD_BG
    cont2.line.color.rgb = COLOR_PRIMARY
    cont2.line.width = Pt(1.5)
    tf_c2 = cont2.text_frame
    tf_c2.margin_left = Inches(0.15)
    tf_c2.margin_top = Inches(0.06)
    p_c2 = tf_c2.paragraphs[0]
    p_c2.text = "2. GOOGLE ADK MULTI-AGENT CORE (SUPERVISOR-WORKER DECOUPLED TOPOLOGY)"
    p_c2.font.name = FONT_HEADING
    p_c2.font.size = Pt(9)
    p_c2.font.bold = True
    p_c2.font.color.rgb = COLOR_PRIMARY

    # Agent 1: Root Orchestrator
    add_diag_box(
        s4,
        left=Inches(0.8),
        top=Inches(3.45),
        width=Inches(3.1),
        height=Inches(1.85),
        title="Root Orchestrator",
        subtitle="Supervisor  |  Gemini 2.5 Flash",
        bullets=[
            "Classifies clinical intent & domain",
            "SafeRefusalEngine policy routing",
            "Enforces max_iterations=2 loop ceiling",
            "Maintains top-level conversation state",
        ],
        border_color=COLOR_PRIMARY,
    )

    # Arrow 5: Root Orchestrator -> Clinical Researcher
    add_arrow_connector(s4, Inches(3.9), Inches(4.37), Inches(4.7), Inches(4.37), label="5. Route")

    # Agent 2: Clinical Researcher
    add_diag_box(
        s4,
        left=Inches(4.7),
        top=Inches(3.45),
        width=Inches(3.5),
        height=Inches(1.85),
        title="Clinical Researcher",
        subtitle="Worker  |  Gemini 2.5 Pro",
        bullets=[
            "Deep biomedical literature reasoning",
            "Executes semantic search over NIH data",
            "Queries lab test reference ranges",
            "Drafts synthesis with inline [1],[2] tags",
        ],
        border_color=COLOR_PRIMARY,
    )

    # Arrow 8: Clinical Researcher -> Reviewer
    add_arrow_connector(s4, Inches(8.2), Inches(4.37), Inches(8.9), Inches(4.37), label="8. Draft")

    # Agent 3: Reviewer & QC
    add_diag_box(
        s4,
        left=Inches(8.9),
        top=Inches(3.45),
        width=Inches(3.6),
        height=Inches(1.85),
        title="Reviewer & QC Gate",
        subtitle="Auditor  |  Gemini 3.5 Flash",
        bullets=[
            "Zero shared hidden state (no bias)",
            "CitationVerifier: 100% chunk ID match",
            "Strips ungrounded/hallucinated statements",
            "Approves streaming release to client",
        ],
        border_color=COLOR_GREEN,
        title_color=COLOR_GREEN,
    )

    # -------------------------------------------------------------------------
    # ROW 3: GROUNDING & DATA STORES (Container)
    # -------------------------------------------------------------------------
    cont3 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(5.62), Inches(12.133), Inches(1.48))
    cont3.fill.solid()
    cont3.fill.fore_color.rgb = COLOR_CARD_BG
    cont3.line.color.rgb = COLOR_BORDER
    cont3.line.width = Pt(1)
    tf_c3 = cont3.text_frame
    tf_c3.margin_left = Inches(0.15)
    tf_c3.margin_top = Inches(0.06)
    p_c3 = tf_c3.paragraphs[0]
    p_c3.text = "3. GROUNDING DATA STORES & OBSERVABILITY SINK"
    p_c3.font.name = FONT_HEADING
    p_c3.font.size = Pt(9)
    p_c3.font.bold = True
    p_c3.font.color.rgb = COLOR_TEXT_MUTED

    # Store 1: Vertex AI Search
    add_diag_box(
        s4,
        left=Inches(0.8),
        top=Inches(5.92),
        width=Inches(2.8),
        height=Inches(1.05),
        title="Vertex AI Search",
        subtitle="Authoritative Literature Datastore",
        bullets=["16,400+ NIH Q&A pairs indexed", "500-token semantic chunks (10% ovlp)"],
    )

    # Store 2: ClinicalDBTool
    add_diag_box(
        s4,
        left=Inches(3.8),
        top=Inches(5.92),
        width=Inches(2.7),
        height=Inches(1.05),
        title="ClinicalDBTool",
        subtitle="Structured Reference Database",
        bullets=["Lab test reference ranges", "Diagnostic biomarker thresholds"],
    )

    # Store 3: In-Memory Vector Fallback
    add_diag_box(
        s4,
        left=Inches(6.7),
        top=Inches(5.92),
        width=Inches(2.8),
        height=Inches(1.05),
        title="Vector DB Fallback",
        subtitle="Circuit Breaker Redundancy",
        bullets=["Local FAISS in-memory store", "Sub-50ms fallback on 504 timeouts"],
    )

    # Store 4: Cloud Trace & BigQuery
    add_diag_box(
        s4,
        left=Inches(9.7),
        top=Inches(5.92),
        width=Inches(2.8),
        height=Inches(1.05),
        title="Cloud Trace & BigQuery",
        subtitle="Observability & Quality Sink",
        bullets=["OpenTelemetry distributed spans", "Nightly automated evaluation audits"],
    )

    # Arrows between Clinical Researcher & Grounding:
    # 6: Down from Researcher to Grounding
    add_arrow_connector(
        s4,
        Inches(5.7),
        Inches(5.3),
        Inches(5.7),
        Inches(5.92),
        color=COLOR_PRIMARY,
        label="6. Query",
        label_dx=0.25,
        label_dy=-0.1,
    )
    # 7: Up from Grounding to Researcher
    add_arrow_connector(
        s4,
        Inches(6.5),
        Inches(5.92),
        Inches(6.5),
        Inches(5.3),
        color=COLOR_PRIMARY,
        label="7. Chunks",
        label_dx=0.3,
        label_dy=0.08,
    )

    # Telemetry Dotted Connector from Reviewer down to Cloud Trace
    add_arrow_connector(
        s4,
        Inches(11.1),
        Inches(5.3),
        Inches(11.1),
        Inches(5.92),
        color=COLOR_TEXT_MUTED,
        label="Telemetry",
        label_dx=0.35,
        label_dy=0.0,
        is_dashed=True,
    )

    add_notes(
        s4,
        "Slide 4 displays the concrete architecture diagram showing the visual flow across components:\n\n"
        "1. Ingress & Perimeter: Clinician queries enter via Cloud Armor and FastAPI on Cloud Run. Model Armor performs Layer 8 guardrails—scrubbing 18 HIPAA Safe Harbor identifiers and filtering jailbreak injections.\n\n"
        "2. Safe Refusal Branch: If the user asks for personal medical advice or dosing, the Safe Refusal Engine exits in under 5ms without invoking model tokens.\n\n"
        "3. Multi-Agent Orchestration: If valid, the query passes to the Root Orchestrator (Gemini 2.5 Flash), which classifies intent and routes to the Clinical Researcher (Gemini 2.5 Pro).\n\n"
        "4. Grounding: The Researcher retrieves 500-token chunks from Vertex AI Search (with fallback to an in-memory vector store) and fetches lab ranges via ClinicalDBTool, synthesizing an evidence draft with inline citation tags.\n\n"
        "5. Independent Verification: The Reviewer & QC agent (Gemini 3.5 Flash) operates with zero shared state. Its CitationVerifier audits every single citation bracket against retrieved chunk IDs. Only 100% verified responses are streamed back to the client.\n\n"
        "6. Observability: Every span is traced to Cloud Trace, and telemetry is recorded in BigQuery for continuous auditing."
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
