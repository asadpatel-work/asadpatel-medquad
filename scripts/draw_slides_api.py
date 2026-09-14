"""Direct Google Slides REST API Drawing Script.

Calls the Google Slides REST API (presentations.batchUpdate) to draw
the complete visual architecture diagram directly on a target slide.

Usage:
    # 1. With token argument:
    python scripts/draw_slides_api.py --token "<ACCESS_TOKEN>"

    # 2. Or using gcloud access token:
    python scripts/draw_slides_api.py --token "$(gcloud auth print-access-token)"

    # 3. Using custom presentation / slide ID:
    python scripts/draw_slides_api.py --token "<TOKEN>" \
        --presentation-id "1cdBc40xSexQXZ3GtXyOKMgSwuobGbfWX8sRn46Jr6cU" \
        --slide-id "h66d1b35f290be7cc_11_38"
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

PRESENTATION_ID_DEFAULT = "1cdBc40xSexQXZ3GtXyOKMgSwuobGbfWX8sRn46Jr6cU"
SLIDE_ID_DEFAULT = "h66d1b35f290be7cc_11_38"

# Colors in 0.0 - 1.0 RGB format for Slides API
COLOR_PRIMARY = {"red": 0.102, "green": 0.451, "blue": 0.910}   # #1A73E8
COLOR_BORDER = {"red": 0.855, "green": 0.863, "blue": 0.878}    # #DADCE0
COLOR_DARK = {"red": 0.125, "green": 0.129, "blue": 0.141}      # #202124
COLOR_MUTED = {"red": 0.373, "green": 0.388, "blue": 0.408}     # #5F6368
COLOR_WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}           # #FFFFFF
COLOR_BLUE_BG = {"red": 0.910, "green": 0.941, "blue": 0.996}   # #E8F0FE
COLOR_RED_BG = {"red": 0.996, "green": 0.949, "blue": 0.949}    # #FEF2F2
COLOR_RED = {"red": 0.918, "green": 0.263, "blue": 0.208}       # #EA4335
COLOR_GREEN = {"red": 0.204, "green": 0.659, "blue": 0.325}     # #34A853


def build_batch_update_requests(slide_id: str) -> list[dict]:
    requests = []

    # Helper: Create shape
    def make_box(
        obj_id: str,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        subtitle: str = "",
        bullets: list[str] | None = None,
        shape_type: str = "ROUND_RECTANGLE",
        fill_color: dict | None = None,
        border_color: dict | None = None,
        title_color: dict | None = None,
    ):
        fill = fill_color or COLOR_WHITE
        border = border_color or COLOR_BORDER
        t_col = title_color or COLOR_PRIMARY

        requests.append({
            "createShape": {
                "objectId": obj_id,
                "shapeType": shape_type,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"width": {"magnitude": w, "unit": "PT"}, "height": {"magnitude": h, "unit": "PT"}},
                    "transform": {
                        "scaleX": 1, "scaleY": 1,
                        "translateX": x, "translateY": y,
                        "unit": "PT"
                    }
                }
            }
        })
        requests.append({
            "updateShapeProperties": {
                "objectId": obj_id,
                "fields": "shapeBackgroundFill.solidFill.color,outline.outlineFill.solidFill.color,outline.weight",
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": fill}}},
                    "outline": {
                        "outlineFill": {"solidFill": {"color": {"rgbColor": border}}},
                        "weight": {"magnitude": 1.2, "unit": "PT"}
                    }
                }
            }
        })

        text = title
        if subtitle:
            text += f"\n{subtitle}"
        if bullets:
            text += "\n• " + "\n• ".join(bullets)

        requests.append({
            "insertText": {
                "objectId": obj_id,
                "insertionIndex": 0,
                "text": text
            }
        })
        # Style title
        requests.append({
            "updateTextStyle": {
                "objectId": obj_id,
                "textRange": {"type": "FIXED_RANGE", "startIndex": 0, "endIndex": len(title)},
                "fields": "bold,fontSize,foregroundColor,fontFamily",
                "style": {
                    "bold": True,
                    "fontSize": {"magnitude": 9, "unit": "PT"},
                    "fontFamily": "Arial",
                    "foregroundColor": {"opaqueColor": {"rgbColor": t_col}}
                }
            }
        })

    # Helper: Create Line
    def make_line(obj_id: str, x1: float, y1: float, x2: float, y2: float, color: dict | None = None, is_dashed: bool = False):
        col = color or COLOR_PRIMARY
        requests.append({
            "createLine": {
                "objectId": obj_id,
                "lineCategory": "STRAIGHT",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"width": {"magnitude": max(abs(x2 - x1), 1), "unit": "PT"}, "height": {"magnitude": max(abs(y2 - y1), 1), "unit": "PT"}},
                    "transform": {
                        "scaleX": 1, "scaleY": 1,
                        "translateX": min(x1, x2), "translateY": min(y1, y2),
                        "unit": "PT"
                    }
                }
            }
        })
        line_props = {
            "lineFill": {"solidFill": {"color": {"rgbColor": col}}},
            "weight": {"magnitude": 1.5, "unit": "PT"},
            "endArrow": "FILL_ARROW"
        }
        if is_dashed:
            line_props["dashStyle"] = "DASH"
        requests.append({
            "updateLineProperties": {
                "objectId": obj_id,
                "fields": "lineFill.solidFill.color,weight,endArrow" + (",dashStyle" if is_dashed else ""),
                "lineProperties": line_props
            }
        })

    # Helper: Create Label
    def make_label(obj_id: str, x: float, y: float, w: float, h: float, text: str, color: dict | None = None):
        col = color or COLOR_PRIMARY
        requests.append({
            "createShape": {
                "objectId": obj_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"width": {"magnitude": w, "unit": "PT"}, "height": {"magnitude": h, "unit": "PT"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": x, "translateY": y, "unit": "PT"}
                }
            }
        })
        requests.append({"insertText": {"objectId": obj_id, "insertionIndex": 0, "text": text}})
        requests.append({
            "updateTextStyle": {
                "objectId": obj_id,
                "textRange": {"type": "ALL"},
                "fields": "bold,fontSize,foregroundColor,fontFamily",
                "style": {
                    "bold": True,
                    "fontSize": {"magnitude": 7, "unit": "PT"},
                    "fontFamily": "Arial",
                    "foregroundColor": {"opaqueColor": {"rgbColor": col}}
                }
            }
        })

    # --- Header ---
    make_label("hdr_title", 45, 25, 870, 50, "SYSTEM ARCHITECTURE\nMulti-Agent ADK Architecture Decouples Retrieval, Synthesis, and Verification", COLOR_DARK)

    # --- Container 1: Ingress ---
    make_box("c1_ingress", 45, 95, 870, 90, "1. INGRESS & PERIMETER SECURITY GATEWAY", shape_type="ROUND_RECTANGLE", border_color=COLOR_BORDER, title_color=COLOR_MUTED)
    make_box("b1_ui", 55, 115, 105, 60, "Clinician / UI", "Web App & REST", ["HTTPS / SSE", "Inline Citations"], fill_color=COLOR_BLUE_BG, border_color=COLOR_PRIMARY)
    make_line("arr_1", 160, 145, 190, 145)
    make_label("lbl_1", 160, 132, 40, 14, "1. Query")

    make_box("b2_waf", 190, 115, 110, 60, "Cloud Armor", "L7 WAF & DDoS", ["IP Throttling", "Bot Defense"])
    make_line("arr_2", 300, 145, 330, 145)
    make_label("lbl_2", 300, 132, 40, 14, "2. Clean")

    make_box("b3_gwy", 330, 115, 120, 60, "Cloud Run Gateway", "FastAPI Backend", ["Auth Token Check", "Streaming SSE"])
    make_line("arr_3", 450, 145, 480, 145)
    make_label("lbl_3", 450, 132, 40, 14, "3. Ingest")

    make_box("b4_ma", 480, 115, 145, 60, "Model Armor", "Layer 8 Guardrail", ["18 HIPAA PHI De-id", "Injection Filter"], border_color=COLOR_PRIMARY)
    make_line("arr_4a", 625, 145, 660, 145, color=COLOR_RED)
    make_label("lbl_4a", 620, 132, 60, 14, "Refusal (<5ms)", COLOR_RED)

    make_box("b5_ref", 660, 115, 245, 60, "Safe Refusal Engine Exit", "Boundary Lock: Diagnosis & Rx Dosing", ["Returns emergency disclaimer", "Zero LLM tokens spent"], fill_color=COLOR_RED_BG, border_color=COLOR_RED, title_color=COLOR_RED)

    # --- Container 2: Agents ---
    make_box("c2_agents", 45, 195, 870, 175, "2. GOOGLE ADK MULTI-AGENT CORE (SUPERVISOR-WORKER DECOUPLED TOPOLOGY)", shape_type="ROUND_RECTANGLE", border_color=COLOR_PRIMARY, title_color=COLOR_PRIMARY)
    make_box("b6_orch", 55, 215, 220, 145, "Root Orchestrator", "Supervisor | Gemini 2.5 Flash", ["Classifies clinical intent & domain", "SafeRefusalEngine policy routing", "Enforces max_iterations=2 loop ceiling", "Maintains conversation context"], border_color=COLOR_PRIMARY)
    make_line("arr_5", 275, 287, 335, 287)
    make_label("lbl_5", 285, 275, 50, 14, "5. Route")

    make_box("b7_res", 335, 215, 250, 145, "Clinical Researcher", "Worker | Gemini 2.5 Pro", ["Deep biomedical literature reasoning", "Executes semantic search over NIH data", "Queries lab test reference ranges", "Drafts synthesis with inline [1],[2] tags"], border_color=COLOR_PRIMARY)
    make_line("arr_8", 585, 287, 645, 287)
    make_label("lbl_8", 595, 275, 50, 14, "8. Draft")

    make_box("b8_rev", 645, 215, 260, 145, "Reviewer & QC Gate", "Auditor | Gemini 3.5 Flash", ["Zero shared hidden state (prevents bias)", "CitationVerifier: 100% chunk ID match", "Strips ungrounded/hallucinated claims", "Approves verified response release"], border_color=COLOR_GREEN, title_color=COLOR_GREEN)

    # --- Container 3: Grounding & Observability ---
    make_box("c3_ground", 45, 380, 870, 120, "3. GROUNDING DATA STORES & OBSERVABILITY SINK", shape_type="ROUND_RECTANGLE", border_color=COLOR_BORDER, title_color=COLOR_MUTED)
    make_box("b9_vsearch", 55, 400, 200, 90, "Vertex AI Search", "Authoritative Literature Datastore", ["16,400+ NIH Q&A pairs indexed", "500-token semantic chunks (10% ovlp)"])
    make_box("b10_cdb", 270, 400, 195, 90, "ClinicalDBTool", "Structured Reference Database", ["Lab test reference ranges", "Diagnostic biomarker thresholds"])
    make_box("b11_faiss", 480, 400, 200, 90, "Vector DB Fallback", "Circuit Breaker Redundancy", ["Local FAISS in-memory store", "Sub-50ms fallback on 504 timeouts"])
    make_box("b12_obs", 695, 400, 210, 90, "Cloud Trace & BigQuery", "Observability & Quality Sink", ["OpenTelemetry distributed spans", "Nightly automated evaluation audits"])

    # Inter-tier arrows
    make_line("arr_6", 410, 360, 410, 400)
    make_label("lbl_6", 412, 375, 50, 14, "6. Query")
    make_line("arr_7", 465, 400, 465, 360)
    make_label("lbl_7", 467, 375, 50, 14, "7. Chunks")
    make_line("arr_tel", 800, 360, 800, 400, color=COLOR_MUTED, is_dashed=True)
    make_label("lbl_tel", 805, 375, 60, 14, "Telemetry", COLOR_MUTED)

    return requests


def execute_batch_update(presentation_id: str, slide_id: str, access_token: str):
    requests = build_batch_update_requests(slide_id)
    url = f"https://slides.googleapis.com/v1/presentations/{presentation_id}:batchUpdate"
    payload = json.dumps({"requests": requests}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"Successfully executed batchUpdate! Responses count: {len(data.get('replies', []))}")
            print(f"Diagram drawn on slide: https://docs.google.com/presentation/d/{presentation_id}/edit#slide=id.{slide_id}")
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.reason}", file=sys.stderr)
        print(e.read().decode(), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Draw architecture diagram using Google Slides API")
    parser.add_argument("--token", required=True, help="Google OAuth access token with slides scope")
    parser.add_argument("--presentation-id", default=PRESENTATION_ID_DEFAULT, help="Target Google Presentation ID")
    parser.add_argument("--slide-id", default=SLIDE_ID_DEFAULT, help="Target Slide Object ID")
    args = parser.parse_args()

    execute_batch_update(args.presentation_id, args.slide_id, args.token)
