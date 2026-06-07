# Software Requirements Specification (SRS)
## MedSafe AI — Intelligent Healthcare Assistant

**Version:** 1.0  
**Date:** 2026-06-07  
**Status:** Active  

---

## 1. Introduction

### 1.1 Purpose
This document defines the functional and non-functional requirements for MedSafe AI. It serves as the authoritative reference for developers, testers, and stakeholders building and maintaining the system.

### 1.2 Scope
MedSafe AI is a Streamlit-based web application that integrates a local drug interaction database with Google Gemini 2.5 Flash to provide drug interaction checking, prescription OCR, and symptom triaging capabilities.

### 1.3 Definitions
| Term | Definition |
|------|------------|
| Active Salt | The chemical compound responsible for a drug's therapeutic effect (e.g., Ibuprofen is the active salt of Advil) |
| Fuzzy Match | String similarity-based matching using `thefuzz` library's `token_sort_ratio` scorer |
| Deterministic Layer | System components that produce reproducible outputs from structured data (the local DB + fuzzy matcher) |
| Probabilistic Layer | System components using LLMs that produce variable natural language outputs (Gemini 2.5 Flash) |
| Threshold | The minimum fuzzy match score (0–100) required to accept a match; default is 80 |

---

## 2. System Overview

MedSafe AI operates as a single-server Streamlit application. Users interact through a browser UI. The backend is entirely Python-based, with no persistent user storage. All AI calls go to the Google Generative AI API (`google-generativeai`).

```
Browser UI (Streamlit)
    ↓
views/ (page components)
    ↓
utils/ (business logic)
    ├── medicine_db.py   → data/medicine_db.json (deterministic)
    ├── llm_helper.py    → Gemini 2.5 Flash API (probabilistic)
    └── ocr_helper.py    → Gemini 2.5 Flash Vision API (probabilistic)
```

---

## 3. Functional Requirements

### FR-01: Drug Name Resolution
- **Description:** The system shall accept free-text medicine names and resolve them to known active salts using fuzzy string matching.
- **Implementation:** `MedicineDatabase.fuzzy_match_medicine(query, threshold=80)` in `utils/medicine_db.py`
- **Scoring:** Uses `fuzz.token_sort_ratio` from `thefuzz`; match accepted if score ≥ threshold
- **Fallback:** If no match found at threshold, the input is classified as "unidentified" and excluded from interaction checking

### FR-02: Drug Interaction Detection
- **Description:** Given a list of resolved medicine objects, the system shall identify all pairwise drug-drug interactions using the local interaction matrix.
- **Implementation:** `MedicineDatabase.check_interactions(medicine_list)` in `utils/medicine_db.py`
- **Deduplication:** The method prevents duplicate interaction pairs (A→B and B→A reported as one)
- **Cross-match scoring:** Uses `fuzz.token_sort_ratio > 85` for salt-level matching within interaction records

### FR-03: AI Interaction Summary
- **Description:** For each detected drug interaction, the system shall generate a patient-friendly plain-language summary using Gemini 2.5 Flash.
- **Implementation:** `summarize_interaction(med1, med2, severity, description)` in `utils/llm_helper.py`
- **Constraints:** Response limited to 3–4 sentences; must end with a medical disclaimer
- **Graceful degradation:** If `GEMINI_API_KEY` is absent, returns a static error string instead of crashing

