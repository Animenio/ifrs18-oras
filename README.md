# IFRS18-ORAS

IFRS18-ORAS is a deterministic Python research pipeline for calculating the **IFRS 18 Observable Reporting Alignment Score** from text-native public reporting packages, including PDFs and official ESEF XHTML/Inline XBRL annual financial reports. It measures **observable documentary alignment** with selected presentation and disclosure features introduced by IFRS 18 for systematic academic screening and later validation on a manually reviewed subsample.

## Academic boundary

The indicator is not a legal IFRS 18 compliance opinion, audit conclusion, organisational-readiness measure, proof of full IFRS 18 implementation, or proof that a detected alternative performance measure is legally an IFRS 18 management-defined performance measure. Codebook v0.1.5 is `provisional_validation_calibrated_pending_external_accounting_review` and includes a narrow post-merge hotfix for the PR #11 A3 and E5 review comments; it must still undergo external accounting review before empirical deployment. Regex screening can produce false positives and false negatives; demo fixtures validate software behaviour, not accounting validity.

## Repository structure

```text
config/                 JSON scoring codebook
docs/                   methodology, reproducibility, data dictionary, validation, review checklist
src/ifrs18_oras/        package source
tests/                  unit and integration tests
.github/workflows/      CI
```

Do not commit real annual reports, IFRS standard PDFs, ESEF XHTML/Inline XBRL filings, proprietary data, or source documents unless redistribution is permitted. `data/raw/` is ignored.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## CLI examples

```bash
python -m ifrs18_oras validate-codebook --codebook config/codebook_v0.1.5.json
python -m ifrs18_oras describe-codebook --codebook config/codebook_v0.1.5.json
python -m ifrs18_oras demo --output-dir outputs/demo
python -m ifrs18_oras score --input-dir data/raw --output-dir outputs/run_001 --codebook config/codebook_v0.1.5.json
python -m ifrs18_oras validate-subsample --automatic-item-scores outputs/run_001/item_scores.csv --manual-coding validation/manual_item_scores.csv --output-dir outputs/validation_run_001
```

## Adding company source documents

Use one folder per company. Supported source extensions are `.pdf`, `.xhtml`, `.html`, and `.htm`:

```text
data/raw/Airbus/annual_report_2025.pdf
data/raw/Airbus/esef_annual_report_2025.xhtml
data/raw/Leonardo/annual_report_2025.html
```

Each folder is scored independently and recursively, so nested ESEF package paths such as `data/raw/Airbus/esef/package/report.xhtml` are discovered deterministically. XHTML/HTML/Inline XBRL files are parsed natively with the required `lxml` backend; they are not converted to PDF and there is no silent parser fallback. If `lxml` is unavailable, the XHTML/HTML document is excluded with `xhtml_parser_unavailable`. The extractor removes non-visible script/style/head content and Inline XBRL hidden sections before deterministic regex scoring. Duplicate files with the same SHA-256 are excluded within each company folder as `duplicate_sha256`. The scoring command performs no web requests and no default OCR. For EU core scoring, use `--preferred-format xhtml`; allowed values are `all` (default), `xhtml`, and `pdf`.

## Outputs

Each run writes `company_scores.csv`, `company_scores.json`, `dimension_scores.csv`, `item_scores.csv`, `evidence_log.csv`, `extraction_manifest.csv`, `run_manifest.json`, and `html_reports/<company>.html`. Inspect the HTML audit trail to see source-location snippets, matched regex patterns, item scores, document hashes, and the codebook hash. PDF evidence retains page-number locators; XHTML/HTML evidence uses deterministic block indexes and XPath locators where available. XHTML/HTML regex matching is allowed to use a bounded three-block context window over consecutive blocks in the same document, with contributing locators recorded in `context_locators`.

## Scoring formula

`DimensionScore(i,d) = 100 × Σ(ItemWeight(j) × ItemScore(i,j)) / Σ(ItemWeight(j))`, using only applicable items. `IFRS18_ORAS(i) = Σ(DimensionWeight(d) × DimensionScore(i,d)) / Σ(DimensionWeight(d))`, using only applicable main dimensions. `ReportingAdjustmentGap(i) = 100 - IFRS18_ORAS(i)`. Main evidence coverage excludes supplementary IAS 7 dimension D and is the primary coverage metric; `evidence_coverage_pct` remains a backwards-compatible alias for `main_evidence_coverage_pct`.

## Reproducibility protocol

Record the data cut-off, archive input document hashes, run from a clean clone, preserve `run_manifest.json`, and avoid comparing scores from different codebook versions without a comparability warning. The default codebook is `config/codebook_v0.1.5.json`; historical `config/codebook_v0.1.0.json` through `config/codebook_v0.1.4.json` remain available to reproduce earlier pilot runs. Codebook v0.1.5 incorporates validation-calibrated rule refinements for IFRS 18 transition disclosures, MPM/APM evidence, income-statement architecture guardrails, and disaggregation signals, plus a narrow post-merge hotfix for the PR #11 A3 and E5 review comments, while remaining a deterministic observable-alignment screen. The codebook is JSON because it is human-readable, versionable, and dependency-light.

## Limitations

Regex evidence can produce false positives and false negatives; PDF text extraction may fail on scanned or image-only files; XHTML/HTML extraction depends on readable source markup; no IFRS materiality is inferred; MPM detections are only candidates; US GAAP convergence screening should be a future separate construct rather than IFRS readiness.

## Tests

```bash
make install
make verify
```

## Citation

Use `CITATION.cff` as a placeholder and replace author fields before publication.

A technically unreadable source document is not evidence of low IFRS 18 alignment. IFRS18-ORAS reports the company as unscorable when no usable text-native document is available. A zero score means readable documents were analysed and no matching evidence was found; `N/A` means the source package was technically insufficient for automatic scoring. OCR is not applied silently, and replacement text-native PDF, XHTML, HTML, or Inline XBRL sources should be obtained.
The low-text warning threshold is a technical extraction-screening parameter, not an IFRS threshold or materiality threshold.
