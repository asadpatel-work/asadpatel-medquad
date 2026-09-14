"""Direct Google Slides REST API Drawing Script.

Calls the Google Slides REST API (presentations.batchUpdate) to draw
the minimal-box, detailed-arrow architecture diagram directly on a target slide.

Usage:
    python scripts/draw_slides_api.py --token "<ACCESS_TOKEN>"
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

    def make_clean_box(
        obj_id: str,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        subtitle: str = "",
        descriptor: str = "",
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
                        "weight": {"magnitude": 1.5 if border in (COLOR_PRIMARY, COLOR_GREEN, COLOR_RED) else 1.0, "unit": "PT"}
                    }
                }
            }
        })

        text = title
        if subtitle:
            text += f"\n{subtitle}"
        if descriptor:
            text += f"\n{descriptor}"

        requests.append({"insertText": {"objectId": obj_id, "insertionIndex": 0, "text": text}})
        requests.append({
            "updateTextStyle": {
                "objectId": obj_id,
                "textRange": {"type": "FIXED_RANGE", "startIndex": 0, "endIndex": len(title)},
                "fields": "bold,fontSize,foregroundColor,fontFamily",
                "style": {
                    "bold": True,
                    "fontSize": {"magnitude": 9.5, "unit": "PT"},
                    "fontFamily": "Arial",
                    "foregroundColor": {"opaqueColor": {"rgbColor": t_col}}
                }
            }
        })

    def make_detailed_arrow(obj_id: str, x1: float, y1: float, x2: float, y2: float, color: dict | None = None, label: str = "", label_dx: float = 0.0, label_dy: float = -14.0, is_dashed: bool = False):
        col = color or COLOR_PRIMARY
        requests.append({
            "createLine": {
                "objectId": obj_id,
                "lineCategory": "STRAIGHT",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"width": {"magnitude": max(abs(x2 - x1), 1), "unit": "PT"}, "height": {"magnitude": max(abs(y2 - y1), 1), "unit": "PT"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": min(x1, x2), "translateY": min(y1, y2), "unit": "PT"}
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

        if label:
            mid_x = (x1 + x2) / 2 + label_dx
            mid_y = (y1 + y2) / 2 + label_dy
            lbl_id = f"lbl_{obj_id}"
            requests.append({
                "createShape": {
                    "objectId": lbl_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {"width": {"magnitude": 140, "unit": "PT"}, "height": {"magnitude": 14, "unit": "PT"}},
                        "transform": {"scaleX": 1, "scaleY": 1, "translateX": mid_x - 70, "translateY": mid_y, "unit": "PT"}
                    }
                }
            })
            requests.append({"insertText": {"objectId": lbl_id, "insertionIndex": 0, "text": label}})
            requests.append({
                "updateTextStyle": {
                    "objectId": lbl_id,
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor,fontFamily",
                    "style": {
                        "bold": True,
                        "fontSize": {"magnitude": 6.8, "unit": "PT"},
                        "fontFamily": "Arial",
                        "foregroundColor": {"opaqueColor": {"rgbColor": col}}
                    }
                }
            })

    # Header
    requests.append({
        "createShape": {
            "objectId": "hdr_title",
            "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": slide_id,
                "size": {"width": {"magnitude": 870, "unit": "PT"}, "height": {"magnitude": 50, "unit": "PT"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 45, "translateY": 25, "unit": "PT"}
            }
        }
    })
    requests.append({"insertText": {"objectId": "hdr_title", "insertionIndex": 0, "text": "SYSTEM ARCHITECTURE\nMulti-Agent ADK Architecture Decouples Retrieval, Synthesis, and Verification"}})

    # Row 1: Ingress
    make_clean_box("c1_ingress", 45, 95, 870, 88, "1. INGRESS & PERIMETER DEFENSE", title_color=COLOR_MUTED)
    make_clean_box("b1_ui", 55, 115, 100, 58, "Clinician UI", "Web & REST API", "HTTPS / SSE streaming", fill_color=COLOR_BLUE_BG, border_color=COLOR_PRIMARY)
    make_detailed_arrow("arr_1", 155, 144, 205, 144, label="1. HTTPS Inquiry")

    make_clean_box("b2_waf", 205, 115, 100, 58, "Cloud Armor", "L7 WAF & DDoS", "Rate & bot filtering")
    make_detailed_arrow("arr_2", 305, 144, 355, 144, label="2. Clean Traffic")

    make_clean_box("b3_gwy", 355, 115, 110, 58, "Cloud Run Gateway", "FastAPI Microservice", "Auth & session state")
    make_detailed_arrow("arr_3", 465, 144, 515, 144, label="3. Auth Payload")

    make_clean_box("b4_ma", 515, 115, 115, 58, "Model Armor", "Layer 8 Guardrail", "HIPAA PHI & Jailbreak", border_color=COLOR_PRIMARY)
    make_detailed_arrow("arr_4a", 630, 144, 680, 144, color=COLOR_RED, label="4a. Safe Refusal (<5ms)")

    make_clean_box("b5_ref", 680, 115, 225, 58, "Safe Refusal Engine Exit", "Personal Advice & Dosing Block", "Returns ER disclaimer | Zero tokens", fill_color=COLOR_RED_BG, border_color=COLOR_RED, title_color=COLOR_RED)

    # Row 2: Agents
    make_clean_box("c2_agents", 45, 195, 870, 168, "2. GOOGLE ADK MULTI-AGENT CORE (DECOUPLED SUPERVISOR-WORKER PATTERN)", border_color=COLOR_PRIMARY, title_color=COLOR_PRIMARY)
    make_clean_box("b6_orch", 55, 215, 210, 138, "Root Orchestrator", "Supervisor | Gemini 2.5 Flash", "• Intent classification & policy routing\n• max_iterations=2 loop ceiling\n• Top-level conversation session state", border_color=COLOR_PRIMARY)
    make_detailed_arrow("arr_5", 265, 284, 340, 284, label="5. Research Intent + Loop Guard (max_iter=2)")

    make_clean_box("b7_res", 340, 215, 235, 138, "Clinical Researcher", "Worker | Gemini 2.5 Pro", "• Deep biomedical literature reasoning\n• Multi-source synthesis across NIH\n• Drafts response with [1],[2] citations", border_color=COLOR_PRIMARY)
    make_detailed_arrow("arr_8", 575, 284, 650, 284, label="8. Draft Response with [1],[2] Anchors")

    make_clean_box("b8_rev", 650, 215, 255, 138, "Reviewer & QC Gate", "Auditor | Gemini 3.5 Flash", "• Zero shared state (eliminates bias)\n• CitationVerifier: 100% chunk match\n• Approves verified streaming release", border_color=COLOR_GREEN, title_color=COLOR_GREEN)

    # Row 3: Grounding
    make_clean_box("c3_ground", 45, 375, 870, 120, "3. GROUNDING DATA STORES & OBSERVABILITY SINK", border_color=COLOR_BORDER, title_color=COLOR_MUTED)
    make_clean_box("b9_vsearch", 55, 395, 200, 90, "Vertex AI Search", "NIH Literature Datastore", "16,400+ verified medical Q&A pairs\n500-token chunks with 10% overlap")
    make_clean_box("b10_cdb", 270, 395, 200, 90, "ClinicalDBTool", "Biomarker Reference DB", "Diagnostic reference ranges &\nclinical lab test thresholds")
    make_clean_box("b11_faiss", 485, 395, 195, 90, "Vector DB Fallback", "Circuit Breaker Store", "Local FAISS in-memory index\nSub-50ms fallback on 504 timeouts")
    make_clean_box("b12_obs", 695, 395, 210, 90, "Cloud Trace & BigQuery", "Observability & Audit Sink", "OpenTelemetry distributed spans &\nnightly continuous evaluation logs")

    # Inter-tier arrows
    make_detailed_arrow("arr_6", 420, 353, 420, 395, label="6. Hybrid Dense+Lexical Query", label_dx=45, label_dy=-4)
    make_detailed_arrow("arr_7", 485, 395, 485, 353, label="7. Top-K NIH Evidence Chunks", label_dx=45, label_dy=4)
    make_detailed_arrow("arr_tel", 785, 353, 785, 395, color=COLOR_MUTED, label="Async OTel Traces & Cost Logs", label_dx=50, label_dy=0, is_dashed=True)

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
