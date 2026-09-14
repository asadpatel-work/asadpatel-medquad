/**
 * MedQuAD Clinical Research Assistant - Google Apps Script
 *
 * This script uses the native Google Slides API (SlidesApp) to draw the
 * complete Multi-Agent Architecture Diagram directly on Slide id: h66d1b35f290be7cc_11_38
 * (or the currently selected slide).
 *
 * HOW TO RUN:
 * 1. Open your presentation: https://docs.google.com/presentation/d/1cdBc40xSexQXZ3GtXyOKMgSwuobGbfWX8sRn46Jr6cU/edit
 * 2. In Google Slides, click: Extensions -> Apps Script
 * 3. Delete any default code in Code.gs, paste this entire script, and click "Save" (Ctrl+S / Cmd+S).
 * 4. Select "drawArchitectureDiagram" in the function dropdown and click "Run".
 * 5. Grant permissions when prompted. The architecture diagram with all 39 boxes,
 *    containers, and directional arrows will be drawn directly onto your slide!
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

  // 3. Proportional scaling based on 960 x 540 reference canvas
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
  const COLOR_CARD = '#FFFFFF';     // White
  const COLOR_BLUE_BG = '#E8F0FE';  // Soft Blue
  const COLOR_RED_BG = '#FEF2F2';   // Soft Red
  const COLOR_RED = '#EA4335';      // Google Red
  const COLOR_GREEN = '#34A853';    // Google Green

  // Helper: Draw Component Box
  function addBox(x, y, w, h, title, subtitle, bullets, borderCol, fillCol, titleCol, isRounded) {
    const shapeType = isRounded ? SlidesApp.ShapeType.ROUND_RECTANGLE : SlidesApp.ShapeType.RECTANGLE;
    const box = slide.insertShape(shapeType, ptX(x), ptY(y), ptW(w), ptH(h));
    box.setTitle('MEDQUAD_BOX');
    box.getFill().setSolidFill(fillCol || COLOR_CARD);
    box.getBorder().getLineFill().setSolidFill(borderCol || COLOR_BORDER);
    box.getBorder().setWeight(borderCol === COLOR_PRIMARY || borderCol === COLOR_GREEN ? 1.5 : 1);

    const tr = box.getText();
    let textContent = title;
    if (subtitle) textContent += '\n' + subtitle;
    if (bullets && bullets.length > 0) {
      textContent += '\n• ' + bullets.join('\n• ');
    }
    tr.setText(textContent);

    // Format paragraphs
    const pars = tr.getParagraphs();
    if (pars.length > 0) {
      pars[0].getRange().getTextStyle()
        .setFontFamily('Arial')
        .setFontSize(9 * sy)
        .setBold(true)
        .setForegroundColor(titleCol || COLOR_PRIMARY);
    }
    if (subtitle && pars.length > 1) {
      pars[1].getRange().getTextStyle()
        .setFontFamily('Arial')
        .setFontSize(7.5 * sy)
        .setBold(true)
        .setForegroundColor(COLOR_MUTED);
    }
    const bulletStart = subtitle ? 2 : 1;
    for (let i = bulletStart; i < pars.length; i++) {
      pars[i].getRange().getTextStyle()
        .setFontFamily('Arial')
        .setFontSize(7.5 * sy)
        .setBold(false)
        .setForegroundColor(COLOR_DARK);
    }
    return box;
  }

  // Helper: Draw Arrow Connector
  function addArrow(x1, y1, x2, y2, color, label, isDashed) {
    const line = slide.insertLine(SlidesApp.LineCategory.STRAIGHT, ptX(x1), ptY(y1), ptX(x2), ptY(y2));
    line.setTitle('MEDQUAD_LINE');
    line.getLineFill().setSolidFill(color || COLOR_PRIMARY);
    line.setWeight(1.5);
    line.setEndArrow(SlidesApp.ArrowStyle.FILL_ARROW);
    if (isDashed) {
      line.setDashStyle(SlidesApp.DashStyle.DASH);
    }

    if (label) {
      const midX = (x1 + x2) / 2;
      const midY = (y1 + y2) / 2;
      const tb = slide.insertTextBox(label, ptX(midX - 45), ptY(midY - 14), ptW(90), ptH(14));
      tb.setTitle('MEDQUAD_LABEL');
      tb.getText().getTextStyle()
        .setFontFamily('Arial')
        .setFontSize(7 * sy)
        .setBold(true)
        .setForegroundColor(color || COLOR_PRIMARY);
    }
    return line;
  }

  // Helper: Draw Orthogonal (Stepped) Arrow
  function addOrthoArrow(x1, y1, x2, y2, color, label) {
    const midY = (y1 + y2) / 2;
    const l1 = slide.insertLine(SlidesApp.LineCategory.STRAIGHT, ptX(x1), ptY(y1), ptX(x1), ptY(midY));
    l1.setTitle('MEDQUAD_LINE');
    l1.getLineFill().setSolidFill(color);
    l1.setWeight(1.5);

    const l2 = slide.insertLine(SlidesApp.LineCategory.STRAIGHT, ptX(x1), ptY(midY), ptX(x2), ptY(midY));
    l2.setTitle('MEDQUAD_LINE');
    l2.getLineFill().setSolidFill(color);
    l2.setWeight(1.5);

    const l3 = slide.insertLine(SlidesApp.LineCategory.STRAIGHT, ptX(x2), ptY(midY), ptX(x2), ptY(y2));
    l3.setTitle('MEDQUAD_LINE');
    l3.getLineFill().setSolidFill(color);
    l3.setWeight(1.5);
    l3.setEndArrow(SlidesApp.ArrowStyle.FILL_ARROW);

    if (label) {
      const tb = slide.insertTextBox(label, ptX((x1 + x2) / 2 - 80), ptY(midY - 14), ptW(160), ptH(14));
      tb.setTitle('MEDQUAD_LABEL');
      tb.getText().getTextStyle()
        .setFontFamily('Arial')
        .setFontSize(7 * sy)
        .setBold(true)
        .setForegroundColor(color);
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
  if (hPars.length > 0) {
    hPars[0].getRange().getTextStyle()
      .setFontFamily('Arial')
      .setFontSize(9 * sy)
      .setBold(true)
      .setForegroundColor(COLOR_PRIMARY);
  }
  if (hPars.length > 1) {
    hPars[1].getRange().getTextStyle()
      .setFontFamily('Arial')
      .setFontSize(16 * sy)
      .setBold(true)
      .setForegroundColor(COLOR_DARK);
  }

  // Divider Line
  const div = slide.insertLine(SlidesApp.LineCategory.STRAIGHT, ptX(45), ptY(88), ptX(915), ptY(88));
  div.setTitle('MEDQUAD_DIVIDER');
  div.getLineFill().setSolidFill(COLOR_BORDER);
  div.setWeight(1);

  // =========================================================================
  // TIER 1: PERIMETER & INGRESS GATEWAY
  // =========================================================================
  const c1 = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE, ptX(45), ptY(98), ptW(870), ptH(90));
  c1.setTitle('MEDQUAD_CONTAINER');
  c1.getFill().setSolidFill(COLOR_CARD);
  c1.getBorder().getLineFill().setSolidFill(COLOR_BORDER);
  c1.getText().setText('1. INGRESS & PERIMETER SECURITY GATEWAY');
  c1.getText().getParagraphs()[0].getRange().getTextStyle()
    .setFontFamily('Arial').setFontSize(7.5 * sy).setBold(true).setForegroundColor(COLOR_MUTED);

  // 1. Clinician UI
  addBox(55, 116, 105, 62, 'Clinician / UI', 'Web App & REST', ['HTTPS / SSE', 'Inline Citations'], COLOR_PRIMARY, COLOR_BLUE_BG, COLOR_PRIMARY, true);
  // Arrow: Client -> Cloud Armor
  addArrow(160, 147, 190, 147, COLOR_PRIMARY, '1. Query');

  // 2. Cloud Armor
  addBox(190, 116, 110, 62, 'Cloud Armor', 'L7 WAF & DDoS', ['IP Throttling', 'Bot Defense'], COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY, true);
  // Arrow: Cloud Armor -> Cloud Run
  addArrow(300, 147, 330, 147, COLOR_PRIMARY, '2. Clean');

  // 3. Cloud Run Gateway
  addBox(330, 116, 120, 62, 'Cloud Run Gateway', 'FastAPI Backend', ['Auth Token Check', 'Streaming SSE'], COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY, true);
  // Arrow: Cloud Run -> Model Armor
  addArrow(450, 147, 480, 147, COLOR_PRIMARY, '3. Ingest');

  // 4. Model Armor Guardrail
  addBox(480, 116, 145, 62, 'Model Armor', 'Layer 8 Guardrail', ['18 HIPAA PHI De-id', 'Injection Filter'], COLOR_PRIMARY, COLOR_CARD, COLOR_PRIMARY, true);
  // Arrow: Model Armor -> Safe Refusal Exit
  addArrow(625, 147, 660, 147, COLOR_RED, 'Refusal (<5ms)');

  // 5. Safe Refusal Exit
  addBox(660, 116, 245, 62, 'Safe Refusal Engine Exit', 'Boundary Lock: Diagnosis & Rx Dosing', ['Returns emergency disclaimer', 'Zero LLM tokens spent'], COLOR_RED, COLOR_RED_BG, COLOR_RED, true);

  // Orthogonal Arrow: Model Armor down to Root Orchestrator
  addOrthoArrow(552, 178, 165, 208, COLOR_GREEN, '4. Valid Inquiry (Sanitized Query)');

  // =========================================================================
  // TIER 2: GOOGLE ADK MULTI-AGENT CORE
  // =========================================================================
  const c2 = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE, ptX(45), ptY(198), ptW(870), ptH(175));
  c2.setTitle('MEDQUAD_CONTAINER');
  c2.getFill().setSolidFill(COLOR_CARD);
  c2.getBorder().getLineFill().setSolidFill(COLOR_PRIMARY);
  c2.getBorder().setWeight(1.5);
  c2.getText().setText('2. GOOGLE ADK MULTI-AGENT CORE (SUPERVISOR-WORKER DECOUPLED TOPOLOGY)');
  c2.getText().getParagraphs()[0].getRange().getTextStyle()
    .setFontFamily('Arial').setFontSize(7.5 * sy).setBold(true).setForegroundColor(COLOR_PRIMARY);

  // Agent 1: Root Orchestrator
  addBox(55, 218, 220, 145, 'Root Orchestrator', 'Supervisor | Gemini 2.5 Flash', [
    'Classifies clinical intent & domain',
    'SafeRefusalEngine policy routing',
    'Enforces max_iterations=2 loop ceiling',
    'Maintains conversation context state'
  ], COLOR_PRIMARY, COLOR_CARD, COLOR_PRIMARY, true);

  // Arrow: Orchestrator -> Researcher
  addArrow(275, 290, 335, 290, COLOR_PRIMARY, '5. Route');

  // Agent 2: Clinical Researcher
  addBox(335, 218, 250, 145, 'Clinical Researcher', 'Worker | Gemini 2.5 Pro', [
    'Deep biomedical literature reasoning',
    'Executes semantic search over NIH data',
    'Queries lab test reference ranges',
    'Drafts synthesis with inline [1],[2] tags'
  ], COLOR_PRIMARY, COLOR_CARD, COLOR_PRIMARY, true);

  // Arrow: Researcher -> Reviewer
  addArrow(585, 290, 645, 290, COLOR_PRIMARY, '8. Draft');

  // Agent 3: Reviewer & QC Gate
  addBox(645, 218, 260, 145, 'Reviewer & QC Gate', 'Auditor | Gemini 3.5 Flash', [
    'Zero shared hidden state (prevents bias)',
    'CitationVerifier: 100% chunk ID match',
    'Strips ungrounded/hallucinated claims',
    'Approves verified response release'
  ], COLOR_GREEN, COLOR_CARD, COLOR_GREEN, true);

  // =========================================================================
  // TIER 3: GROUNDING DATA STORES & OBSERVABILITY
  // =========================================================================
  const c3 = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE, ptX(45), ptY(383), ptW(870), ptH(120));
  c3.setTitle('MEDQUAD_CONTAINER');
  c3.getFill().setSolidFill(COLOR_CARD);
  c3.getBorder().getLineFill().setSolidFill(COLOR_BORDER);
  c3.getText().setText('3. GROUNDING DATA STORES & OBSERVABILITY SINK');
  c3.getText().getParagraphs()[0].getRange().getTextStyle()
    .setFontFamily('Arial').setFontSize(7.5 * sy).setBold(true).setForegroundColor(COLOR_MUTED);

  // Store 1: Vertex AI Search
  addBox(55, 403, 200, 88, 'Vertex AI Search', 'Authoritative Literature Datastore', [
    '16,400+ NIH Q&A pairs indexed',
    '500-token semantic chunks (10% ovlp)'
  ], COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY, true);

  // Store 2: ClinicalDBTool
  addBox(270, 403, 195, 88, 'ClinicalDBTool', 'Structured Reference Database', [
    'Lab test reference ranges',
    'Diagnostic biomarker thresholds'
  ], COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY, true);

  // Store 3: In-Memory Vector DB Fallback
  addBox(480, 403, 200, 88, 'Vector DB Fallback', 'Circuit Breaker Redundancy', [
    'Local FAISS in-memory store',
    'Sub-50ms fallback on 504 timeouts'
  ], COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY, true);

  // Store 4: Cloud Trace & BigQuery
  addBox(695, 403, 210, 88, 'Cloud Trace & BigQuery', 'Observability & Quality Sink', [
    'OpenTelemetry distributed spans',
    'Nightly automated evaluation audits'
  ], COLOR_BORDER, COLOR_CARD, COLOR_PRIMARY, true);

  // Inter-tier Connectors between Researcher & Grounding:
  // 6. Query (Down)
  addArrow(410, 363, 410, 403, COLOR_PRIMARY, '6. Query');
  // 7. Chunks (Up)
  addArrow(465, 403, 465, 363, COLOR_PRIMARY, '7. Chunks');

  // Telemetry Connector (Dashed)
  addArrow(800, 363, 800, 403, COLOR_MUTED, 'Telemetry', true);

  // Presenter Notes
  slide.getNotesPage().getSpeakerNotesShape().getText().setText(
    "Slide 4 displays the concrete architecture diagram showing the visual flow across components:\n\n" +
    "1. Ingress & Perimeter: Clinician queries enter via Cloud Armor and FastAPI on Cloud Run. Model Armor performs Layer 8 guardrails—scrubbing 18 HIPAA Safe Harbor identifiers and filtering jailbreak injections.\n\n" +
    "2. Safe Refusal Branch: If the user asks for personal medical advice or dosing, the Safe Refusal Engine exits in under 5ms without invoking model tokens.\n\n" +
    "3. Multi-Agent Orchestration: If valid, the query passes to the Root Orchestrator (Gemini 2.5 Flash), which classifies intent and routes to the Clinical Researcher (Gemini 2.5 Pro).\n\n" +
    "4. Grounding: The Researcher retrieves 500-token chunks from Vertex AI Search (with fallback to an in-memory vector store) and fetches lab ranges via ClinicalDBTool, synthesizing an evidence draft with inline citation tags.\n\n" +
    "5. Independent Verification: The Reviewer & QC agent (Gemini 3.5 Flash) operates with zero shared state. Its CitationVerifier audits every single citation bracket against retrieved chunk IDs. Only 100% verified responses are streamed back to the client.\n\n" +
    "6. Observability: Every span is traced to Cloud Trace, and telemetry is recorded in BigQuery for continuous auditing."
  );

  Logger.log('Successfully drew architecture diagram on slide: ' + slide.getObjectId());
}
