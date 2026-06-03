# IFRS18-ORAS

IFRS18-ORAS is a deterministic Python research pipeline for calculating the **IFRS 18 Observable Reporting Alignment Score** from text-native public PDF reporting packages. It measures **observable documentary alignment** with selected presentation and disclosure features introduced by IFRS 18 for systematic academic screening and later validation on a manually reviewed subsample.

## Academic boundary

The indicator is not a legal IFRS 18 compliance opinion, audit conclusion, organisational-readiness measure, proof of full IFRS 18 implementation, or proof that a detected alternative performance measure is legally an IFRS 18 management-defined performance measure. Codebook v0.1.0 is `provisional_pending_accounting_review` and must be reviewed by an accounting specialist before empirical deployment. Regex screening can produce false positives and false negatives; demo fixtures validate software behaviour, not accounting validity.

## Repository structure

```text
config/                 JSON scoring codebook
docs/                   methodology, reproducibility, data dictionary, validation, review checklist
src/ifrs18_oras/        package source
tests/                  unit and integration tests
.github/workflows/      CI
```

Do not commit real annual reports, IFRS standard PDFs, proprietary data, or PDFs unless redistribution is permitted. `data/raw/` is ignored.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## CLI examples

```bash
python -m ifrs18_oras validate-codebook --codebook config/codebook_v0.1.0.json
python -m ifrs18_oras describe-codebook --codebook config/codebook_v0.1.0.json
python -m ifrs18_oras demo --output-dir outputs/demo
python -m ifrs18_oras score --input-dir data/raw --output-dir outputs/run_001 --codebook config/codebook_v0.1.0.json
python -m ifrs18_oras validate-subsample --automatic-item-scores outputs/run_001/item_scores.csv --manual-coding validation/manual_item_scores.csv --output-dir outputs/validation_run_001
```

## Adding company PDFs

Use one folder per company:

```text
data/raw/Airbus/annual_report_2025.pdf
data/raw/Airbus/results_release_2025.pdf
data/raw/Leonardo/annual_report_2025.pdf
```

Each folder is scored independently. The scoring command performs no web requests and no default OCR.

## Outputs

Each run writes `company_scores.csv`, `company_scores.json`, `dimension_scores.csv`, `item_scores.csv`, `evidence_log.csv`, `extraction_manifest.csv`, `run_manifest.json`, and `html_reports/<company>.html`. Inspect the HTML audit trail to see page-numbered snippets, matched regex patterns, item scores, document hashes, and the codebook hash.

## Scoring formula

`DimensionScore(i,d) = 100 × Σ(ItemWeight(j) × ItemScore(i,j)) / Σ(ItemWeight(j))`, using only applicable items. `IFRS18_ORAS(i) = Σ(DimensionWeight(d) × DimensionScore(i,d)) / Σ(DimensionWeight(d))`, using only applicable main dimensions. `ReportingAdjustmentGap(i) = 100 - IFRS18_ORAS(i)`.

## Reproducibility protocol

Record the data cut-off, archive input PDF hashes, run from a clean clone, preserve `run_manifest.json`, and avoid comparing scores from different codebook versions without a comparability warning. The codebook is JSON because it is human-readable, versionable, and dependency-light.

## Limitations

Regex evidence can produce false positives and false negatives; PDF text extraction may fail on scanned or image-only files; no IFRS materiality is inferred; MPM detections are only candidates; US GAAP convergence screening should be a future separate construct rather than IFRS readiness.

## Tests

```bash
make install
make verify
```

## Citation

Use `CITATION.cff` as a placeholder and replace author fields before publication.

A technically unreadable PDF is not evidence of low IFRS 18 alignment. IFRS18-ORAS reports the company as unscorable when no usable text-native document is available. A zero score means readable documents were analysed and no matching evidence was found; `N/A` means the source package was technically insufficient for automatic scoring. OCR is not applied silently, and replacement text-native PDFs, XHTML or XBRL sources should be obtained.
 The low-text warning threshold is a technical extraction-screening parameter, not an IFRS threshold or materiality threshold.
