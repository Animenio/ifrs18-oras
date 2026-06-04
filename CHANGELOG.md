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
