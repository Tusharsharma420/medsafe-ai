# ⚖️ Licensing, Compliance & Medical Software Disclaimers

This document details the licensing terms, compliance guidelines, and critical liability disclaimers for the **MedSafe AI** software application.

---

## 🚫 1. Medical Software Disclaimer (Critical)

> [!WARNING]
> **NO MEDICAL ADVICE IS PROVIDED BY THIS SOFTWARE**
> The information provided by MedSafe AI—including drug-drug interactions, symptom triage risk levels, and prescription translations—is for **educational and informational purposes only**.
> 
> *   **Not Diagnostic**: MedSafe AI does not diagnose illnesses, prescribe medication, or recommend specific courses of treatment.
> *   **No Doctor-Patient Relationship**: Your use of this application does not create a doctor-patient relationship.
> *   **Not a Replacement for Professional Care**: This software must **never** be used as a substitute for professional medical advice, diagnosis, or treatment by qualified healthcare professionals.
> *   **Emergency Situations**: Do not use this app to triage emergency situations. If you are experiencing a medical emergency, call your local emergency services (e.g. 911 / 112 / 102) immediately.

---

## 📄 2. Core Software License (MIT)

The source code of this project is licensed under the **MIT License**.

```text
Copyright (c) 2026 Tushar Sharma

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📦 3. Third-Party Library & API Compliance

MedSafe AI integrates several open-source libraries and APIs. Users and contributors must adhere to their respective terms:

### A. Google Gemini API (`google-generativeai` / `google.genai`)
*   **License**: Apache License 2.0
*   **Terms of Service**: Subject to the [Google APIs Terms of Service](https://developers.google.com/terms) and [Google Generative AI Additional Terms of Service](https://support.google.com/googleapi/answer/14147367). Do not send Personally Identifiable Information (PII) or Protected Health Information (PHI) to the API endpoints unless you have configured a HIPAA-compliant workspace.

### B. Streamlit (`streamlit`)
*   **License**: Apache License 2.0
*   **Compliance**: Sharing data through public Streamlit Community Cloud hosting requires adherence to the Streamlit Privacy Policy.

### C. String Matching (`thefuzz`)
*   **License**: MIT License
*   **Compliance**: Utilizes Levenshtein distance calculations. No additional commercial restrictions.
