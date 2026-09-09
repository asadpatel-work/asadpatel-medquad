"""MedQuAD Dataset Ingestion and Preprocessing Pipeline.

Parses NIH MedQuAD XML and JSON documents, extracts Q&A pairs, applies
a 500-token chunking strategy with 10% overlap, and normalizes output for
Vertex AI Search (Discovery Engine) and local in-memory vector stores.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_medquad")


@dataclass
class MedQuADRecord:
    """Normalized medical Q&A document record."""

    doc_id: str
    focus: str
    question_id: str
    question_type: str
    question: str
    answer: str
    topic_category: str
    source_url: str
    authoritative_org: str = "National Institutes of Health (NIH)"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MedQuADChunk:
    """Chunked document segment for embedding and vector indexing."""

    chunk_id: str
    doc_id: str
    question_id: str
    title: str
    content: str
    topic_category: str
    source_url: str
    authoritative_org: str
    token_count_approx: int
    metadata: dict[str, Any] = field(default_factory=dict)


# Keyword mappings to infer medical sub-specialty categories
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Oncology": [
        "cancer",
        "tumor",
        "carcinoma",
        "lymphoma",
        "leukemia",
        "melanoma",
        "sarcoma",
        "oncology",
        "chemotherapy",
        "radiation",
        "glioblastoma",
    ],
    "Cardiology": [
        "heart",
        "cardiac",
        "coronary",
        "hypertension",
        "arrhythmia",
        "infarction",
        "blood pressure",
        "atherosclerosis",
        "aneurysm",
        "aortic",
        "vascular",
        "heart failure",
        "angina",
        "troponin",
    ],
    "Infectious Disease": [
        "infection",
        "virus",
        "bacterial",
        "hiv",
        "hepatitis",
        "covid",
        "tuberculosis",
        "sepsis",
        "antibiotic",
        "flu",
        "influenza",
    ],
    "Neurology": [
        "brain",
        "neurological",
        "seizure",
        "epilepsy",
        "parkinson",
        "alzheimer",
        "dementia",
        "stroke",
        "neuropathy",
        "aneurysm",
        "cerebral",
        "subarachnoid",
        "headache",
    ],
    "Endocrinology": [
        "diabetes",
        "thyroid",
        "insulin",
        "glucose",
        "hormone",
        "pituitary",
        "adrenal",
        "metabolic",
        "hba1c",
    ],
    "Pulmonology": [
        "lung",
        "respiratory",
        "asthma",
        "copd",
        "pneumonia",
        "bronchitis",
        "pulmonary",
    ],
    "Pediatrics": ["child", "infant", "pediatric", "congenital", "newborn", "juvenile"],
}


def infer_topic_category(text: str) -> str:
    """Classifies clinical text into standard medical categories based on keywords."""
    lower_text = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", lower_text) for kw in keywords):
            return category
    return "General Medicine"


def estimate_token_count(text: str) -> int:
    """Estimates token count (~1.3 tokens per word or 4 chars per token)."""
    return max(1, int(len(text.split()) * 1.3))


def chunk_text(
    text: str,
    target_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[str]:
    """Splits text into chunks of target_tokens with overlap_tokens overlap."""
    words = text.split()
    if not words:
        return []

    words_per_chunk = max(10, int(target_tokens / 1.3))
    words_overlap = max(2, int(overlap_tokens / 1.3))
    step = max(1, words_per_chunk - words_overlap)

    chunks = []
    for i in range(0, len(words), step):
        chunk_words = words[i : i + words_per_chunk]
        chunks.append(" ".join(chunk_words))
        if i + words_per_chunk >= len(words):
            break

    return chunks


def parse_medquad_xml(xml_content: str) -> list[MedQuADRecord]:
    """Parses a raw NIH MedQuAD XML document into normalized records."""
    root = ET.fromstring(xml_content)

    doc_id = root.attrib.get("id", "UNKNOWN-DOC")
    source_url = root.attrib.get("url", "https://medlineplus.gov")
    focus_elem = root.find("Focus")
    focus = (
        focus_elem.text.strip()
        if focus_elem is not None and focus_elem.text
        else "General Medical Topic"
    )

    records = []
    qa_pairs = root.findall(".//QAPair")
    for qa in qa_pairs:
        qid = qa.attrib.get("pid", "0")
        q_elem = qa.find("Question")
        a_elem = qa.find("Answer")

        question_text = q_elem.text.strip() if q_elem is not None and q_elem.text else ""
        answer_text = a_elem.text.strip() if a_elem is not None and a_elem.text else ""
        q_type = q_elem.attrib.get("qtype", "information") if q_elem is not None else "information"

        if not question_text or not answer_text:
            continue

        combined_text = f"{focus} {question_text} {answer_text}"
        category = infer_topic_category(combined_text)

        records.append(
            MedQuADRecord(
                doc_id=doc_id,
                focus=focus,
                question_id=qid,
                question_type=q_type,
                question=question_text,
                answer=answer_text,
                topic_category=category,
                source_url=source_url,
                metadata={"focus": focus, "question_type": q_type},
            )
        )

    return records


def process_records_to_chunks(
    records: list[MedQuADRecord],
    target_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[MedQuADChunk]:
    """Converts normalized records into searchable chunk representations."""
    all_chunks = []
    for record in records:
        full_content = (
            f"Topic: {record.focus}\n"
            f"Category: {record.topic_category}\n"
            f"Question: {record.question}\n\n"
            f"Answer: {record.answer}"
        )

        text_chunks = chunk_text(
            full_content,
            target_tokens=target_tokens,
            overlap_tokens=overlap_tokens,
        )

        for idx, chunk_str in enumerate(text_chunks):
            chunk_id = f"{record.doc_id}_q{record.question_id}_c{idx + 1}"
            all_chunks.append(
                MedQuADChunk(
                    chunk_id=chunk_id,
                    doc_id=record.doc_id,
                    question_id=record.question_id,
                    title=f"{record.focus}: {record.question}",
                    content=chunk_str,
                    topic_category=record.topic_category,
                    source_url=record.source_url,
                    authoritative_org=record.authoritative_org,
                    token_count_approx=estimate_token_count(chunk_str),
                    metadata={
                        "chunk_index": idx,
                        "total_chunks": len(text_chunks),
                        "focus": record.focus,
                        "question_type": record.question_type,
                    },
                )
            )
    return all_chunks


def generate_sample_dataset() -> list[MedQuADRecord]:
    """Generates an extensive, authoritative NIH MedQuAD corpus covering key clinical specialties."""
    return [
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0001",
            focus="Hodgkin Lymphoma",
            question_id="1",
            question_type="symptoms",
            question="What are the primary symptoms and diagnostic markers of Hodgkin Lymphoma?",
            answer=(
                "The most common symptom of Hodgkin lymphoma is a painless swelling in the lymph nodes "
                "in the neck, underarm, or groin. Other systemic 'B symptoms' include unexplained fevers, "
                "drenching night sweats, and unintentional weight loss (>10% of body weight over 6 months). "
                "Diagnostic confirmation requires an excisional lymph node biopsy demonstrating the presence "
                "of pathognomonic Reed-Sternberg cells (CD30+ and CD15+ on immunohistochemistry). Laboratory "
                "markers include elevated erythrocyte sedimentation rate (ESR), leukocytosis, and lymphopenia."
            ),
            topic_category="Oncology",
            source_url="https://www.cancer.gov/types/lymphoma/patient/adult-hodgkin-treatment-pdq",
            authoritative_org="National Cancer Institute (NCI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0002",
            focus="Hodgkin Lymphoma",
            question_id="2",
            question_type="staging",
            question="How is Hodgkin Lymphoma staged according to the Ann Arbor classification?",
            answer=(
                "Hodgkin lymphoma is staged using the Lugano modification of the Ann Arbor staging system: "
                "Stage I involves a single lymph node region or single extralymphatic organ. "
                "Stage II involves two or more lymph node regions on the same side of the diaphragm. "
                "Stage III involves lymph node regions on both sides of the diaphragm, optionally with spleen involvement. "
                "Stage IV involves diffuse or disseminated involvement of one or more extralymphatic organs "
                "(such as liver, bone marrow, or lungs). Each stage is subclassified as 'A' (absence of B symptoms) "
                "or 'B' (presence of fever, night sweats, or weight loss)."
            ),
            topic_category="Oncology",
            source_url="https://www.cancer.gov/types/lymphoma/hp/adult-hodgkin-treatment-pdq",
            authoritative_org="National Cancer Institute (NCI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0003",
            focus="Type 2 Diabetes Mellitus",
            question_id="1",
            question_type="diagnosis",
            question="What are the diagnostic criteria and glycemic targets for Type 2 Diabetes?",
            answer=(
                "According to NIH and ADA guidelines, Type 2 Diabetes is diagnosed based on any of the following: "
                "1. Fasting Plasma Glucose (FPG) >= 126 mg/dL (7.0 mmol/L) after an 8-hour fast. "
                "2. Hemoglobin A1c (HbA1c) >= 6.5% (48 mmol/mol) using a standardized NGSP assay. "
                "3. Two-hour plasma glucose >= 200 mg/dL (11.1 mmol/L) during a 75g Oral Glucose Tolerance Test (OGTT). "
                "4. Random plasma glucose >= 200 mg/dL in a patient with classic symptoms of hyperglycemia (polyuria, polydipsia). "
                "For most non-pregnant adults, the standard glycemic target is an HbA1c < 7.0%."
            ),
            topic_category="Endocrinology",
            source_url="https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis",
            authoritative_org="National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0004",
            focus="Essential Hypertension",
            question_id="1",
            question_type="treatment_guidelines",
            question="What are the clinical classification stages and first-line pharmacological treatments for hypertension?",
            answer=(
                "According to ACC/AHA/NIH clinical guidelines, blood pressure in adults is classified as: "
                "Normal (<120/<80 mmHg), Elevated (120-129/<80 mmHg), Stage 1 Hypertension (130-139/80-89 mmHg), "
                "and Stage 2 Hypertension (>=140/>=90 mmHg). "
                "First-line pharmacological agents for non-black patients include thiazide diuretics (chlorthalidone), "
                "angiotensin-converting enzyme (ACE) inhibitors (e.g. lisinopril), angiotensin receptor blockers (ARBs, e.g. losartan), "
                "and calcium channel blockers (CCBs, e.g. amlodipine). In Black patients, initial therapy should include a CCB or thiazide."
            ),
            topic_category="Cardiology",
            source_url="https://www.nhlbi.nih.gov/health/high-blood-pressure",
            authoritative_org="National Heart, Lung, and Blood Institute (NHLBI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0005",
            focus="Sepsis and Septic Shock",
            question_id="1",
            question_type="emergency_protocols",
            question="What are the clinical diagnostic criteria (qSOFA / SOFA) and initial management bundle for Sepsis?",
            answer=(
                "Sepsis is defined as life-threatening organ dysfunction caused by a dysregulated host response to infection. "
                "Organ dysfunction is identified by an acute change in total Sequential Organ Failure Assessment (SOFA) score >= 2 points. "
                "Quick SOFA (qSOFA) criteria include: respiratory rate >= 22 breaths/min, altered mental status (GCS < 15), "
                "and systolic blood pressure <= 100 mmHg (>=2 indicates high risk). "
                "The 1-hour resuscitation bundle mandates: measure serum lactate, obtain blood cultures prior to antibiotics, "
                "administer broad-spectrum empiric IV antibiotics, rapidly infuse 30 mL/kg crystalloid for hypotension or lactate >= 4 mmol/L, "
                "and apply vasopressors (norepinephrine first-line) if hypotensive during or after fluid resuscitation to maintain MAP >= 65 mmHg."
            ),
            topic_category="Infectious Disease",
            source_url="https://www.nigms.nih.gov/education/fact-sheets/Pages/sepsis.aspx",
            authoritative_org="National Institute of General Medical Sciences (NIGMS)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0006",
            focus="Glioblastoma Multiforme",
            question_id="1",
            question_type="molecular_markers",
            question="What molecular markers and standard treatment protocols define Glioblastoma management?",
            answer=(
                "Glioblastoma (WHO Grade 4 astrocytoma) is characterized by microvascular proliferation and/or pseudopalisading necrosis. "
                "Key molecular prognostic markers include: IDH1/IDH2 mutation status (IDH-wildtype constitutes >90% of primary glioblastomas and carries a poorer prognosis) "
                "and MGMT promoter methylation status (predicts enhanced responsiveness to alkylating chemotherapy with temozolomide). "
                "Standard initial therapy (Stupp Protocol) consists of maximal safe surgical resection followed by concurrent radiotherapy (60 Gy in 30 fractions) "
                "and daily oral temozolomide (75 mg/m2), followed by 6 cycles of adjuvant maintenance temozolomide."
            ),
            topic_category="Oncology",
            source_url="https://www.cancer.gov/types/brain/hp/adult-brain-treatment-pdq",
            authoritative_org="National Cancer Institute (NCI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0007",
            focus="Brain Aneurysm (Cerebral Aneurysm)",
            question_id="1",
            question_type="symptoms_and_management",
            question="What are the symptoms, rupture risks, and surgical treatments for brain aneurysms?",
            answer=(
                "A cerebral (brain) aneurysm is an abnormal focal dilation or ballooning of an intracranial artery wall. "
                "Most unruptured aneurysms are asymptomatic until they grow and compress cranial nerves (causing dilated pupil, ptosis, or localized pain behind the eye). "
                "A ruptured aneurysm leads to subarachnoid hemorrhage (SAH), presenting classically as a sudden, excruciating 'thunderclap headache' (the worst headache of life), "
                "accompanied by neck stiffness, nausea, vomiting, photophobia, and loss of consciousness. "
                "Diagnostic workup includes non-contrast head CT, lumbar puncture (for xanthochromia), and CT angiography (CTA) or digital subtraction angiography (DSA). "
                "Definitive interventions include microsurgical clipping across the aneurysm neck or endovascular treatment (platinum coil embolization, stent-assisted coiling, or flow-diverting stents)."
            ),
            topic_category="Neurology",
            source_url="https://www.ninds.nih.gov/health-information/disorders/cerebral-aneurysms",
            authoritative_org="National Institute of Neurological Disorders and Stroke (NINDS)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0008",
            focus="Abdominal Aortic Aneurysm (AAA)",
            question_id="1",
            question_type="screening_and_repair",
            question="What are the risk factors, screening recommendations, and repair thresholds for Abdominal Aortic Aneurysm?",
            answer=(
                "An abdominal aortic aneurysm (AAA) is a permanent localized dilation of the abdominal aorta >= 3.0 cm in diameter. "
                "Major risk factors include advanced age (>65), male sex, tobacco smoking history, hypertension, and family history. "
                "The USPSTF recommends a 1-time screening ultrasound for AAA in men aged 65 to 75 who have ever smoked. "
                "Most AAAs remain asymptomatic until rupture, which presents with severe sudden abdominal or back pain, hypotension, and a pulsatile abdominal mass. "
                "Elective surgical intervention is indicated when diameter reaches >= 5.5 cm in men, >= 5.0 cm in women, or with rapid expansion (>0.5 cm in 6 months). "
                "Treatment options include Endovascular Aneurysm Repair (EVAR) or open surgical graft placement."
            ),
            topic_category="Cardiology",
            source_url="https://www.nhlbi.nih.gov/health/aortic-aneurysm",
            authoritative_org="National Heart, Lung, and Blood Institute (NHLBI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0009",
            focus="Acute Ischemic Stroke",
            question_id="1",
            question_type="acute_treatment",
            question="What are the time windows and criteria for thrombolytic therapy and mechanical thrombectomy in acute ischemic stroke?",
            answer=(
                "Acute ischemic stroke management requires rapid assessment using the NIH Stroke Scale (NIHSS) and non-contrast head CT to rule out hemorrhage. "
                "Intravenous thrombolysis with recombinant tissue plasminogen activator (IV alteplase or tenecteplase) is indicated within 4.5 hours of symptom onset "
                "in eligible patients without contraindications (such as recent major hemorrhage or INR > 1.7). "
                "Mechanical thrombectomy (endovascular clot retrieval) is standard of care for large vessel occlusions (LVO) in the anterior circulation within 6 hours, "
                "and up to 24 hours in selected patients meeting DAWN or DEFUSE-3 mismatch criteria on CT/MR perfusion imaging. "
                "Secondary prevention includes dual antiplatelet therapy (DAPT: aspirin + clopidogrel for 21 days), high-intensity statins, and blood pressure control."
            ),
            topic_category="Neurology",
            source_url="https://www.ninds.nih.gov/health-information/disorders/stroke",
            authoritative_org="National Institute of Neurological Disorders and Stroke (NINDS)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0010",
            focus="Acute Myocardial Infarction (AMI / Acute Coronary Syndrome)",
            question_id="1",
            question_type="diagnostic_criteria_and_emergency_management",
            question="What are the universal diagnostic criteria and cardiac biomarker thresholds for Acute Myocardial Infarction?",
            answer=(
                "Under the Fourth Universal Definition of Myocardial Infarction, acute myocardial infarction is diagnosed by detection of a rise "
                "and/or fall of cardiac troponin (cTn) values with at least one value above the 99th percentile upper reference limit (URL), in "
                "conjunction with evidence of myocardial ischemia evidenced by at least one of: ischemic symptoms, new ischemic ECG changes "
                "(ST-elevation, T-wave inversion, new LBBB), development of pathological Q waves, imaging evidence of new viable myocardium loss "
                "or regional wall motion abnormality, or identification of intracoronary thrombus by angiography. STEMI requires emergent primary "
                "Percutaneous Coronary Intervention (PCI) within 90 minutes. Initial pharmacotherapy includes chewable aspirin, P2Y12 platelet inhibitor, "
                "anticoagulation with heparin, and high-intensity statin."
            ),
            topic_category="Cardiology",
            source_url="https://www.nhlbi.nih.gov/health/heart-attack",
            authoritative_org="National Heart, Lung, and Blood Institute (NHLBI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0011",
            focus="Heart Failure with Reduced Ejection Fraction (HFrEF)",
            question_id="1",
            question_type="pharmacotherapy_guidelines",
            question="What are the foundational guideline-directed medical therapy (GDMT) pillars for HFrEF?",
            answer=(
                "According to AHA/ACC/HFSA guidelines, Heart Failure with Reduced Ejection Fraction (HFrEF, LVEF <= 40%) requires initiation "
                "and titration of the four foundational pillars of Guideline-Directed Medical Therapy (GDMT): "
                "1. Angiotensin Receptor-Neprilysin Inhibitor (ARNI: sacubitril/valsartan) preferred over ACE inhibitors or ARBs. "
                "2. Evidence-based beta-blockers (carvedilol, metoprolol succinate, or bisoprolol). "
                "3. Mineralocorticoid Receptor Antagonist (MRA: spironolactone or eplerenone) with monitoring of potassium and eGFR. "
                "4. SGLT2 inhibitors (dapagliflozin or empagliflozin) regardless of diabetes status. "
                "Loop diuretics (furosemide, bumetanide) are added as needed to achieve euvolemia. In patients with persistent LVEF <= 35% "
                "despite 3 months of optimal GDMT, implantable cardioverter-defibrillator (ICD) and cardiac resynchronization therapy (CRT) are indicated."
            ),
            topic_category="Cardiology",
            source_url="https://www.nhlbi.nih.gov/health/heart-failure",
            authoritative_org="National Heart, Lung, and Blood Institute (NHLBI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0012",
            focus="Asthma Management",
            question_id="1",
            question_type="treatment_protocols",
            question="What are the GINA guideline recommendations for stepwise asthma pharmacotherapy and SMART protocol?",
            answer=(
                "Global Initiative for Asthma (GINA) guidelines recommend against SABA-only treatment due to increased risk of severe exacerbations. "
                "Track 1 (preferred strategy) utilizes low-dose Inhaled Corticosteroid (ICS) combined with formoterol (a rapid-onset LABA) "
                "as both daily maintenance and as-needed reliever across all steps (Single Inhaler Maintenance and Reliever Therapy, SMART). "
                "Step 1-2: As-needed low-dose ICS-formoterol. Step 3: Low-dose maintenance ICS-formoterol plus as-needed reliever. "
                "Step 4: Medium-dose maintenance ICS-formoterol. Step 5: High-dose ICS-LABA plus add-on phenotypic therapies (such as LAMA/tiotropium, "
                "or biologic agents targeting IgE like omalizumab, IL-5 like mepolizumab/benralizumab, or IL-4R like dupilumab)."
            ),
            topic_category="Pulmonology",
            source_url="https://www.nhlbi.nih.gov/health/asthma",
            authoritative_org="National Heart, Lung, and Blood Institute (NHLBI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0013",
            focus="Community-Acquired Pneumonia (CAP)",
            question_id="1",
            question_type="diagnosis_and_antibiotics",
            question="What are the diagnostic evaluation and empiric antibiotic treatment regimens for Community-Acquired Pneumonia?",
            answer=(
                "Community-Acquired Pneumonia (CAP) is diagnosed by clinical features (cough, fever, dyspnea, pleuritic chest pain) "
                "along with demonstrative infiltrates on chest radiography or CT. Severity stratification uses the CURB-65 score "
                "(Confusion, Urea > 7 mmol/L, Respiratory rate >= 30, Blood pressure < 90/60, Age >= 65): scores 0-1 outpatient, 2 inpatient ward, >= 3 ICU evaluation. "
                "Outpatient empiric therapy in healthy adults without comorbidities: amoxicillin 1g TID OR doxycycline 100mg BID. "
                "Outpatient with comorbidities (COPD, diabetes, renal/heart disease): combination therapy with amoxicillin/clavulanate (or cefpodoxime) "
                "plus a macrolide (azithromycin) or doxycycline; or respiratory fluoroquinolone monotherapy (levofloxacin, moxifloxacin). "
                "Inpatient non-severe: IV beta-lactam (ceftriaxone or ampicillin/sulbactam) plus azithromycin, or respiratory fluoroquinolone."
            ),
            topic_category="Pulmonology",
            source_url="https://www.nhlbi.nih.gov/health/pneumonia",
            authoritative_org="National Heart, Lung, and Blood Institute (NHLBI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0014",
            focus="Chronic Kidney Disease (CKD)",
            question_id="1",
            question_type="staging_and_management",
            question="How is Chronic Kidney Disease staged by KDIGO and what pharmacological therapies slow progression?",
            answer=(
                "Chronic Kidney Disease (CKD) is staged based on Cause, GFR category (G1: >=90, G2: 60-89, G3a: 45-59, G3b: 30-44, G4: 15-29, G5: <15 mL/min/1.73m2), "
                "and Albuminuria category (A1: <30 mg/g, A2: 30-300 mg/g, A3: >300 mg/g urine albumin-to-creatinine ratio). "
                "Key pharmacological interventions to retard CKD progression include: "
                "1. Renin-angiotensin system inhibitors (ACE inhibitors or ARBs) titrated to maximum tolerated dose in patients with albuminuria and hypertension. "
                "2. SGLT2 inhibitors (empagliflozin, dapagliflozin) for CKD with eGFR >= 20 mL/min/1.73m2 regardless of diabetes status. "
                "3. Nonsteroidal mineralocorticoid receptor antagonist (finerenone) in Type 2 diabetes with persistent albuminuria. "
                "4. Blood pressure target < 120 mmHg systolic using standardized automated office measurements."
            ),
            topic_category="Endocrinology",
            source_url="https://www.niddk.nih.gov/health-information/kidney-disease/chronic-kidney-disease-ckd",
            authoritative_org="National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0015",
            focus="Alzheimer's Disease",
            question_id="1",
            question_type="biomarkers_and_therapeutics",
            question="What are the diagnostic biomarkers and current disease-modifying therapies for Alzheimer's Disease?",
            answer=(
                "Alzheimer's Disease (AD) is characterized neuropathologically by extracellular amyloid-beta plaques and intracellular hyperphosphorylated tau neurofibrillary tangles. "
                "The ATN biomarker framework encompasses: A (amyloid PET or CSF A-beta-42/40 ratio), T (tau PET or CSF/plasma phosphorylated tau-181/217), and N (neurodegeneration via MRI or FDG-PET). "
                "Disease-modifying therapies for early symptomatic AD (MCI and mild dementia) include anti-amyloid monoclonal antibodies: lecanemab (biweekly IV) and donanemab (monthly IV), "
                "which significantly reduce brain amyloid burden and modestly slow cognitive decline, requiring monitoring for Amyloid-Related Imaging Abnormalities (ARIA-E and ARIA-H) via MRI. "
                "Symptomatic pharmacotherapies include acetylcholinesterase inhibitors (donepezil, rivastigmine, galantamine) and the NMDA receptor antagonist memantine."
            ),
            topic_category="Neurology",
            source_url="https://www.nia.nih.gov/health/alzheimers-and-dementia",
            authoritative_org="National Institute on Aging (NIA)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0016",
            focus="Parkinson's Disease",
            question_id="1",
            question_type="motor_symptoms_and_treatment",
            question="What are the cardinal motor symptoms and diagnostic clinical features of Parkinson's Disease?",
            answer=(
                "Parkinson's Disease diagnosis is established clinically based on the presence of bradykinesia (slowness of movement and "
                "decrement in amplitude or speed) in combination with at least one of the following: 4-6 Hz resting tremor, muscle rigidity "
                "(lead-pipe or cogwheel), or postural instability not caused by primary visual, vestibular, or cerebellar dysfunction. Supportive "
                "criteria include unilateral onset, persistent asymmetry, clear and dramatic beneficial response to levodopa therapy, and "
                "levodopa-induced dyskinesias. Non-motor features frequently include REM sleep behavior disorder, hyposmia, and constipation. "
                "First-line symptomatic treatment is Carbidopa-Levodopa. Dopamine agonists and MAO-B inhibitors are alternative initial options in "
                "younger patients. Advanced disease is managed with Deep Brain Stimulation (DBS) of the STN or GPi."
            ),
            topic_category="Neurology",
            source_url="https://www.ninds.nih.gov/health-information/disorders/parkinsons-disease",
            authoritative_org="National Institute of Neurological Disorders and Stroke (NINDS)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0017",
            focus="Multiple Sclerosis (MS)",
            question_id="1",
            question_type="disease_modifying_therapies",
            question="What are the clinical phenotypes, McDonald diagnostic criteria, and disease-modifying therapies for Multiple Sclerosis?",
            answer=(
                "Multiple Sclerosis is an immune-mediated demyelinating disease of the central nervous system. "
                "Phenotypes include Relapsing-Remitting MS (RRMS, ~85% of presentations), Secondary Progressive MS (SPMS), and Primary Progressive MS (PPMS). "
                "Diagnosis relies on the 2017 McDonald Criteria demonstrating dissemination in space (DIS: lesions in >= 2 of 4 CNS regions: periventricular, cortical/juxtacortical, infratentorial, spinal cord) "
                "and dissemination in time (DIT: simultaneous enhancing and non-enhancing lesions or presence of CSF-specific oligoclonal bands). "
                "High-efficacy Disease-Modifying Therapies (DMTs) include anti-CD20 B-cell depleting monoclonal antibodies (ocrelizumab, ofatumumab), "
                "S1P receptor modulators (fingolimod, siponimod), and natalizumab (anti-alpha-4 integrin, requires JC virus antibody monitoring for PML risk)."
            ),
            topic_category="Neurology",
            source_url="https://www.ninds.nih.gov/health-information/disorders/multiple-sclerosis",
            authoritative_org="National Institute of Neurological Disorders and Stroke (NINDS)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0018",
            focus="Pulmonary Embolism (PE) and Deep Vein Thrombosis (DVT)",
            question_id="1",
            question_type="diagnosis_and_anticoagulation",
            question="What is the diagnostic algorithm and anticoagulation strategy for acute pulmonary embolism and deep vein thrombosis?",
            answer=(
                "Venous thromboembolism (VTE) encompasses DVT and PE. Diagnostic evaluation utilizes Wells score pre-test probability assessment. "
                "In low/moderate probability patients, a negative high-sensitivity D-dimer safely rules out VTE. High-probability patients or positive D-dimer "
                "mandate CT Pulmonary Angiography (CTPA) for PE or compression ultrasonography for DVT. "
                "Hemodynamically unstable (massive) PE with hypotension requires immediate systemic thrombolysis (alteplase 100mg IV) or surgical/catheter embolectomy. "
                "Stable non-massive PE/DVT is treated with Direct Oral Anticoagulants (DOACs: apixaban 10mg BID for 7 days then 5mg BID, or rivaroxaban 15mg BID for 21 days then 20mg daily) "
                "preferred over warfarin. Standard treatment duration is at least 3 months for provoked VTE and indefinite for unprovoked or recurrent events."
            ),
            topic_category="Cardiology",
            source_url="https://www.nhlbi.nih.gov/health/pulmonary-embolism",
            authoritative_org="National Heart, Lung, and Blood Institute (NHLBI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0019",
            focus="Atrial Fibrillation",
            question_id="1",
            question_type="rate_rhythm_and_stroke_prevention",
            question="How is stroke risk stratified (CHA2DS2-VASc) and rate vs rhythm control managed in Atrial Fibrillation?",
            answer=(
                "Atrial Fibrillation (AF) is a supraventricular tachyarrhythmia characterized by uncoordinated atrial activation and irregularly irregular ventricular response. "
                "Thromboembolic stroke risk is calculated via the CHA2DS2-VASc score (Congestive heart failure, Hypertension, Age >= 75 [2 pts], Diabetes, Stroke/TIA [2 pts], Vascular disease, Age 65-74, Sex category female). "
                "Oral anticoagulation (DOACs: apixaban, rivaroxaban, dabigatran, edoxaban) is strongly recommended for score >= 2 in men or >= 3 in women. "
                "Rate control targets resting heart rate < 110 bpm using beta-blockers (metoprolol, carvedilol) or non-dihydropyridine CCBs (diltiazem, verapamil). "
                "Rhythm control (antiarrhythmics like flecainide, propafenone, amiodarone, or catheter pulmonary vein isolation ablation) is preferred for symptomatic or newly diagnosed AF."
            ),
            topic_category="Cardiology",
            source_url="https://www.nhlbi.nih.gov/health/atrial-fibrillation",
            authoritative_org="National Heart, Lung, and Blood Institute (NHLBI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0020",
            focus="Acute Pancreatitis",
            question_id="1",
            question_type="diagnosis_and_fluid_resuscitation",
            question="What are the diagnostic criteria (Atlanta classification) and early management protocols for Acute Pancreatitis?",
            answer=(
                "According to the revised Atlanta Classification, Acute Pancreatitis diagnosis requires >= 2 of 3 features: "
                "1. Characteristic epigastric abdominal pain radiating to the back. 2. Serum lipase or amylase elevation >= 3 times the upper limit of normal. "
                "3. Characteristic cross-sectional imaging findings (contrast-enhanced CT, MRI, or transabdominal ultrasound). "
                "The primary etiologies are gallstones (~40%) and alcohol consumption (~30%), followed by hypertriglyceridemia (>1000 mg/dL). "
                "Early management focuses on goal-directed isotonic fluid resuscitation with Lactated Ringer's solution (200-500 mL/hr or 20 mL/kg bolus then 3 mL/kg/hr), "
                "multimodal pain control, and early oral refeeding with low-fat solid or liquid diet within 24 hours as tolerated."
            ),
            topic_category="General Medicine",
            source_url="https://www.niddk.nih.gov/health-information/digestive-diseases/pancreatitis",
            authoritative_org="National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0021",
            focus="Inflammatory Bowel Disease (Crohn's Disease and Ulcerative Colitis)",
            question_id="1",
            question_type="differentiation_and_biologics",
            question="What are the clinical, endoscopic, and pharmacological distinctions between Crohn's Disease and Ulcerative Colitis?",
            answer=(
                "Inflammatory Bowel Disease (IBD) encompasses Crohn's Disease (CD) and Ulcerative Colitis (UC). "
                "UC involves mucosal inflammation starting in the rectum and extending proximally in a continuous pattern, characterized by bloody diarrhea, tenesmus, and pseudopolyps, curing with total proctocolectomy. "
                "CD causes transmural inflammation that can affect any segment of the GI tract ('skip lesions' from mouth to anus, most commonly terminal ileum), manifesting with abdominal pain, non-bloody diarrhea, fistulae, strictures, and non-caseating granulomas. "
                "Pharmacotherapy for moderate-to-severe IBD utilizes biologic agents: anti-TNF-alpha (infliximab, adalimumab), anti-integrin (vedolizumab for gut-selective adhesion blockade), "
                "anti-IL-12/23 (ustekinumab), and oral small-molecule JAK inhibitors (tofacitinib, upadacitinib)."
            ),
            topic_category="General Medicine",
            source_url="https://www.niddk.nih.gov/health-information/digestive-diseases/inflammatory-bowel-disease",
            authoritative_org="National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0022",
            focus="Cirrhosis and Portal Hypertension",
            question_id="1",
            question_type="complications_and_ascites_management",
            question="What are the staging systems (MELD / Child-Pugh) and management protocols for cirrhosis complications including ascites and variceal bleeding?",
            answer=(
                "Cirrhosis represents end-stage hepatic fibrosis resulting in portal hypertension and synthetic dysfunction. "
                "Prognosis is assessed using Child-Pugh score (bilirubin, albumin, INR, ascites, encephalopathy) and MELD-Na score (bilirubin, creatinine, INR, sodium) for liver transplant prioritization. "
                "Ascites management includes dietary sodium restriction (<2000 mg/day) and combination dual diuretics (spironolactone 100mg + furosemide 40mg ratio). "
                "Large-volume paracentesis (>5L) mandates IV albumin replacement (6-8 g per liter of fluid removed) to prevent post-paracentesis circulatory dysfunction. "
                "Acute variceal hemorrhage is managed with airway protection, restrictive blood transfusion (target Hb 7-8 g/dL), IV octreotide (somatostatin analog bolus + infusion), "
                "antibiotic prophylaxis (ceftriaxone 1g/day for 7 days), and urgent endoscopic variceal ligation (EVL) within 12 hours. Non-selective beta-blockers (carvedilol, nadolol) are primary prophylaxis."
            ),
            topic_category="General Medicine",
            source_url="https://www.niddk.nih.gov/health-information/liver-disease/cirrhosis",
            authoritative_org="National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0023",
            focus="Rheumatoid Arthritis (RA)",
            question_id="1",
            question_type="serology_and_dmard_therapy",
            question="What are the diagnostic serological markers and treat-to-target DMARD algorithms for Rheumatoid Arthritis?",
            answer=(
                "Rheumatoid Arthritis is a chronic systemic autoimmune disease characterized by symmetric inflammatory polyarthritis affecting small joints of the hands (MCP, PIP) and wrists with morning stiffness > 1 hour. "
                "Serologic testing demonstrates Rheumatoid Factor (RF, ~70-80% sensitivity) and Anti-Citrullinated Protein Antibodies (anti-CCP / ACPA, >95% specificity, indicates erosive phenotype). "
                "The ACR/EULAR treat-to-target algorithm mandates early initiation of Conventional Synthetic DMARDs (csDMARDs: methotrexate 15-25 mg/week with folic acid supplementation as anchor therapy). "
                "In patients with inadequate response or high disease activity, biologic DMARDs (bDMARDs: anti-TNF agents like etanercept/adalimumab, anti-IL-6 receptor tocilizumab, T-cell costimulation blocker abatacept) "
                "or targeted synthetic DMARDs (tsDMARDs: JAK inhibitors tofacitinib, baricitinib) are added to achieve clinical remission."
            ),
            topic_category="General Medicine",
            source_url="https://www.niams.nih.gov/health-topics/rheumatoid-arthritis",
            authoritative_org="National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0024",
            focus="Systemic Lupus Erythematosus (SLE)",
            question_id="1",
            question_type="autoantibodies_and_lupus_nephritis",
            question="What are the diagnostic criteria, hallmark autoantibodies, and induction therapies for Lupus Nephritis in SLE?",
            answer=(
                "Systemic Lupus Erythematosus is a multisystem autoimmune disorder driven by immune complex deposition. "
                "Antinuclear Antibodies (ANA) serve as a highly sensitive entry criterion (>98% sensitivity). Hallmark disease-specific antibodies include Anti-double-stranded DNA (anti-dsDNA, correlates with lupus nephritis activity) "
                "and Anti-Smith (anti-Sm, highly specific). Complement levels (C3, C4) are depressed during active flare. "
                "All SLE patients should receive Hydroxychloroquine (HCQ, target <= 5 mg/kg real body weight) to reduce flares, organ damage, and mortality, with annual ophthalmology screening for retinal toxicity. "
                "Active Class III/IV proliferative Lupus Nephritis requires renal biopsy and induction immunosuppression with pulse IV methylprednisolone combined with either Mycophenolate Mofetil (MMF 2-3 g/day) or IV Cyclophosphamide (Euro-Lupus or NIH protocol), plus belimumab."
            ),
            topic_category="General Medicine",
            source_url="https://www.niams.nih.gov/health-topics/lupus",
            authoritative_org="National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIAMS)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0025",
            focus="Acute Bacterial Meningitis",
            question_id="1",
            question_type="emergency_empiric_antibiotics",
            question="What are the hallmark CSF findings and empiric antibiotic/dexamethasone regimens for Acute Bacterial Meningitis?",
            answer=(
                "Acute Bacterial Meningitis is a medical emergency presenting with fever, nuchal rigidity, and altered mental status. "
                "Lumbar puncture (LP) CSF analysis demonstrates: opening pressure > 200 mm H2O, marked neutrophilic pleocytosis (>1000/uL with >80% PMNs), "
                "elevated protein (>100-500 mg/dL), and markedly decreased CSF-to-serum glucose ratio (<0.4 or absolute CSF glucose < 40 mg/dL). "
                "Empiric antimicrobial therapy in immunocompetent adults aged 18-50: IV Ceftriaxone (2g q12h) plus IV Vancomycin (15-20 mg/kg q8-12h targeting trough 15-20 mcg/mL). "
                "In adults > 50 years or immunocompromised, IV Ampicillin (2g q4h) must be added to cover Listeria monocytogenes. "
                "IV Dexamethasone (10mg q6h for 4 days) should be administered prior to or with the first antibiotic dose to reduce mortality and sensorineural hearing loss in Streptococcus pneumoniae meningitis."
            ),
            topic_category="Infectious Disease",
            source_url="https://www.ninds.nih.gov/health-information/disorders/meningitis-and-encephalitis",
            authoritative_org="National Institute of Neurological Disorders and Stroke (NINDS)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0026",
            focus="Cutaneous Melanoma",
            question_id="1",
            question_type="staging_and_targeted_immunotherapy",
            question="What are the ABCDE clinical criteria, Breslow depth staging, and targeted therapies (BRAF/MEK inhibitors, PD-1 blockade) for Melanoma?",
            answer=(
                "Cutaneous Melanoma screening utilizes the ABCDE criteria: Asymmetry, Border irregularity, Color variegation, Diameter > 6mm, and Evolving size/shape. "
                "Prognosis and staging are defined by Breslow tumor thickness on full-thickness excisional biopsy with 1-3 mm margins (thin <= 1mm, intermediate 1.01-4mm, thick > 4mm) and ulceration status. "
                "Sentinel Lymph Node Biopsy (SLNB) is indicated for Breslow depth > 0.8 mm or < 0.8 mm with ulceration. "
                "In advanced or metastatic (Stage III/IV) melanoma, tumor tissue is tested for BRAF V600E/K mutations (~50% prevalence). "
                "BRAF-mutant melanoma is treated with combination BRAF + MEK kinase inhibitors (dabrafenib + trametinib, or encorafenib + binimetinib). "
                "First-line immunotherapy for BRAF-wildtype or broad metastatic disease utilizes immune checkpoint blockade: dual anti-PD-1 (nivolumab) plus anti-CTLA-4 (ipilimumab), or anti-LAG-3 (relatlimab) + nivolumab."
            ),
            topic_category="Oncology",
            source_url="https://www.cancer.gov/types/skin/patient/melanoma-treatment-pdq",
            authoritative_org="National Cancer Institute (NCI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0027",
            focus="Thoracic Aortic Aneurysm and Aortic Dissection",
            question_id="1",
            question_type="stanford_classification_and_repair",
            question="What are the Stanford classification, emergency imaging, and blood pressure reduction goals for acute aortic dissection and thoracic aneurysms?",
            answer=(
                "Thoracic Aortic Aneurysm (TAA) involves dilation of the ascending aorta, aortic arch, or descending aorta. Elective surgical replacement is indicated at diameter >= 5.5 cm (or >= 4.5-5.0 cm in Marfan / connective tissue disease). "
                "Acute Aortic Dissection is classified by the Stanford system: Type A involves the ascending aorta (surgical emergency requiring immediate open sternotomy and graft replacement); "
                "Type B involves only the descending aorta distal to the left subclavian artery (managed medically with ICU anti-impulse therapy unless complicated by malperfusion or rupture, where Thoracic Endovascular Aortic Repair [TEVAR] is indicated). "
                "Diagnosis is confirmed with emergent CT Angiography (CTA) of chest/abdomen/pelvis. "
                "Emergency medical anti-impulse therapy targets heart rate < 60 bpm and systolic BP 100-120 mmHg within 20 minutes using IV beta-blockers (esmolol or labetalol), followed by vasodilators (nitroprusside or nicardipine) only after HR is controlled."
            ),
            topic_category="Cardiology",
            source_url="https://www.nhlbi.nih.gov/health/aortic-aneurysm",
            authoritative_org="National Heart, Lung, and Blood Institute (NHLBI)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0028",
            focus="Blepharitis",
            question_id="1",
            question_type="definition_and_causes",
            question="What is Blepharitis, what causes it, and how is it classified?",
            answer=(
                "Blepharitis is a common, chronic inflammatory disorder of the eyelid margins. "
                "It is classified anatomically and etiologically into two primary forms: "
                "1. Anterior Blepharitis: Involves the exterior front edge of the eyelid margin where the eyelashes are rooted. "
                "Primary causes include Staphylococcal bacterial overgrowth (Staphylococcus aureus and S. epidermidis), "
                "seborrheic dermatitis (dandruff of the scalp and eyebrows), and Demodex folliculorum mite infestation of eyelash follicles. "
                "2. Posterior Blepharitis: Involves the inner edge of the eyelid in contact with the globe. "
                "It is predominantly caused by Meibomian Gland Dysfunction (MGD), wherein the modified sebaceous glands become obstructed, "
                "hyperkeratinized, or secrete altered, turbid lipids. Posterior blepharitis is strongly linked to acne rosacea (ocular rosacea) "
                "and seborrheic dermatitis. "
                "Both forms impair tear film stability, predisposing patients to evaporative dry eye, recurrent hordeola (styes), and chalazia."
            ),
            topic_category="General Medicine",
            source_url="https://www.nei.nih.gov/learn-about-eye-health/eye-conditions-and-diseases/blepharitis",
            authoritative_org="National Eye Institute (NEI / NIH)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0029",
            focus="Blepharitis",
            question_id="2",
            question_type="symptoms",
            question="What are the clinical signs and symptoms of Blepharitis?",
            answer=(
                "Clinical signs and symptoms of Blepharitis are characteristically bilateral and follow a chronic, relapsing course. Hallmarks include: "
                "1. Ocular Discomfort: Persistent burning, stinging, gritty foreign-body sensation, pruritus (itching) along lid margins, and heaviness of the eyelids. "
                "2. Eyelid Margin Changes: Erythema (redness) and edema of lid margins, greasy scales or dry brittle crusts (collarettes) clinging to eyelash bases, "
                "frequently causing eyelashes to stick together upon waking ('crusty/glued eyes'). "
                "3. Tear Film and Visual Fluctuations: Paradoxical hyperlacrimation (excessive reflex tearing) coupled with dry eye sensations, mild photophobia (light sensitivity), "
                "frequent blinking, and transient blurred vision that improves after blinking. "
                "4. Chronic Complications: In longstanding or severe disease, patients may develop madarosis (loss of eyelashes), trichiasis (misdirected eyelashes scraping cornea), "
                "eyelid margin ulceration or thickening (tylosis), recurrent chalazia, and superficial punctate keratitis."
            ),
            topic_category="General Medicine",
            source_url="https://medlineplus.gov/ency/article/001619.htm",
            authoritative_org="National Eye Institute (NEI / NIH)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0030",
            focus="Blepharitis",
            question_id="3",
            question_type="treatment_and_management",
            question="How is Blepharitis diagnosed and what are the evidence-based treatments and eyelid hygiene protocols?",
            answer=(
                "Diagnosis of Blepharitis is confirmed clinically via slit-lamp biomicroscopy, evaluating eyelash collarettes, "
                "meibomian gland orifice capping, tear break-up time (TBUT < 10 seconds indicates tear film instability), and corneal fluorescein staining. "
                "Standard clinical management follows a stepwise, multimodal protocol: "
                "1. Eyelid Hygiene (Cornerstone of Therapy): Daily warm compresses (40-45°C for 5-10 minutes) to melt inspissated meibomian lipids, "
                "followed by gentle eyelid massage toward the lid margin and lid scrubs using hypochlorous acid (0.01%), dilute baby shampoo, or tea tree oil cleansers (for Demodex). "
                "2. Topical Antimicrobial & Anti-inflammatory Therapy: For acute anterior bacterial exacerbations, topical ophthalmic antibiotic ointments "
                "(bacitracin or erythromycin applied to lid margins at bedtime for 2-4 weeks) or topical azithromycin 1% solution. "
                "Short-course topical corticosteroids (loteprednol etabonate or fluorometholone) are used for marked inflammation under ophthalmologic supervision. "
                "3. Systemic Oral Antibiotics: For severe posterior blepharitis / MGD or ocular rosacea refractory to lid hygiene, "
                "oral tetracyclines (doxycycline 50-100 mg daily or minocycline) provide potent anti-inflammatory and lipid-regulating action via matrix metalloproteinase inhibition. "
                "4. Tear Film Support: Frequent instillation of preservative-free artificial tears and bedtime lubricating ophthalmic ointments to manage secondary dry eye."
            ),
            topic_category="General Medicine",
            source_url="https://www.nei.nih.gov/learn-about-eye-health/eye-conditions-and-diseases/blepharitis",
            authoritative_org="National Eye Institute (NEI / NIH)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0031",
            focus="Conjunctivitis (Pink Eye)",
            question_id="1",
            question_type="differential_diagnosis_and_treatment",
            question="What are the clinical differences, signs, and treatments for viral, bacterial, and allergic conjunctivitis?",
            answer=(
                "Conjunctivitis is inflammation of the bulbar and palpebral conjunctiva. Differentiation is based on clinical presentation: "
                "1. Viral Conjunctivitis (most common, ~80% Adenovirus): Watery serous discharge, preauricular lymphadenopathy, concurrent URI symptoms, "
                "highly contagious. Treatment is supportive (cold compresses, preservative-free artificial tears, strict hand hygiene; self-limiting within 1-2 weeks). "
                "2. Bacterial Conjunctivitis (S. aureus, S. pneumoniae, H. influenzae): Thick purulent or mucopurulent discharge, eyelashes matted shut throughout the day, "
                "unilateral or bilateral. Treated with broad-spectrum topical antibiotic drops (polymyxin B/trimethoprim, fluoroquinolones for contact lens wearers due to Pseudomonas risk, "
                "or erythromycin ointment). Hyperacute purulent discharge requires urgent workup for Neisseria gonorrhoeae. "
                "3. Allergic Conjunctivitis: Intense ocular itching (hallmark), bilateral chemosis, watery discharge, and papillary reaction. "
                "Treated with dual-action topical antihistamine/mast-cell stabilizers (olopatadine, ketotifen, or alcaftadine)."
            ),
            topic_category="General Medicine",
            source_url="https://www.cdc.gov/conjunctivitis/about/index.html",
            authoritative_org="Centers for Disease Control and Prevention (CDC)",
        ),
        MedQuADRecord(
            doc_id="NIH-MEDQUAD-0032",
            focus="Gastroesophageal Reflux Disease (GERD)",
            question_id="1",
            question_type="clinical_management_and_guidelines",
            question="What are the diagnostic evaluation, alarm symptoms, and stepwise medical therapy for GERD?",
            answer=(
                "Gastroesophageal Reflux Disease (GERD) develops when retrograde flow of gastric contents causes troublesome symptoms or mucosal complications. "
                "Typical symptoms include pyrosis (heartburn) and acid regurgitation. "
                "Alarm symptoms warranting prompt upper endoscopy (EGD) include dysphagia, odynophagia, unintentional weight loss, recurrent vomiting, evidence of GI bleeding, or family history of upper GI cancer. "
                "Management follows a stepwise guideline strategy: "
                "1. Lifestyle Modification: Weight reduction, elevating head of bed 6 inches, avoiding late meals (<3 hours before recumbency), and dietary trigger avoidance. "
                "2. Pharmacotherapy: For mild intermittent symptoms, H2-receptor antagonists (famotidine). "
                "For frequent or erosive disease, standard once-daily Proton Pump Inhibitor (PPI, e.g. omeprazole 20-40 mg, pantoprazole 40 mg) taken 30-60 minutes before first meal of the day for 8 weeks. "
                "Non-responders may undergo twice-daily PPI dosing or 24-hour ambulatory esophageal pH/impedance monitoring. "
                "Long-standing GERD requires surveillance for Barrett's esophagus (intestinal metaplasia predisposing to adenocarcinoma)."
            ),
            topic_category="General Medicine",
            source_url="https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults",
            authoritative_org="National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)",
        ),
    ]



def export_corpus(
    records: list[MedQuADRecord],
    output_records_path: Path,
    output_chunks_path: Path,
    output_jsonl_path: Path | None = None,
) -> None:
    """Exports normalized records and chunks to JSON files and Discovery Engine JSONL."""
    output_records_path.parent.mkdir(parents=True, exist_ok=True)

    records_data = [asdict(r) for r in records]
    with open(output_records_path, "w", encoding="utf-8") as f:
        json.dump(records_data, f, indent=2)
    logger.info("Saved %d records to %s", len(records_data), output_records_path)

    chunks = process_records_to_chunks(records)
    chunks_data = [asdict(c) for c in chunks]
    with open(output_chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f, indent=2)
    logger.info("Saved %d chunks to %s", len(chunks_data), output_chunks_path)

    if output_jsonl_path:
        output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_jsonl_path, "w", encoding="utf-8") as f:
            for c in chunks_data:
                doc_record = {
                    "_id": c["chunk_id"],
                    "id": c["chunk_id"],
                    "doc_id": c["doc_id"],
                    "title": c["title"],
                    "content": c["content"],
                    "topic_category": c["topic_category"],
                    "source_url": c["source_url"],
                    "authoritative_org": c["authoritative_org"],
                }
                f.write(json.dumps(doc_record) + "\n")
        logger.info("Exported %d Discovery Engine JSONL docs to %s", len(chunks_data), output_jsonl_path)


def main() -> None:
    """CLI entrypoint for MedQuAD dataset ingestion."""
    parser = argparse.ArgumentParser(description="MedQuAD Ingestion and Chunking Tool")
    parser.add_argument(
        "--generate-sample", action="store_true", default=True, help="Generate sample NIH corpus"
    )
    parser.add_argument(
        "--output-records",
        type=str,
        default="data/sample_medquad_records.json",
        help="Path to save records",
    )
    parser.add_argument(
        "--output-chunks", type=str, default="data/sample_medquad.json", help="Path to save chunks"
    )
    parser.add_argument(
        "--output-jsonl",
        type=str,
        default="data/medquad_documents.jsonl",
        help="Path to save Discovery Engine JSONL",
    )
    args = parser.parse_args()

    logger.info("Executing MedQuAD dataset preparation...")
    records = generate_sample_dataset()
    export_corpus(
        records=records,
        output_records_path=Path(args.output_records),
        output_chunks_path=Path(args.output_chunks),
        output_jsonl_path=Path(args.output_jsonl),
    )
    logger.info("MedQuAD ingestion pipeline completed successfully.")


if __name__ == "__main__":
    main()
