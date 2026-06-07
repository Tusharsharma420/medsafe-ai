# System Architecture Document
## MedSafe AI — Intelligent Healthcare Assistant

**Version:** 1.0  
**Date:** 2026-06-07  

---

## 1. Architectural Philosophy

MedSafe AI is designed around a **hybrid deterministic-probabilistic boundary**. This is the core architectural decision that makes it safe to use LLMs in a medical context:

- **Deterministic layer:** All safety-critical decisions (known drug interactions, severity flags) are made using structured, offline, version-controlled data. This layer will always produce the same output for the same input.
- **Probabilistic layer:** LLMs are used exclusively for tasks that require natural language synthesis — summarization, OCR parsing, symptom triage. These outputs are educational only and are never used as the basis for safety decisions.

This separation ensures that a hallucinating LLM cannot introduce a false negative on a known dangerous drug interaction.

---

## 2. System Components

```
┌────────────────────────────────────────────────────────────────┐
│                      Browser (User)                            │
└───────────────────────────┬────────────────────────────────────┘
                            │ HTTP (Streamlit WebSocket)
┌───────────────────────────▼────────────────────────────────────┐
│                    Streamlit Server                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    app.py (Entry Point)                  │  │
│  │           Page config, global CSS, routing               │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │                                               │
│  ┌──────────────▼───────────────────────────────────────────┐  │
│  │                     views/                               │  │
│  │  ┌──────────────┐ ┌───────────────┐ ┌────────────────┐  │  │
│  │  │ dashboard.py │ │interaction_   │ │prescription_   │  │  │
│  │  │              │ │checker.py     │ │ocr.py          │  │  │
│  │  └──────────────┘ └──────┬────────┘ └───────┬────────┘  │  │
│  │                          │                   │           │  │
│  └──────────────────────────┼───────────────────┼───────────┘  │
│                             │                   │               │
│  ┌──────────────────────────▼───────────────────▼───────────┐  │
│  │                     utils/                               │  │
│  │  ┌─────────────────────┐  ┌────────────┐ ┌───────────┐  │  │
│  │  │   medicine_db.py    │  │llm_helper  │ │ocr_helper │  │  │
│  │  │  MedicineDatabase   │  │    .py     │ │   .py     │  │  │
│  │  │  - fuzzy_match      │  │            │ │           │  │  │
│  │  │  - check_interactions│  │            │ │           │  │  │
│  │  └──────────┬──────────┘  └─────┬──────┘ └─────┬─────┘  │  │
│  └─────────────┼───────────────────┼───────────────┼────────┘  │
│                │                   │               │            │
│  ┌─────────────▼──────┐    ┌───────▼───────────────▼────────┐  │
│  │ data/medicine_db   │    │   Google Generative AI API     │  │
│  │      .json         │    │   (Gemini 2.5 Flash)           │  │
│  │  (local, offline)  │    │   (remote, probabilistic)      │  │
│  └────────────────────┘    └────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Descriptions

### 3.1 `app.py` — Entry Point
- Sets Streamlit page configuration (title, icon, layout, sidebar state)
- Injects global CSS (Apple-inspired typography, color palette, widget grid layout)
- Acts as the router; Streamlit's multipage routing dispatches to `views/`

### 3.2 `views/dashboard.py` — Navigation Hub
- Renders feature cards linking to the three core tools
- Provides the first-impression UI and onboarding context

### 3.3 `views/interaction_checker.py` — Drug Interaction Checker
- Manages dynamic medicine input fields via `st.session_state`
- Orchestrates the full interaction check pipeline:
  1. Calls `MedicineDatabase.fuzzy_match_medicine()` for each input
  2. Calls `MedicineDatabase.check_interactions()` on resolved medicines
  3. Calls `llm_helper.summarize_interaction()` for each detected interaction
  4. Renders severity badges and AI summaries

### 3.4 `views/prescription_ocr.py` — Prescription OCR
- Handles image upload via `st.file_uploader`
- Calls `ocr_helper.extract_prescription_data()` with the uploaded image
- Displays extracted medicine list; can feed into interaction checker

### 3.5 `views/symptom_solver.py` — Symptom Triager
- Collects age, gender, medicines, symptom description
- Calls `llm_helper.get_symptom_guidance()` and renders risk badge + guidance text

### 3.6 `utils/medicine_db.py` — Database Access Layer
- `MedicineDatabase` class loads `data/medicine_db.json` on instantiation
- Builds in-memory name and salt lists for fuzzy matching
- Cached in Streamlit with `@st.cache_resource` to avoid re-loading on every rerender
- Three public methods: `fuzzy_match_medicine()`, `get_medicine_by_name()`, `get_medicine_by_salt()`, `check_interactions()`

### 3.7 `utils/llm_helper.py` — LLM Integration
- Configures `google.generativeai` with `GEMINI_API_KEY` from `.env`
- Instantiates `genai.GenerativeModel('gemini-2.5-flash')`
- Two public functions: `summarize_interaction()`, `get_symptom_guidance()`
- All calls are wrapped in `try/except`; errors surface as strings, not exceptions

### 3.8 `utils/ocr_helper.py` — Vision OCR Integration
- Uses Gemini 2.5 Flash vision capabilities (same model as text, multimodal input)
- Opens image via `PIL.Image.open()` and sends to `vision_model.generate_content([prompt, img])`
- Strips markdown code fences before `json.loads()` parsing
- Returns `{"error": "..."}` on any failure

### 3.9 `data/medicine_db.json` — Drug Interaction Database
- Flat JSON array of 9 medicine objects
- Each object contains: `name`, `active_salt`, `uses`, `interactions[]`
- Each interaction entry: `interacting_drug_salt`, `severity`, `description`
- Self-contained; no external API required for interaction detection

---

## 4. Data Flow

### Drug Interaction Check
```
User input ("Advil", "Aspirin")
    │
    ▼
