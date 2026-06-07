# Database Design Document
## MedSafe AI — `data/medicine_db.json`

**Version:** 1.0  
**Date:** 2026-06-07  

---

## 1. Overview

MedSafe AI uses a local JSON file (`data/medicine_db.json`) as its deterministic drug interaction database. This is intentional: by keeping the safety-critical data offline and version-controlled, the system guarantees that known dangerous interactions will always be flagged, independent of any external API.

The database is the core of the **deterministic layer** — all interaction logic that does not involve an LLM is driven entirely by this file.

---

## 2. Schema

Each entry in the JSON array represents one medicine:

```json
{
  "name": "string",
  "active_salt": "string",
  "uses": "string",
  "interactions": [
    {
      "interacting_drug_salt": "string",
      "severity": "High | Moderate | Low",
      "description": "string"
    }
  ]
}
```

### Field Definitions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | string | Brand name or common name of the medicine | `"Aspirin"`, `"Advil"` |
| `active_salt` | string | The active chemical compound (IUPAC or common chemical name) | `"Acetylsalicylic acid"`, `"Ibuprofen"` |
| `uses` | string | Brief, comma-separated list of therapeutic uses | `"Pain relief, fever reduction"` |
| `interactions` | array | List of known drug-drug interaction records | — |
| `interactions[].interacting_drug_salt` | string | The active salt of the drug this medicine interacts with | `"Warfarin"` |
| `interactions[].severity` | enum string | Severity classification: `"High"`, `"Moderate"`, or `"Low"` | `"High"` |
| `interactions[].description` | string | Plain-English clinical description of the interaction | `"Increased risk of bleeding."` |

---

## 3. Current Dataset (v1.0)

The database currently contains 9 medicines with 13 interaction records:

| Name | Active Salt | Key Interactions |
|------|-------------|-----------------|
| Aspirin | Acetylsalicylic acid | Warfarin (High), Ibuprofen (Moderate) |
| Warfarin | Warfarin sodium | Acetylsalicylic acid (High), Acetaminophen (Moderate) |
| Paracetamol | Acetaminophen | Warfarin sodium (Moderate) |
| Amoxicillin | Amoxicillin trihydrate | Methotrexate (High) |
| Lisinopril | Lisinopril | Potassium (High), Ibuprofen (Moderate) |
| Advil | Ibuprofen | Lisinopril (Moderate), Acetylsalicylic acid (Moderate) |
| Metformin | Metformin hydrochloride | Ibuprofen (Moderate) |
| Prilosec | Omeprazole | Clopidogrel (High) |
| Lipitor | Atorvastatin | Clarithromycin (High) |

---

## 4. Data Relationships

The database uses a **flat array structure with embedded interaction lists**. There is no explicit foreign key relationship — interactions reference their counterpart by `active_salt` string, not by array index. This is intentional for simplicity and human readability.

```
medicines[]
    └── medicine
          ├── name (unique, used for display)
          ├── active_salt (used as canonical identifier for matching)
          └── interactions[]
                └── interacting_drug_salt (references another medicine's active_salt)
```

**Important:** Interactions can be bidirectional but are stored unidirectionally. For example:
- `Aspirin.interactions` contains `{interacting_drug_salt: "Warfarin"}`
- `Warfarin.interactions` also contains `{interacting_drug_salt: "Acetylsalicylic acid"}`

The `check_interactions()` method in `medicine_db.py` handles deduplication to prevent the same pair from being reported twice.

---

## 5. How Fuzzy Matching Works

The matching pipeline in `MedicineDatabase` (defined in `utils/medicine_db.py`) works in two passes:

### Pass 1: Brand Name Match
```python
name_match = process.extractOne(query, self.medicine_names, scorer=fuzz.token_sort_ratio)
if name_match and name_match[1] >= threshold:
    return self.get_medicine_by_name(name_match[0])
```
- Matches user input against all `name` fields in the DB
- Uses `token_sort_ratio` — sorts tokens alphabetically before comparing, so "Advil Ibuprofen" matches "Ibuprofen Advil"
- Default threshold: 80/100

### Pass 2: Active Salt Match (fallback)
```python
salt_match = process.extractOne(query, self.salt_names, scorer=fuzz.token_sort_ratio)
if salt_match and salt_match[1] >= threshold:
    return self.get_medicine_by_salt(salt_match[0])
```
- If brand name fails, try matching the query against all `active_salt` fields
- Useful when users type generic/chemical names directly

### Why token_sort_ratio?
Standard Levenshtein ratio is sensitive to word order. `token_sort_ratio` normalizes by sorting tokens first, making it resilient to:
- "Aspirin 500mg" → matches "Aspirin"
- "500mg Paracetamol" → matches "Paracetamol"
- Partial brand + dosage strings

---

## 6. Interaction Detection Logic

`check_interactions(medicine_list)` runs an O(n²) pairwise comparison across all identified medicines:

```python
for i in range(n):
    for j in range(i+1, n):
        med1 = medicine_list[i]
        med2 = medicine_list[j]
        # Check med1's interactions vs med2's active_salt
        for interaction in med1.get('interactions', []):
            if fuzz.token_sort_ratio(interaction['interacting_drug_salt'], med2['active_salt']) > 85:
                interactions_found.append(...)
```

The inner match uses a slightly higher threshold of **85** (vs 80 for name resolution) because this is a safety-critical check: we want false positives over false negatives, but not so low that unrelated drugs trigger each other.

---

## 7. Extending the Database

Adding a new medicine requires zero code changes. Simply add a new object to the JSON array following the schema:

```json
{
  "name": "Clopidogrel",
  "active_salt": "Clopidogrel bisulfate",
  "uses": "Antiplatelet, stroke prevention",
  "interactions": [
    {
      "interacting_drug_salt": "Omeprazole",
      "severity": "High",
      "description": "Omeprazole reduces the antiplatelet effectiveness of Clopidogrel."
    }
  ]
}
```

The `MedicineDatabase` class rebuilds its internal name and salt lookup lists on every instantiation (or from the Streamlit resource cache).

---

## 8. Future Migration Path

The JSON flat-file approach is appropriate for a prototype with < 100 drugs. At scale, the following migration path is recommended:

| Scale | Recommended DB | Rationale |
|-------|---------------|-----------|
| < 100 drugs | `medicine_db.json` (current) | Zero infrastructure, version-controlled |
| 100–10,000 drugs | SQLite + FTS5 | File-based, full-text search, no server required |
| > 10,000 drugs | PostgreSQL + pgvector | Semantic vector search for drug name resolution; production-grade |
| Clinical integration | RxNorm API or DrugBank license | Authoritative, clinically validated interaction data |

For the vector DB migration, `active_salt` fields would be embedded using a medical language model (e.g., BioBERT or PubMedBERT) to enable semantic matching rather than string matching.

---

## 9. Data Quality Notes

- **Source:** The current dataset is hand-curated for demonstration purposes. It is not a clinical reference.
- **Completeness:** Only high-profile interactions are included. Many real-world interactions are not represented.
- **Directionality:** Some interactions are stored in one direction only. The application handles bidirectional checking in code but the raw data is asymmetric.
- **Production warning:** This database must not be used as the sole safety reference in a real clinical setting. Replace with a validated clinical dataset before any production medical use.
