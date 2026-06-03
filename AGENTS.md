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
