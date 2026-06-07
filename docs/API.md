# API Documentation
## MedSafe AI — Internal Utility APIs

**Version:** 1.0  
**Date:** 2026-06-07  

> These are internal Python APIs — not HTTP REST endpoints. They are called directly by the Streamlit view components in `views/`.

---

## Module: `utils/medicine_db.py`

Provides the deterministic drug interaction detection layer. All functions here operate on local data only — no network calls.

---

### Class: `MedicineDatabase`

```python
class MedicineDatabase:
    def __init__(self)
```

**Description:** Loads `data/medicine_db.json` on instantiation and builds in-memory lookup lists for fuzzy matching. Intended to be used as a singleton via Streamlit's `@st.cache_resource`.

**Attributes:**
- `self.medicines` — `list[dict]`: Full list of medicine objects from the JSON database
- `self.medicine_names` — `list[str]`: All `name` values, used for brand name fuzzy matching
- `self.salt_names` — `list[str]`: All `active_salt` values, used for salt fuzzy matching

---

### `MedicineDatabase.fuzzy_match_medicine`

```python
def fuzzy_match_medicine(self, query: str, threshold: int = 80) -> dict | None
```

**Description:** Attempts to resolve a free-text user input to a known medicine record. Performs two-pass matching: brand name first, then active salt.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | The user-entered medicine name (e.g. `"Advil"`, `"ibuprofen 400mg"`) |
| `threshold` | `int` | `80` | Minimum `fuzz.token_sort_ratio` score (0–100) to accept a match |

**Returns:**
- `dict` — The matching medicine object from `medicine_db.json` if found, e.g.:
  ```json
  {
    "name": "Advil",
    "active_salt": "Ibuprofen",
    "uses": "Pain relief, fever reduction, anti-inflammatory",
    "interactions": [...]
  }
  ```
- `None` — If no match meets the threshold in either name or salt pass

**Example:**
```python
db = MedicineDatabase()
result = db.fuzzy_match_medicine("advil")
# → {"name": "Advil", "active_salt": "Ibuprofen", ...}

result = db.fuzzy_match_medicine("xyz_unknown_drug")
# → None
```

**Notes:**
- Uses `thefuzz.process.extractOne()` with `fuzz.token_sort_ratio` scorer
- Name pass runs first; if it meets threshold, salt pass is skipped
- `query=None` or `query=""` returns `None` immediately

---

### `MedicineDatabase.get_medicine_by_name`

```python
def get_medicine_by_name(self, name: str) -> dict | None
```

**Description:** Exact (case-insensitive) lookup by `name` field. Used internally by `fuzzy_match_medicine`.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Exact medicine name to look up |

**Returns:** Matching medicine dict or `None`

---

### `MedicineDatabase.get_medicine_by_salt`

```python
def get_medicine_by_salt(self, salt: str) -> dict | None
```

**Description:** Exact (case-insensitive) lookup by `active_salt` field. Used internally by `fuzzy_match_medicine`.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `salt` | `str` | Exact active salt name to look up |

**Returns:** Matching medicine dict or `None`

---

### `MedicineDatabase.check_interactions`

```python
def check_interactions(self, medicine_list: list[dict]) -> list[dict]
```

**Description:** Performs pairwise drug-drug interaction checking across all identified medicines. Checks each pair in both directions and deduplicates results.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `medicine_list` | `list[dict]` | List of resolved medicine objects (output of multiple `fuzzy_match_medicine` calls) |

**Returns:** `list[dict]` — List of detected interactions. Each interaction dict contains:
```python
{
    "med1": str,        # Name of first medicine
    "med2": str,        # Name of second medicine
    "severity": str,    # "High", "Moderate", or "Low"
    "description": str  # Clinical description of the interaction
}
```
Returns empty list `[]` if no interactions are found.

**Interaction matching threshold:** `fuzz.token_sort_ratio > 85` (higher than the name resolution threshold for safety)

**Deduplication:** Prevents the same pair (A, B) from appearing as both (A, B) and (B, A).

**Example:**
```python
db = MedicineDatabase()
aspirin = db.fuzzy_match_medicine("Aspirin")
warfarin = db.fuzzy_match_medicine("Warfarin")
interactions = db.check_interactions([aspirin, warfarin])
# → [{"med1": "Aspirin", "med2": "Warfarin", "severity": "High", "description": "Increased risk of bleeding."}]
```

**Complexity:** O(n² × m) where n = number of medicines, m = average interactions per medicine. Acceptable for n < 20.

---

## Module: `utils/llm_helper.py`

Provides LLM-powered text generation using Gemini 2.5 Flash. All functions are probabilistic — outputs may vary between calls with identical inputs.

**Initialization:** On import, reads `GEMINI_API_KEY` from environment (via `python-dotenv`) and calls `genai.configure(api_key=api_key)`. Instantiates `genai.GenerativeModel('gemini-2.5-flash')` as `generation_model`.

---

### `summarize_interaction`

```python
def summarize_interaction(med1: str, med2: str, severity: str, description: str) -> str
```

