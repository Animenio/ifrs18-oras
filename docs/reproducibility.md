# Reproducibility

1. Clone the repository and create a Python 3.11+ environment.
2. Run `python -m pip install -e ".[dev]"`.
3. Place public PDFs in `data/raw/<Company>/` without committing them.
4. Validate the JSON codebook with `python -m ifrs18_oras validate-codebook --codebook config/codebook_v0.1.0.json`.
5. Run `python -m ifrs18_oras score --input-dir data/raw --output-dir outputs/run_001 --codebook config/codebook_v0.1.0.json`.
6. Archive all outputs, especially `run_manifest.json`, `evidence_log.csv`, document SHA-256 hashes, codebook SHA-256, timestamp, exact command, and data cut-off.

The codebook is JSON rather than YAML because it remains human-readable and versionable while using Python standard-library parsing and avoiding an extra runtime dependency. Input provenance can be preserved by storing source URLs and hashes in researcher notes while not committing copyrighted PDFs. Codebook changes affecting scores require a new codebook version, changelog entry, updated tests, regenerated demo outputs, and comparability warnings when comparing versions.

Demo fixtures are fictional and generated programmatically. They validate deterministic software behaviour, output traceability, low-text handling, and scoring formulas; they do not validate the accounting interpretation of the provisional codebook.

A technically unreadable PDF is not evidence of low IFRS 18 alignment. IFRS18-ORAS reports the company as unscorable when no usable text-native document is available. A zero score means readable documents were analysed and no matching evidence was found; `N/A` means the source package was technically insufficient for automatic scoring. OCR is not applied silently, and replacement text-native PDFs, XHTML or XBRL sources should be obtained.
 The low-text warning threshold is a technical extraction-screening parameter, not an IFRS threshold or materiality threshold.
