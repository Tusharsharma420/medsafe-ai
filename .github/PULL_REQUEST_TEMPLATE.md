## 🚀 Pull Request Description
Provide a concise overview of the changes introduced by this PR. Mention any relevant design files, GitHub issue IDs, or specific requirements being fulfilled.

Fixes # (issue ID)

---

## 🛠 Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functional capabilities)
- [ ] Breaking change (fix or feature that would cause existing functionality to behave differently)
- [ ] CI/CD pipeline or configuration update (no runtime code impact)
- [ ] Documentation update (e.g. README updates, `gemini.md`)

---

## 🧪 Verification & Test Report

### Automated Tests
Describe the testing commands run to verify changes:
* Run command: `python -m pytest`
* Test status: [e.g., All 8 tests passed]

### Manual Verification
Describe any manual testing performed (e.g., Streamlit UI page loads, mobile viewport checks, uploading sample prescriptions):
* Steps performed: ...
* Expected outcome: ...

---

## 🛡 Security & Quality Checklist
- [ ] My code conforms to the style configuration specified in `pyproject.toml`.
- [ ] I have executed `ruff check .` locally without errors.
- [ ] I have written unit tests in `tests/` covering new logic paths.
- [ ] The change does not introduce any hardcoded credentials or API keys (secrets must live in `.env`).
- [ ] Disclaimers regarding medical software liability have been maintained.