fuzzy_match_medicine("Advil", threshold=80)
    │  token_sort_ratio("Advil", all names) → 100% match → Advil → {name: "Advil", active_salt: "Ibuprofen", ...}
    ▼
fuzzy_match_medicine("Aspirin", threshold=80)
    │  → {name: "Aspirin", active_salt: "Acetylsalicylic acid", ...}
    ▼
check_interactions([advil_obj, aspirin_obj])
    │  Cross-checks Advil.interactions[].interacting_drug_salt vs Aspirin.active_salt
    │  token_sort_ratio("Acetylsalicylic acid", "Acetylsalicylic acid") = 100 > 85 → Match!
    │  Returns [{med1: "Advil", med2: "Aspirin", severity: "Moderate", description: "..."}]
    ▼
summarize_interaction("Advil", "Aspirin", "Moderate", "May reduce cardioprotective effects...")
    │  → Gemini 2.5 Flash generates 3-4 sentence plain-language summary
    ▼
Render: severity badge (orange) + medical note + AI summary
```

---

## 5. Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Frontend/Backend | Streamlit 1.x | Rapid prototyping; Python-native; no JS required |
| LLM | Gemini 2.5 Flash | Fast inference, multimodal support, generous free tier |
| Fuzzy Matching | thefuzz (python-Levenshtein) | Token-sort ratio handles word order variation in drug names |
| Image Processing | PIL (Pillow) | Standard Python image library; required for Gemini Vision input |
| Config | python-dotenv | `.env`-based secret management |
| Package Management | pyproject.toml + pip | PEP 518 standard |

---

## 6. Deployment Architecture

Current deployment is a single-server Streamlit app. For production:

```
User → CDN/Reverse Proxy (nginx) → Streamlit Server → Google AI API
                                        │
                                  [No DB required]
                                  [Stateless requests]
```

**Recommended hosting:** Streamlit Community Cloud (free), Google Cloud Run, or any PaaS supporting Python containers.

---

## 7. Scalability Considerations

- **Current:** Single-process Streamlit; no horizontal scaling. Suitable for demo/portfolio use.
- **Short-term:** Separate the backend logic into a FastAPI service. Streamlit becomes a thin UI layer calling REST endpoints.
- **Long-term:** Replace `medicine_db.json` with a PostgreSQL + pgvector database for semantic drug matching. Add caching (Redis) for repeated LLM summaries. Add a job queue for OCR processing.

---

## 8. Failure Modes & Mitigations

| Failure | Behavior | Mitigation |
|---------|----------|------------|
| Gemini API down | `summarize_interaction` returns error string | Try/except wrapping; deterministic layer still works |
| LLM returns invalid JSON (OCR) | `json.loads` raises exception | Caught in try/except; returns `{"error": "..."}` |
| Medicine not in DB | Classified as "unidentified" | Warning shown to user; interaction check proceeds with identified meds |
| API key missing | All LLM functions return static error string | Graceful degradation; deterministic features remain functional |
