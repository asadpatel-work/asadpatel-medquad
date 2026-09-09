"""Mock Clinical Database and Reference Tool.

Simulates electronic health record (EHR) reference databases, lab normal ranges,
and NIH clinical trial protocol criteria with defensive retry and rate-limiting resilience.
"""

from __future__ import annotations

import json
import logging
import random
from typing import Any

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

logger = logging.getLogger(__name__)


class ClinicalQueryType:
    LAB_REFERENCE = "lab_reference"
    TRIAL_PROTOCOL = "trial_protocol"
    DRUG_INTERACTION = "drug_interaction"


# Mock reference databases
LAB_REFERENCE_RANGES: dict[str, dict[str, Any]] = {
    "hba1c": {
        "test_name": "Hemoglobin A1c (HbA1c)",
        "normal_range": "< 5.7%",
        "prediabetes_range": "5.7% - 6.4%",
        "diabetes_diagnostic": ">= 6.5%",
        "units": "%",
        "guideline_source": "ADA / NIDDK 2026 Standards of Care",
    },
    "esr": {
        "test_name": "Erythrocyte Sedimentation Rate (Westergren)",
        "normal_range_male": "0 - 15 mm/hr",
        "normal_range_female": "0 - 20 mm/hr",
        "clinical_significance": "Elevated (>50 mm/hr) in Hodgkin Lymphoma, systemic inflammation, and temporal arteritis.",
        "units": "mm/hr",
        "guideline_source": "NIH Clinical Center Laboratory Reference Manual",
    },
    "lactate": {
        "test_name": "Serum Lactate (Venous/Arterial)",
        "normal_range": "0.5 - 2.0 mmol/L",
        "sepsis_warning": "> 2.0 mmol/L",
        "sepsis_critical_bundle": ">= 4.0 mmol/L (Mandates 30 mL/kg rapid fluid resuscitation)",
        "units": "mmol/L",
        "guideline_source": "Surviving Sepsis Campaign / NIGMS 2026",
    },
    "troponin": {
        "test_name": "High-Sensitivity Cardiac Troponin T (hs-cTnT)",
        "normal_range": "< 14 ng/L",
        "myocardial_infarction_cutoff": ">= 52 ng/L (or delta change >= 5 ng/L in 1 hr)",
        "units": "ng/L",
        "guideline_source": "ACC/AHA/ESC Consensus Guidelines",
    },
}

TRIAL_PROTOCOLS: dict[str, dict[str, Any]] = {
    "NCI-2026-HL01": {
        "protocol_id": "NCI-2026-HL01",
        "title": "Phase III Trial of Targeted Immunotherapy (Brentuximab Vedotin + AVD) in Stage II-IV Hodgkin Lymphoma",
        "lead_organization": "National Cancer Institute (NCI)",
        "phase": "Phase 3",
        "eligibility_criteria": [
            "Histologically confirmed CD30+ classical Hodgkin lymphoma",
            "Age >= 18 years and <= 75 years",
            "ECOG performance status 0-2",
            "No prior systemic chemotherapy or radiotherapy for lymphoma",
            "Adequate baseline renal and hepatic function (Creatinine <= 1.5x ULN, Bilirubin <= 1.5x ULN)",
        ],
        "primary_endpoint": "Progression-Free Survival (PFS) at 24 months",
    },
    "NIH-NIDDK-DM02": {
        "protocol_id": "NIH-NIDDK-DM02",
        "title": "Evaluation of SGLT2i and GLP-1RA Dual Therapy on Renal Outcomes in Early Stage Diabetic Nephropathy",
        "lead_organization": "National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)",
        "phase": "Phase 2b",
        "eligibility_criteria": [
            "Documented Type 2 Diabetes Mellitus with HbA1c between 7.0% and 10.5%",
            "eGFR between 30 and 90 mL/min/1.73m2",
            "Urine Albumin-to-Creatinine Ratio (UACR) >= 300 mg/g",
            "Stable dose of ACE inhibitor or ARB for >= 4 weeks prior to screening",
        ],
        "primary_endpoint": "Rate of eGFR decline slope over 104 weeks",
    },
}