### FR-04: Prescription OCR
- **Description:** The system shall accept an uploaded image (JPG, PNG) of a handwritten or printed prescription and extract a structured list of medicines.
- **Implementation:** `extract_prescription_data(image_path)` in `utils/ocr_helper.py`
- **Output format:** JSON array of objects with keys `name` and `active_salt`
- **Failsafe:** Strips markdown code fences (` ```json `) from LLM output before `json.loads()` parsing
- **Error handling:** Returns `{"error": "..."}` dict on any failure (API error, parse failure, missing key)

### FR-05: Symptom Triage
- **Description:** The system shall accept a user profile (age, gender, recent medicines, symptoms) and return an emergency risk level and educational guidance.
- **Implementation:** `get_symptom_guidance(age, gender, medicines, experience)` in `utils/llm_helper.py`
- **Output format:** Parses structured LLM output containing `RISK_LEVEL: [Low/Medium/High]` and `GUIDANCE:` sections
- **Non-diagnostic enforcement:** Prompt explicitly instructs the model to remain "informative and non-diagnostic"

### FR-06: Severity Display
- **Description:** Interaction severity shall be visually differentiated: High severity displayed in red; Moderate severity in orange.
- **Implementation:** `views/interaction_checker.py` lines 114–121

### FR-07: Multi-Medicine Input
- **Description:** Users shall be able to add or remove medicine input fields dynamically, with a minimum of 2 fields required.
- **Implementation:** `views/interaction_checker.py` — `add_med()` and `remove_med(index)` session state callbacks

---

## 4. Non-Functional Requirements

### NFR-01: Performance
- LLM response (p95) must complete within 10 seconds under normal network conditions
- Fuzzy matching across the current 9-drug database must complete in < 100ms

### NFR-02: Reliability
- If the Gemini API is unavailable, the deterministic layer (interaction detection) must still function
- The application must not crash on malformed LLM responses; all LLM calls are wrapped in `try/except`

### NFR-03: Safety
- All AI-generated content must include a disclaimer advising users to consult a medical professional
- The system must never claim to diagnose conditions

### NFR-04: Privacy
- No personally identifiable information (PII) is stored at any point
- Prescription images uploaded for OCR are processed in memory only (not written to disk by the application)
- The `GEMINI_API_KEY` must be stored in a `.env` file and loaded via `python-dotenv`; never hardcoded

### NFR-05: Usability
- The UI shall be operable by a non-technical user without any training
- Input fields include placeholder examples (e.g., "e.g. Aspirin, Advil, Lisinopril")

### NFR-06: Maintainability
- New drug entries can be added to `data/medicine_db.json` without any code changes
- The fuzzy match threshold is a configurable parameter, not a hardcoded magic number

### NFR-07: Portability
- The application must run on any OS where Python 3.8+ and pip are available
- All dependencies are declared in `requirements.txt` and `pyproject.toml`

---

## 5. System Constraints

1. **LLM non-determinism:** AI summaries are not reproducible. The same inputs may produce different outputs across calls. Safety logic must never depend on LLM output.
2. **Database size:** `medicine_db.json` currently covers 9 drugs. Production deployment requires integration with a clinical-grade database (RxNorm, DrugBank, or OpenFDA).
3. **API key dependency:** Full functionality requires a valid `GEMINI_API_KEY`. Without it, only the deterministic interaction detection remains functional.
4. **No authentication:** The application has no user authentication layer. Deployment in a clinical environment would require adding auth.

---

## 6. Use Cases

### UC-01: Check interaction between two known drugs
1. User enters "Aspirin" and "Warfarin" in the interaction checker
2. System fuzzy-matches both to `Acetylsalicylic acid` and `Warfarin sodium`
3. System detects a High-severity interaction from the local matrix
4. Gemini generates a patient-friendly summary with disclaimer
5. UI displays red badge + medical note + AI guidance

### UC-02: Upload a prescription image
1. User uploads a JPG of a handwritten prescription
2. `extract_prescription_data()` sends image to Gemini Vision with OCR prompt
3. Gemini returns `[{"name": "Amoxicillin 500mg", "active_salt": "Amoxicillin trihydrate"}, ...]`
4. System feeds extracted names into the interaction checker flow

### UC-03: Triage symptoms
1. User enters: age 45, female, medicines "Metformin, Ibuprofen", experience "nausea and muscle cramps"
2. `get_symptom_guidance()` sends prompt to Gemini
3. System parses `RISK_LEVEL: Medium` and displays educational guidance about possible lactic acidosis risk
4. Disclaimer appended: consult a doctor
