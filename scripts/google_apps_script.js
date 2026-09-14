/**
 * MedQuAD Clinical Research Assistant - Google Apps Script
 *
 * Focus: High-clarity architecture diagram with minimal element detail
 * and rich, descriptive data flow arrows between elements.
 *
 * Target Slide: h66d1b35f290be7cc_11_38
 *
 * HOW TO RUN:
 * 1. In your Google Slides presentation (https://docs.google.com/presentation/d/1cdBc40xSexQXZ3GtXyOKMgSwuobGbfWX8sRn46Jr6cU/edit),
 *    click: Extensions -> Apps Script
 * 2. Replace the contents of Code.gs with this script.
 * 3. Click "Save" (Ctrl+S / Cmd+S).
 * 4. Make sure "drawArchitectureDiagram" is selected in the function dropdown, then click "Run".
 * 5. Review the updated slide — each element is clean & punchy, and every arrow describes
 *    the exact payload, security filter, and protocol contract!
 */

function drawArchitectureDiagram() {
  const presentation = SlidesApp.getActivePresentation();
  const targetSlideId = 'h66d1b35f290be7cc_11_38';

  // 1. Locate target slide
  let slide = presentation.getSlideById(targetSlideId);
  if (!slide) {
    const selection = presentation.getSelection();
    slide = selection.getCurrentPage();
    if (!slide) {
      slide = presentation.getSlides()[3] || presentation.getSlides()[0];
    }
  }

  // 2. Clear previous diagram shapes if any were tagged
  const existingShapes = slide.getShapes();
  for (let i = 0; i < existingShapes.length; i++) {
    const title = existingShapes[i].getTitle();
    if (title && title.indexOf('MEDQUAD_') === 0) {
      existingShapes[i].remove();
    }
  }

  // 3. Coordinate scaling (based on 960 x 540 reference canvas)
  const pageWidth = presentation.getPageWidth();
  const pageHeight = presentation.getPageHeight();
  const sx = pageWidth / 960;
  const sy = pageHeight / 540;

  function ptX(x) { return x * sx; }
  function ptY(y) { return y * sy; }
  function ptW(w) { return w * sx; }
  function ptH(h) { return h * sy; }

  // Color Palette
  const COLOR_PRIMARY = '#1A73E8';  // Google Blue
  const COLOR_BORDER = '#DADCE0';   // Light Gray Border
  const COLOR_DARK = '#202124';     // Dark Charcoal
  const COLOR_MUTED = '#5F6368';    // Secondary Slate
  const COLOR_CARD = '#FFFFFF';     // White Card
  const COLOR_BLUE_BG = '#E8F0FE';  // Soft Blue
  const COLOR_RED_BG = '#FEF2F2';   // Soft Red
  const COLOR_RED = '#EA4335';      // Google Red
  const COLOR_GREEN = '#34A853';    // Google Green

  // Helper: Draw Minimal, Clean Component Box
  function addCleanBox(x, y, w, h, title, subtitle, descriptor, borderCol, fillCol, titleCol) {
    const box = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE, ptX(x), ptY(y), ptW(w), ptH(h));
    box.setTitle('MEDQUAD_BOX');
    box.getFill().setSolidFill(fillCol || COLOR_CARD);
    box.getBorder().getLineFill().setSolidFill(borderCol || COLOR_BORDER);
    box.getBorder().setWeight(borderCol === COLOR_PRIMARY || borderCol === COLOR_GREEN || borderCol === COLOR_RED ? 1.5 : 1);

    let textContent = title;
    if (subtitle) textContent += '\n' + subtitle;
    if (descriptor) textContent += '\n' + descriptor;
    const tr = box.getText();
    tr.setText(textContent);

    const pars = tr.getParagraphs();
    if (pars.length > 0) {
      pars[0].getRange().getTextStyle()
        .setFontFamily('Arial').setFontSize(9.5 * sy).setBold(true).setForegroundColor(titleCol || COLOR_PRIMARY);
    }
    if (subtitle && pars.length > 1) {
      pars[1].getRange().getTextStyle()
        .setFontFamily('Arial').setFontSize(8 * sy).setBold(true).setForegroundColor(COLOR_MUTED);
    }
    if (descriptor && pars.length > 2) {
      pars[2].getRange().getTextStyle()
        .setFontFamily('Arial').setFontSize(7.5 * sy).setBold(false).setForegroundColor(COLOR_DARK);
    }
    return box;
  }

  // Helper: Draw Descriptive Directional Arrow with Flow Label
  function addDetailedArrow(x1, y1, x2, y2, color, label, labelDx, labelDy, isDashed) {
    const line = slide.insertLine(SlidesApp.LineCategory.STRAIGHT, ptX(x1), ptY(y1), ptX(x2), ptY(y2));
    line.setTitle('MEDQUAD_LINE');
    line.getLineFill().setSolidFill(color || COLOR_PRIMARY);
    line.setWeight(1.5);
    line.setEndArrow(SlidesApp.ArrowStyle.FILL_ARROW);
    if (isDashed) line.setDashStyle(SlidesApp.DashStyle.DASH);

    if (label) {
      const midX = (x1 + x2) / 2 + (labelDx || 0);
      const midY = (y1 + y2) / 2 + (labelDy || -15);
      const tb = slide.insertTextBox(label, ptX(midX - 70), ptY(midY), ptW(140), ptH(14));
      tb.setTitle('MEDQUAD_LABEL');
      tb.getText().getTextStyle()
        .setFontFamily('Arial').setFontSize(6.8 * sy).setBold(true).setForegroundColor(color || COLOR_PRIMARY);
    }
    return line;
  }

  // Helper: Draw Orthogonal (Stepped) Arrow with Flow Label
  function addDetailedOrthoArrow(x1, y1, x2, y2, color, label, labelXOffset) {
    const midY = (y1 + y2) / 2;
    const l1 = slide.insertLine(SlidesApp.LineCategory.STRAIGHT, ptX(x1), ptY(y1), ptX(x1), ptY(midY));
    l1.setTitle('MEDQUAD_LINE').getLineFill().setSolidFill(color);
    l1.setWeight(1.5);

    const l2 = slide.insertLine(SlidesApp.LineCategory.STRAIGHT, ptX(x1), ptY(midY), ptX(x2), ptY(midY));
    l2.setTitle('MEDQUAD_LINE').getLineFill().setSolidFill(color);
    l2.setWeight(1.5);

    const l3 = slide.insertLine(SlidesApp.LineCategory.STRAIGHT, ptX(x2), ptY(midY), ptX(x2), ptY(y2));
    l3.setTitle('MEDQUAD_LINE').getLineFill().setSolidFill(color);
    l3.setWeight(1.5);
    l3.setEndArrow(SlidesApp.ArrowStyle.FILL_ARROW);

    if (label) {
      const tb = slide.insertTextBox(label, ptX((x1 + x2) / 2 - 120 + (labelXOffset || 0)), ptY(midY - 14), ptW(240), ptH(14));
      tb.setTitle('MEDQUAD_LABEL');
      tb.getText().getTextStyle()
        .setFontFamily('Arial').setFontSize(6.8 * sy).setBold(true).setForegroundColor(color);
    }
  }

  // =========================================================================
  // SLIDE HEADER (Action Title & Tracker)
  // =========================================================================
  const headerBox = slide.insertTextBox(
    'SYSTEM ARCHITECTURE\nMulti-Agent ADK Architecture Decouples Retrieval, Synthesis, and Verification',
    ptX(45), ptY(25), ptW(870), ptH(55)
  );
  headerBox.setTitle('MEDQUAD_HEADER');
  const hPars = headerBox.getText().getParagraphs();
  if (hPars.length > 0) hPars[0].getRange().getTextStyle().setFontFamily('Arial').setFontSize(9 * sy).setBold(true).setForegroundColor(COLOR_PRIMARY);
  if (hPars.length > 1) hPars[1].getRange().getTextStyle().setFontFamily('Arial').setFontSize(16 * sy).setBold(true).setForegroundColor(COLOR_DARK);

  const div = slide.insertLine(SlidesApp.LineCategory.STRAIGHT, ptX(45), ptY(86), ptX(915), ptY(86));
  div.setTitle('MEDQUAD_DIVIDER').getLineFill().setSolidFill(COLOR_BORDER);

  // =========================================================================
  // TIER 1: INGRESS & PERIMETER SECURITY GATEWAY
  // =========================================================================
  const c1 = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE, ptX(45), ptY(95), ptW(870), ptH(88));
  c1.setTitle('MEDQUAD_CONTAINER').getFill().setSolidFill(COLOR_CARD);
  c1.getBorder().getLineFill().setSolidFill(COLOR_BORDER);
  c1.getText().setText('1. INGRESS & PERIMETER DEFENSE');
  c1.getText().getParagraphs()[0].getRange().getTextStyle().setFontFamily('Arial').setFontSize(7 * sy).setBold(true).setForegroundColor(COLOR_MUTED);

  // 1. Clinician Portal
  addCleanBox(55, 115, 100, 58, 'Clinician UI', 'Web & REST API', 'HTTPS / SSE streaming', COLOR_PRIMARY, COLOR_BLUE_BG, COLOR_PRIMARY);
  // Arrow: Client -> Cloud Armor
  addDetailedArrow(155, 144, 205, 144, COLOR_PRIMARY, '1. HTTPS Inquiry', 0, -14);

  // 2. Cloud Armor
  addCleanBox(205, 115, 100, 58, 'Cloud Armor', 'L7 WAF & DDoS', 'Rate & bot filtering', COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY);
  // Arrow: Cloud Armor -> Cloud Run
  addDetailedArrow(305, 144, 355, 144, COLOR_PRIMARY, '2. Clean Traffic', 0, -14);

  // 3. Cloud Run Gateway
  addCleanBox(355, 115, 110, 58, 'Cloud Run Gateway', 'FastAPI Microservice', 'Auth & session state', COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY);
  // Arrow: Cloud Run -> Model Armor
  addDetailedArrow(465, 144, 515, 144, COLOR_PRIMARY, '3. Auth Payload', 0, -14);

  // 4. Model Armor Guardrail
  addCleanBox(515, 115, 115, 58, 'Model Armor', 'Layer 8 Guardrail', 'HIPAA PHI & Jailbreak', COLOR_PRIMARY, COLOR_CARD, COLOR_PRIMARY);
  // Arrow: Model Armor -> Safe Refusal Exit
  addDetailedArrow(630, 144, 680, 144, COLOR_RED, '4a. Safe Refusal (<5ms)', 0, -14);

  // 5. Safe Refusal Exit
  addCleanBox(680, 115, 225, 58, 'Safe Refusal Engine Exit', 'Personal Advice & Dosing Block', 'Returns ER disclaimer | Zero tokens', COLOR_RED, COLOR_RED_BG, COLOR_RED);

  // Stepped Arrow: Model Armor down to Root Orchestrator
  addDetailedOrthoArrow(572, 173, 160, 205, COLOR_GREEN, '4b. Sanitized Query (18 HIPAA PHI Identifiers Scrubbed)', 15);

  // =========================================================================
  // TIER 2: GOOGLE ADK MULTI-AGENT CORE
  // =========================================================================
  const c2 = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE, ptX(45), ptY(195), ptW(870), ptH(168));
  c2.setTitle('MEDQUAD_CONTAINER').getFill().setSolidFill(COLOR_CARD);
  c2.getBorder().getLineFill().setSolidFill(COLOR_PRIMARY);
  c2.getBorder().setWeight(1.5);
  c2.getText().setText('2. GOOGLE ADK MULTI-AGENT CORE (DECOUPLED SUPERVISOR-WORKER PATTERN)');
  c2.getText().getParagraphs()[0].getRange().getTextStyle().setFontFamily('Arial').setFontSize(7 * sy).setBold(true).setForegroundColor(COLOR_PRIMARY);

  // Agent 1: Root Orchestrator
  addCleanBox(55, 215, 210, 138, 'Root Orchestrator', 'Supervisor | Gemini 2.5 Flash', '• Intent classification & policy routing\n• max_iterations=2 safety loop ceiling\n• Top-level conversation session state', COLOR_PRIMARY, COLOR_CARD, COLOR_PRIMARY);

  // Arrow: Orchestrator -> Clinical Researcher
  addDetailedArrow(265, 284, 340, 284, COLOR_PRIMARY, '5. Research Intent + Loop Guard (max_iter=2)', 0, -14);

  // Agent 2: Clinical Researcher
  addCleanBox(340, 215, 235, 138, 'Clinical Researcher', 'Worker | Gemini 2.5 Pro', '• Deep biomedical literature reasoning\n• Multi-source synthesis across NIH\n• Drafts response with [1], [2] citations', COLOR_PRIMARY, COLOR_CARD, COLOR_PRIMARY);

  // Arrow: Clinical Researcher -> Reviewer & QC Gate
  addDetailedArrow(575, 284, 650, 284, COLOR_PRIMARY, '8. Draft Response with [1],[2] Anchors', 0, -14);

  // Agent 3: Reviewer & QC Gate
  addCleanBox(650, 215, 255, 138, 'Reviewer & QC Gate', 'Auditor | Gemini 3.5 Flash', '• Zero shared state (eliminates bias)\n• CitationVerifier: 100% chunk match\n• Approves verified streaming release', COLOR_GREEN, COLOR_CARD, COLOR_GREEN);

  // =========================================================================
  // TIER 3: GROUNDING DATA & OBSERVABILITY SINK
  // =========================================================================
  const c3 = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE, ptX(45), ptY(375), ptW(870), ptH(120));
  c3.setTitle('MEDQUAD_CONTAINER').getFill().setSolidFill(COLOR_CARD);
  c3.getBorder().getLineFill().setSolidFill(COLOR_BORDER);
  c3.getText().setText('3. GROUNDING DATA STORES & OBSERVABILITY SINK');
  c3.getText().getParagraphs()[0].getRange().getTextStyle().setFontFamily('Arial').setFontSize(7 * sy).setBold(true).setForegroundColor(COLOR_MUTED);

  // Store 1: Vertex AI Search
  addCleanBox(55, 395, 200, 90, 'Vertex AI Search', 'NIH Literature Datastore', '16,400+ verified medical Q&A pairs\n500-token chunks with 10% overlap', COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY);

  // Store 2: ClinicalDBTool
  addCleanBox(270, 395, 200, 90, 'ClinicalDBTool', 'Biomarker Reference DB', 'Diagnostic reference ranges &\nclinical lab test thresholds', COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY);

  // Store 3: In-Memory Vector Fallback
  addCleanBox(485, 395, 195, 90, 'Vector DB Fallback', 'Circuit Breaker Store', 'Local FAISS in-memory index\nSub-50ms fallback on 504 timeouts', COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY);

  // Store 4: Cloud Trace & BigQuery
  addCleanBox(695, 395, 210, 90, 'Cloud Trace & BigQuery', 'Observability & Audit Sink', 'OpenTelemetry distributed spans &\nnightly continuous evaluation logs', COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY);

  // Vertical Arrows: Researcher <-> Grounding Layer
  // 6. Query (Down)
  addDetailedArrow(420, 353, 420, 395, COLOR_PRIMARY, '6. Hybrid Dense+Lexical Query', 70, -4);
  // 7. Chunks (Up)
  addDetailedArrow(485, 395, 485, 353, COLOR_PRIMARY, '7. Top-K NIH Evidence Chunks', 70, 4);

  // Telemetry Connector (Dashed)
  addDetailedArrow(785, 353, 785, 395, COLOR_MUTED, 'Async OTel Traces & Cost Logs', 75, 0, true);

  // Presenter Notes
  slide.getNotesPage().getSpeakerNotesShape().getText().setText(
    "Slide 4 displays the concrete architecture diagram showing the visual flow across components:\n\n" +
    "1. Ingress & Perimeter: Clinician queries enter via Cloud Armor and FastAPI on Cloud Run. Model Armor scrubs 18 HIPAA PHI identifiers.\n\n" +
    "2. Safe Refusal Branch: If personal medical advice or dosing is detected, it exits in <5ms without model token consumption.\n\n" +
    "3. Multi-Agent Orchestration: Root Orchestrator (Gemini 2.5 Flash) routes to Clinical Researcher (Gemini 2.5 Pro).\n\n" +
    "4. Grounding: Researcher retrieves 500-token chunks from Vertex AI Search and queries ClinicalDBTool.\n\n" +
    "5. Independent Verification: Reviewer & QC gate (Gemini 3.5 Flash) audits 100% citation ID matching before streaming release.\n\n" +
    "6. Observability: Spans are sent to Cloud Trace, and telemetry is logged to BigQuery."
  );

  Logger.log('Successfully drew updated architecture diagram on slide: ' + slide.getObjectId());
}