DRUG_INTERACTIONS: dict[str, dict[str, Any]] = {
    "lisinopril": {
        "drug_name": "Lisinopril (ACE Inhibitor)",
        "major_interactions": [
            "Potassium supplements / Spironolactone (Risk of severe hyperkalemia)",
            "NSAIDs (ibuprofen, naproxen) (Attenuates antihypertensive effect, accelerates renal impairment)",
            "Lithium (Increases serum lithium toxicity)",
        ],
        "contraindications": [
            "History of ACE inhibitor-induced angioedema",
            "Pregnancy (Black Box Warning)",
        ],
    },
    "temozolomide": {
        "drug_name": "Temozolomide (Alkylating Chemotherapy)",
        "major_interactions": [
            "Valproic acid (Decreases oral clearance of temozolomide by ~5%)",
            "Live vaccines (Severe immunosuppression risk)",
        ],
        "contraindications": [
            "Severe myelosuppression (Absolute Neutrophil Count < 1.5 x 10^9/L, Platelets < 100 x 10^9/L)"
        ],
    },
}


class TransientDatabaseError(Exception):
    """Raised to simulate transient network connectivity or rate limit failures."""

    pass


class ClinicalDBTool:
    """Mock Clinical Reference Database with retry and exponential backoff resilience."""

    @retry(
        retry=retry_if_exception_type(TransientDatabaseError),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.1, max=1.0),
        reraise=True,
    )
    def query_lab_reference(
        self, test_name: str, simulate_flakiness: bool = False
    ) -> dict[str, Any]:
        """Queries standardized reference ranges for medical laboratory tests."""
        if simulate_flakiness and random.random() < 0.2:
            raise TransientDatabaseError("Transient connection timeout to Mock Clinical DB")

        normalized = test_name.strip().lower()
        for key, data in LAB_REFERENCE_RANGES.items():
            if key in normalized or normalized in key:
                return {"status": "found", "data": data}

        return {
            "status": "not_found",
            "message": f"Lab reference for '{test_name}' not found. Available tests: {list(LAB_REFERENCE_RANGES.keys())}",
        }

    @retry(
        retry=retry_if_exception_type(TransientDatabaseError),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.1, max=1.0),
        reraise=True,
    )
    def query_trial_protocol(self, query: str, simulate_flakiness: bool = False) -> dict[str, Any]:
        """Queries active NIH clinical trial protocols and eligibility criteria."""
        if simulate_flakiness and random.random() < 0.2:
            raise TransientDatabaseError("Transient connection timeout to Mock Clinical DB")

        normalized = query.strip().upper()
        # Direct key match
        if normalized in TRIAL_PROTOCOLS:
            return {"status": "found", "data": TRIAL_PROTOCOLS[normalized]}

        # Substring/title match
        for _proto_id, data in TRIAL_PROTOCOLS.items():
            if normalized in data["title"].upper() or query.lower() in data["title"].lower():
                return {"status": "found", "data": data}

        return {
            "status": "not_found",
            "message": f"Trial protocol for '{query}' not found. Available protocols: {list(TRIAL_PROTOCOLS.keys())}",
        }

    def query_drug_info(self, drug_name: str) -> dict[str, Any]:
        """Queries drug interactions and contraindications."""
        normalized = drug_name.strip().lower()
        for key, data in DRUG_INTERACTIONS.items():
            if key in normalized or normalized in key:
                return {"status": "found", "data": data}

        return {
            "status": "not_found",
            "message": f"Drug data for '{drug_name}' not found. Available drugs: {list(DRUG_INTERACTIONS.keys())}",
        }


# Convenience function for ADK Tool registration
def clinical_db_lookup_tool(query_type: str, lookup_key: str) -> str:
    """Tool function: Queries clinical laboratory reference ranges, trial protocols, or drug interactions.

    Args:
        query_type: One of 'lab_reference', 'trial_protocol', or 'drug_interaction'.
        lookup_key: Name of the lab test (e.g. 'HbA1c', 'ESR', 'Lactate'), protocol ID (e.g. 'NCI-2026-HL01'), or drug name (e.g. 'Lisinopril').

    Returns:
        JSON string containing structured clinical reference data.
    """
    db_tool = ClinicalDBTool()
    q_type = query_type.strip().lower()

    if "lab" in q_type:
        result = db_tool.query_lab_reference(lookup_key)
    elif "trial" in q_type or "protocol" in q_type:
        result = db_tool.query_trial_protocol(lookup_key)
    elif "drug" in q_type:
        result = db_tool.query_drug_info(lookup_key)
    else:
        result = {
            "status": "invalid_query_type",
            "error": f"Invalid query_type '{query_type}'. Must be 'lab_reference', 'trial_protocol', or 'drug_interaction'.",
        }

    return json.dumps(result, indent=2)
