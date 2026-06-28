# Reproducibility

1. Clone the repository and create a Python 3.11+ environment.
2. Run `python -m pip install -e ".[dev]"`.
3. Place public `.pdf`, `.xhtml`, `.html`, or `.htm` files anywhere under `data/raw/<Company>/` without committing them; discovery is recursive and deterministic.
4. Validate the default JSON codebook with `python -m ifrs18_oras validate-codebook --codebook config/codebook_v0.1.6.json`; validate `config/codebook_v0.1.0.json` through `config/codebook_v0.1.5.json` when reproducing earlier pilot runs.
5. Run `python -m ifrs18_oras score --input-dir data/raw --output-dir outputs/run_001 --codebook config/codebook_v0.1.6.json --preferred-format xhtml` for recommended EU ESEF core scoring, or use `--preferred-format all` for default mixed-package scoring.
6. Archive all outputs, especially `run_manifest.json`, `evidence_log.csv`, document SHA-256 hashes, codebook SHA-256, timestamp, exact command, and data cut-off.

The codebook is JSON rather than YAML because it remains human-readable and versionable while using Python standard-library parsing and avoiding an extra runtime dependency. Input provenance can be preserved by storing source URLs and hashes in researcher notes while not committing copyrighted source documents. Codebook changes affecting scores require a new codebook version, preservation of historical codebooks, changelog entry, updated tests, regenerated demo outputs, and comparability warnings when comparing versions. Codebook v0.1.6 is the current final validation-calibrated baseline; it preserves v0.1.5 historically and restores direct IFRS 18 expected-impact E5 matches while retaining the A3 collective-category fix.

Demo fixtures are fictional and generated programmatically. They validate deterministic software behaviour, output traceability, low-text handling, and scoring formulas; they do not validate the accounting interpretation of the provisional codebook.

A technically unreadable source document is not evidence of low IFRS 18 alignment. IFRS18-ORAS reports the company as unscorable when no usable text-native document is available. A zero score means readable documents were analysed and no matching evidence was found; `N/A` means the source package was technically insufficient for automatic scoring. OCR is not applied silently, and replacement text-native PDF, XHTML, HTML, or Inline XBRL sources should be obtained.
The low-text warning threshold is a technical extraction-screening parameter, not an IFRS threshold or materiality threshold.


Reproducibility controls: XHTML/HTML parsing requires lxml and does not silently fall back to another parser; PDF files use page-number locators and XHTML/HTML files use block/XPath locators; duplicate SHA-256 source documents are excluded after deterministic path ordering; non-preferred formats are retained in the extraction manifest with `non_preferred_format`.

XHTML/HTML context matching is deterministic: only consecutive blocks in the same document may be joined, at most three blocks are considered, and joined text uses a single newline separator with contributing locators recorded in evidence outputs.
