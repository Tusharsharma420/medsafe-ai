# AI Design Document
## MedSafe AI — LLM Integration, Prompt Engineering & Safety Architecture

**Version:** 1.0  
**Date:** 2026-06-07  

---

## 1. Core Design Philosophy

MedSafe AI's AI architecture is built around a single principle: **LLMs must never be in the critical path of a safety decision.**

In healthcare, false negatives (missing a dangerous drug interaction) are more harmful than false positives (flagging a safe combination). Therefore, the system uses a **hybrid deterministic-probabilistic boundary**:

```
Deterministic Layer (safety-critical)
├── medicine_db.json       — known interactions, version-controlled
├── MedicineDatabase       — fuzzy matching + interaction cross-check
└── Outputs: interaction presence/absence, severity level

        ↓ feeds into ↓

Probabilistic Layer (communication only)
├── Gemini 2.5 Flash       — generates plain-language explanations
└── Outputs: patient-friendly summaries, guidance text, OCR extraction
```

**The LLM never decides whether an interaction exists.** That decision is made deterministically. The LLM is only used to translate existing clinical data into language the user can act on.

---

## 2. Model Selection Rationale

**Model chosen:** `gemini-2.5-flash` (Google Generative AI)

| Criterion | Rationale |
|-----------|-----------|
| Speed | "Flash" tier optimizes for latency; medical UIs need < 5s responses |
| Multimodal | Single model handles both text generation and vision (OCR) — no second model needed |
| Context window | Sufficient for drug interaction data + prompt instructions |
| Free tier | Accessible for portfolio/demo deployment without billing setup |
| Safety filters | Gemini's built-in content filtering adds a secondary layer against harmful outputs |

**Why not GPT-4o or Claude?**  
The project uses Google's stack (Streamlit + `google-generativeai`) by design, as a showcase of Gemini-based agentic engineering. In production, the LLM provider is abstracted enough that swapping is feasible.

---

## 3. Prompt Engineering: Three Prompt Types

### 3.1 Drug Interaction Summarizer (`llm_helper.summarize_interaction`)

**Goal:** Convert a structured interaction record into a 3–4 sentence patient-friendly explanation with a disclaimer.

**Prompt template:**
```
You are MedSafe AI, a helpful, educational, and non-diagnostic healthcare assistant.
Explain the potential interaction between {med1} and {med2} to a patient in simple, reassuring terms.
The known severity is '{severity}' and the medical description is '{description}'.

Structure your response appropriately and keep it under 3-4 sentences.
Always include a disclaimer that this is educational and not medical advice, advising them to consult a doctor.
```

**Design decisions:**
- **Role assignment** ("You are MedSafe AI..."): Establishes persona and behavioral constraints before any task specification. The model is less likely to drift into diagnostic territory when it has a named, bounded identity.
- **Grounding in known data** (`severity`, `description`): The LLM receives the deterministic output as context. It is explaining a known fact, not discovering one — reducing hallucination risk.
- **Length constraint** ("under 3-4 sentences"): Prevents rambling. Long AI responses in medical contexts erode user trust and may introduce false information through elaboration.
- **Compulsory disclaimer** ("always include a disclaimer"): Enforced at prompt level, not post-processing. The model must generate the disclaimer as part of its natural response.
- **Tone guidance** ("simple, reassuring terms"): Reduces patient anxiety while maintaining accuracy.

**Hallucination mitigations:**
- The prompt does not ask the model to recall drug information from training data. It is given the clinical description and asked only to rephrase it.
- If the LLM contradicts the severity or description it was given, the structured UI elements (severity badge, medical note) still display the correct deterministic data.

---

### 3.2 Prescription OCR Extractor (`ocr_helper.extract_prescription_data`)

**Goal:** Extract a structured JSON list of medicines from a prescription image.

**Prompt template:**
```
You are an expert pharmacist AI reading a prescription image (handwritten or printed).
Extract the list of medicines prescribed from the image.
For each medicine, extract or infer the 'name' and the probable 'active_salt' if you can determine it.

Return exactly ONLY a JSON array of objects, with no markdown formatting or extra text.
Example:
[
    {"name": "Aspirin 500mg", "active_salt": "Acetylsalicylic acid"},
    {"name": "SomeBrandName", "active_salt": "Somesaltname"}
]
```

**Design decisions:**
- **Expert role framing** ("expert pharmacist AI"): Activates pharmacological reasoning patterns in the model, improving active salt inference accuracy.
- **Output constraint** ("Return exactly ONLY a JSON array"): Strict format enforcement. The model is told what it cannot do (markdown, extra text) and shown the exact schema with a concrete example.
- **Structured example in prompt**: Showing the exact output format is significantly more effective than describing it. The model pattern-matches to the example.
- **`active_salt` inference**: The prompt asks the model to "infer" the active salt if it can determine it. This is intentionally soft — if the model cannot determine it, it can leave it empty rather than hallucinate.