**Description:** Generates a patient-friendly, non-diagnostic plain-language summary of a known drug interaction using Gemini 2.5 Flash.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `med1` | `str` | Name of the first medicine (e.g. `"Aspirin"`) |
| `med2` | `str` | Name of the second medicine (e.g. `"Warfarin"`) |
| `severity` | `str` | Severity string from the interaction record (`"High"`, `"Moderate"`, `"Low"`) |
| `description` | `str` | Clinical description from the interaction record |

**Returns:** `str` — 3–4 sentence patient-friendly summary including a disclaimer. On error or missing API key, returns an error string (never raises).

**Prompt design:**
- Role: "MedSafe AI, a helpful, educational, and non-diagnostic healthcare assistant"
- Length constraint: "under 3-4 sentences"
- Mandatory disclaimer: "always include a disclaimer...advising them to consult a doctor"

**Example:**
```python
summary = summarize_interaction(
    "Aspirin", "Warfarin", "High",
    "Increased risk of bleeding."
)
# → "Taking Aspirin and Warfarin together significantly increases your risk of bleeding,
#    including internal bleeding that may not be immediately visible. This combination
#    requires close medical supervision. Please consult your doctor or pharmacist before
#    taking these medicines together — this information is educational and not medical advice."
```

**Error responses:**
- Missing API key → `"API Key not configured. Unable to generate AI summary."`
- API/network error → `"Error generating summary: {exception message}"`

---

### `get_symptom_guidance`

```python
def get_symptom_guidance(age: int, gender: str, medicines: str, experience: str) -> tuple[str, str]
```

**Description:** Generates educational symptom guidance and an emergency risk level based on user-reported profile and symptoms.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `age` | `int` | Patient age in years |
| `gender` | `str` | Patient gender string (e.g. `"Female"`, `"Male"`) |
| `medicines` | `str` | Comma-separated list of medicines recently taken |
| `experience` | `str` | Free-text description of symptoms or experience |

**Returns:** `tuple[str, str]` — `(guidance, risk_level)` where:
- `guidance`: Educational response text (string)
- `risk_level`: One of `"Low"`, `"Medium"`, `"High"`, or `"Unknown"` (fallback if parsing fails)

**Structured output parsing:** The function expects the LLM to return a response matching:
```
RISK_LEVEL: [Low/Medium/High]
GUIDANCE:
[Response text]
```
Parsing is done via string splitting; if the format is missing, the full response is returned as `guidance` and `risk_level` defaults to `"Unknown"`.

**Example:**
```python
guidance, risk = get_symptom_guidance(45, "Female", "Metformin, Ibuprofen", "nausea and muscle cramps")
# → ("Nausea and muscle cramps in someone taking Metformin and Ibuprofen could indicate...", "Medium")
```

**Error responses:**
- Missing API key → `("API Key not configured. Unable to generate AI guidance.", "Unknown")`
- API/network error → `(f"Error generating guidance: {exception}", "Unknown")`

---

## Module: `utils/ocr_helper.py`

Provides prescription image parsing using Gemini 2.5 Flash's vision capabilities.

**Initialization:** Same pattern as `llm_helper.py` — reads API key from env, instantiates `genai.GenerativeModel('gemini-2.5-flash')` as `vision_model`.

---

### `extract_prescription_data`

```python
def extract_prescription_data(image_path: str) -> list[dict] | dict
```

**Description:** Accepts a path to a prescription image (handwritten or printed) and extracts a structured list of medicines using Gemini Vision.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `image_path` | `str` | Absolute or relative file path to a JPG or PNG image |

**Returns:**
- On success: `list[dict]` — JSON array of medicine objects, e.g.:
  ```json
  [
    {"name": "Amoxicillin 500mg", "active_salt": "Amoxicillin trihydrate"},
    {"name": "Paracetamol", "active_salt": "Acetaminophen"}
  ]
  ```
- On failure: `dict` — Error object: `{"error": "Error running OCR: {exception message}"}`

**Vision prompt design:**
- Role: "an expert pharmacist AI reading a prescription image"
- Output constraint: "Return exactly ONLY a JSON array of objects, with no markdown formatting or extra text"
- Schema enforced: `[{"name": "...", "active_salt": "..."}]`

**Failsafe parsing:**
```python
text = text.replace('```json', '').replace('```', '').strip()
return json.loads(text)
```
Strips markdown code fences before parsing to handle models that ignore the "no markdown" instruction.

**Example:**
```python
medicines = extract_prescription_data("/tmp/prescription.jpg")
# → [{"name": "Aspirin 100mg", "active_salt": "Acetylsalicylic acid"}]

medicines = extract_prescription_data("/tmp/blurry.jpg")
# → {"error": "Error running OCR: JSONDecodeError..."}
```

**Notes:**
- Images are opened via `PIL.Image.open()` and passed as a multimodal input alongside the text prompt
- Large or blurry images may cause parse failures; the error dict prevents crashes
- The function does not write the image to any persistent storage
