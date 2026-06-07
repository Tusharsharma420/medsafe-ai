# Product Requirements Document (PRD)
## MedSafe AI — Intelligent Healthcare Assistant

**Version:** 1.0  
**Date:** 2026-06-07  
**Status:** Active  

---

## 1. Overview

MedSafe AI is an AI-driven clinical decision-support and patient-safety application. It helps healthcare professionals and patients verify drug-to-drug interactions, parse handwritten or printed prescriptions using vision AI, and triage symptoms for emergency risk assessment. The system is built as a portfolio demonstration of how deterministic medical data can be safely combined with non-deterministic large language models (LLMs) in a healthcare context.

---

## 2. Problem Statement

Medication errors are one of the leading causes of preventable harm in healthcare. Patients and caregivers frequently lack access to immediate, plain-language guidance on drug interactions. Additionally, handwritten prescriptions are error-prone and hard to digitize at point-of-care. MedSafe AI addresses these problems by providing an always-available, low-friction safety layer.

---

## 3. Goals & Non-Goals

### Goals
- Provide real-time drug interaction warnings grounded in a curated local database
- Generate patient-friendly, non-diagnostic explanations via Gemini 2.5 Flash
- Parse handwritten and printed prescription images to extract medicine names
- Triage user-reported symptoms and return an emergency risk level (Low/Medium/High)
- Demonstrate responsible AI integration in medical contexts (hybrid deterministic + probabilistic design)

### Non-Goals
- **Not a diagnostic tool** — MedSafe AI does not diagnose diseases or replace medical advice
- **Not a replacement for a pharmacist or physician**
- **Not a comprehensive drug database** — the current `medicine_db.json` covers 9 representative drugs; a production deployment would integrate a full clinical database (e.g., RxNorm, DrugBank)
- **Not HIPAA-compliant in current form** — no patient data is stored, but the system has not been certified for PHI processing

---

## 4. User Personas

### Persona 1: The Cautious Patient (Primary)
- **Name:** Riya, 34, India
- **Scenario:** Takes Aspirin for heart health and was recently prescribed Ibuprofen for pain. Wants to know if they can be taken together before calling her doctor.
- **Goal:** Quick, readable interaction check with clear severity labeling
- **Pain point:** Cannot decode medical jargon; afraid of getting it wrong

### Persona 2: The Busy Caregiver
- **Name:** Arjun, 52, caregiver for elderly parents
- **Scenario:** Manages 4–5 medications for his parents and wants to confirm there are no dangerous combinations
- **Goal:** Multi-drug interaction check in one flow
- **Pain point:** No time to look up every drug pair manually

### Persona 3: The Medical Student / Junior Clinician
- **Name:** Priya, 24, MBBS intern
- **Scenario:** Receives a handwritten prescription from a senior and wants to extract and double-check medications quickly
- **Goal:** OCR prescription parsing + interaction check in one workflow
- **Pain point:** Handwriting is illegible; no quick cross-reference tool at hand

---

## 5. Core Features

| Feature | Description | Priority |
|---------|-------------|----------|
| Drug Interaction Checker | Fuzzy-match brand names/salts → cross-reference interaction matrix → LLM-generated summary | P0 |
| Prescription OCR Parser | Upload image → Gemini Vision extracts medicine list as structured JSON | P0 |
| Symptom Triager | Input age, gender, medicines, symptoms → LLM returns risk level + educational guidance | P1 |
| Dashboard | Navigation hub with feature cards and app overview | P1 |
| Severity Badges | Color-coded interaction severity (High = red, Moderate = orange) | P1 |
| Non-Diagnostic Disclaimers | Every AI response ends with a "consult your doctor" disclaimer | P0 |

---

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| Drug interaction detection accuracy | ≥ 95% for known pairs in `medicine_db.json` |
| OCR extraction success rate | ≥ 80% on clearly printed prescriptions |
| LLM response latency (p95) | < 5 seconds per request |
| Disclaimer presence rate | 100% — every AI summary must include disclaimer |
| Fuzzy match threshold accuracy | ≥ 90% correct resolution for common brand names |

---

## 7. User Flow

```
User opens app
  └─> Dashboard (views/dashboard.py)
        ├─> Drug Interaction Checker (views/interaction_checker.py)
        │     ├─> Enter medicine names (free text)
        │     ├─> Fuzzy match → active salt resolution (utils/medicine_db.py)
        │     ├─> Interaction matrix cross-check (MedicineDatabase.check_interactions)
        │     └─> LLM summary → display with severity badge (utils/llm_helper.summarize_interaction)
        │
        ├─> Prescription OCR (views/prescription_ocr.py)
        │     ├─> Upload image (JPG/PNG/PDF)
        │     ├─> Gemini Vision parse → JSON array of {name, active_salt}
        │     └─> Feed parsed list into interaction checker
        │
        └─> Symptom Solver (views/symptom_solver.py)
              ├─> Enter age, gender, medicines, symptoms
              └─> LLM returns RISK_LEVEL + GUIDANCE (utils/llm_helper.get_symptom_guidance)
```

---

## 8. Release Criteria (v1.0)

- [ ] All three core features are functional end-to-end
- [ ] Every AI response includes a non-diagnostic disclaimer
- [ ] No patient data is persisted to disk or database
- [ ] The app runs with a single `streamlit run app.py` command
- [ ] `GEMINI_API_KEY` is loaded from `.env` (never hardcoded)
- [ ] Fuzzy matching threshold is set to 80% (configurable via `threshold` param)

---

## 9. Out of Scope (v1.0)

- User accounts / authentication
- Full RxNorm or DrugBank integration
- Dosage interaction checks (only salt-level interactions currently)
- Mobile native app
- Multi-language support
- EHR (Electronic Health Record) integration