**Failsafe parsing chain:**
```python
text = text.replace('```json', '').replace('```', '').strip()
return json.loads(text)
```
Even with a strict prompt, models occasionally wrap output in markdown fences. This strip handles the most common failure mode before calling `json.loads()`.

**Failure handling:** The entire function is wrapped in `try/except`. Any failure (JSON parse error, API error, file read error) returns `{"error": "..."}` instead of crashing. The UI then displays the error gracefully.

---

### 3.3 Symptom Triager (`llm_helper.get_symptom_guidance`)

**Goal:** Given a user profile and symptom description, return a structured response containing an emergency risk level and educational guidance.

**Prompt template:**
```
You are MedSafe AI, a healthcare assistant. Determine how to educate a user based on their experience.

User Profile: Age {age}, {gender}
Recently taken medicines: {medicines}
Reported Symptoms/Experience: {experience}

Provide two things:
1. A short, educational response highlighting possible contributing factors, home remedies or lifestyle tips,
   and warning signs. Remain informative and non-diagnostic. Do not induce panic.
2. Suggest an Emergency Risk Level (Low, Medium, or High) based solely on common medical triaging for the
   described symptoms.

Output exact format:
RISK_LEVEL: [Low/Medium/High]
GUIDANCE:
[Your educational response here]
```

**Design decisions:**
- **Structured output format** (`RISK_LEVEL:` + `GUIDANCE:`): Forces the model to emit machine-parseable output alongside natural language. This avoids a separate parsing LLM call.
- **"Do not induce panic"**: Healthcare AI systems that generate alarming responses can cause users to call emergency services unnecessarily or, conversely, dismiss real warnings due to learned skepticism. This instruction calibrates tone.
- **"Non-diagnostic"** repeated in role + instruction: Redundancy is intentional. The model needs multiple signals to maintain the boundary between education and diagnosis.
- **User profile context** (age, gender, medicines): Provides contextual grounding for the triage. A 70-year-old reporting chest pain is different from a 20-year-old. Medicines context helps identify possible drug-symptom interactions.
- **Risk level enumeration** (`Low/Medium/High` only): Constrains output to three categories matching the UI's color-coding (green/yellow/red), preventing ambiguous outputs like "Medium-High".

**Parsing logic:**
```python
if "RISK_LEVEL:" in text:
    for line in text.split('\n'):
        if line.startswith("RISK_LEVEL:"):
            risk_level = line.replace("RISK_LEVEL:", "").strip()
    guidance = text.split("GUIDANCE:")[1].strip()
```
Robust to leading/trailing whitespace; falls back to full text as `guidance` and `"Unknown"` as `risk_level` if the format is absent.

---

## 4. Safety Guardrails

### 4.1 LLM Isolation from Safety Decisions
As described in Section 1, the LLM never decides whether an interaction is present. It only explains what the deterministic layer has already determined.

### 4.2 Disclaimer Enforcement
All three prompts are designed to include disclaimers:
- `summarize_interaction`: Explicit instruction — "Always include a disclaimer...advising them to consult a doctor"
- `get_symptom_guidance`: Role framing ("educational, non-diagnostic") + "Remain informative and non-diagnostic"
- `extract_prescription_data`: The output is a data extraction (no health claims made by the model)

### 4.3 Graceful Degradation
If the Gemini API is unavailable:
- Drug interaction detection still works (100% deterministic)
- LLM features return error strings — the app remains functional without crashing

### 4.4 Gemini Built-in Safety Filters
Gemini's API has built-in content filters for harmful health advice, self-harm, and dangerous instructions. MedSafe AI benefits from these as a second layer of protection without any additional code.

---

## 5. Hallucination Mitigation Strategy

| Risk | Mitigation |
|------|-----------|
| LLM invents a drug interaction that doesn't exist | Interaction detection is 100% deterministic; LLM only summarizes known ones |
| LLM overstates or understates severity | Severity badge is rendered from the deterministic record, not LLM output |
| LLM gives incorrect active salt in OCR | OCR output is re-fed into fuzzy matching; unmatched salts are flagged as "unidentified" |
| LLM gives diagnostic advice despite prompt | Role framing + redundant "non-diagnostic" instruction + Gemini safety filters |
| LLM ignores JSON format constraint (OCR) | Markdown fence stripping + `try/except` around `json.loads` |

---

## 6. Model Configuration

Both `llm_helper.py` and `ocr_helper.py` use default generation parameters (no explicit `temperature`, `top_p`, or `max_output_tokens` set). This means the model uses its default settings:

- `temperature`: Default (balanced between creativity and consistency)
- No streaming — `generate_content()` waits for the full response

**Production recommendation:** Set `temperature=0.3` for medical summarization to reduce variability, and `temperature=0.0` for OCR extraction to maximize format consistency.
