# Changelog

## 0.1.0 - 2026-06-03

- Initial IFRS18-ORAS software release.
- Added codebook `0.1.0-provisional`, status `provisional_pending_accounting_review`.
- Implemented deterministic PDF extraction, regex evidence detection, conditional applicability, scoring formulas, output artifacts, synthetic demo, tests, documentation, and CI.

Codebook changes affecting scores require a new codebook version, changelog entry, updated tests, regenerated demo outputs, and a documented comparability warning when comparing runs produced with different codebook versions.


## 0.1.0 hardening revision - 2026-06-03

- Removed local PDF backend fallback and dependency-shadowing module.
- Migrated codebook file extension to JSON and removed unused runtime dependencies.
- Added real PyMuPDF backend tests, four fictional golden fixtures, stronger determinism checks, and manual-validation support.

## 0.1.0 final hardening - 2026-06-03

- Constrained the PyMuPDF dependency to `>=1.24,<2` and added tests for malformed dependency artifacts and package-version manifest keys.
- Added scoring eligibility and exclusion reasons to extraction manifests.
- Treat technically unreadable PDF packages as unscorable (`N/A`) rather than zero alignment.
- Added company processing status, usable-document count, excluded-document count, invalid-PDF tests, and mixed-package tests.

## 0.1.0 ESEF XHTML support - 2026-06-04

- Added native deterministic extraction for `.xhtml`, `.html`, and `.htm` source documents, including official ESEF XHTML/Inline XBRL filings, without PDF conversion, OCR, web requests, LLMs, or hidden scoring logic.
- Added the constrained `lxml>=5.0,<7` runtime dependency for robust XHTML parsing and recorded `lxml` in run package-version manifests.
- Preserved existing PDF extraction and scoring while adding source-document hashes to `run_manifest.json`; `source_pdf_hashes` remains for backwards compatibility.
- Updated tests and documentation for mixed PDF/XHTML packages, hidden Inline XBRL text exclusion, and supported-source handling.

## 0.1.0 ESEF XHTML audit hardening - 2026-06-04

- Required lxml as the XHTML/HTML parser backend with controlled `xhtml_parser_unavailable` exclusions instead of silent fallback parsing.
- Added source-aware evidence locators, recursive discovery, duplicate SHA-256 exclusion, preferred-format selection, expanded extraction manifests, and separated evidence-coverage metrics.
- Updated tests and documentation for audit-safe ESEF workflows while preserving PDF functionality and backwards-compatible manifest fields.


## 0.1.1 provisional codebook hardening - 2026-06-04

- Added `config/codebook_v0.1.1.json` while preserving historical `config/codebook_v0.1.0.json` for reproducibility.
- Corrected the Adjusted EBIT/EBITDA MPM-candidate regex from `adjusted\s+EBITDA?` to `adjusted\s+EBIT(?:DA)?`, preventing `Adjusted EBITD` matches and enabling `Adjusted EBIT`.
- Added narrow E2, E3, and E4 transition-transparency patterns for annual reporting periods beginning, IFRS 18 impact assessment/evaluation, and IFRS 18 affected reporting areas.
- Added deterministic XHTML/HTML context-window matching over at most three consecutive blocks in one document with auditable context locators; PDF matching remains page-local.
