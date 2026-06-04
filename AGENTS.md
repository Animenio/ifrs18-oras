# AGENTS.md

Objective: build and maintain IFRS18-ORAS, a deterministic Python research pipeline measuring observable documentary alignment with selected IFRS 18 presentation and disclosure features in public reporting packages.

Required verification commands before completing future tasks:
- `make lint`
- `make format-check`
- `make test`
- `make validate-codebook`
- `make demo`
- `make verify`

Rules:
- Do not introduce hidden scoring logic; all scoring rules and regex patterns must remain visible and traceable.
- Do not add LLM, external AI API, web-request, proprietary-service, probabilistic-classification, or default OCR dependencies to the scoring runtime.
- Keep codebook rules external to Python source code; update `config/codebook_*.json` rather than hard-coding item patterns.
- Do not add local modules that shadow dependencies, including `fitz.py`, `pymupdf.py`, `yaml.py`, or `pydantic.py`.
- Update documentation and tests whenever scoring behaviour, output fields, codebook semantics, or applicability logic changes.
- Preserve backwards compatibility unless a versioned changelog entry documents the break and its comparability implications.
- Run the full verification suite before completing future tasks.

XHTML/ESEF hardening notes:
- Native ESEF XHTML/HTML/Inline XBRL support uses the declared `lxml>=5.0,<7` runtime dependency; do not add a silent standard-library parser fallback for scoring.
- XHTML/HTML inputs must not be converted to PDF and must not use OCR, LLMs, web requests, or hidden scoring logic.
- PDF evidence uses page-number locators; XHTML/HTML evidence uses deterministic block indexes and XPath locators where available.
- Company source discovery is recursive under each company folder and is restricted to `.pdf`, `.xhtml`, `.html`, and `.htm` files.
- Duplicate source documents are excluded by SHA-256 within each company folder and recorded with `exclusion_reason=duplicate_sha256`.
- The EU core-score recommendation is to run `score --preferred-format xhtml`; `all` remains the default for backwards-compatible mixed-package scoring.
- Report main, supplementary D, and total evidence coverage separately; `evidence_coverage_pct` is a backwards-compatible alias for main coverage.
