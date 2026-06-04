# Data dictionary

## company_scores.csv / company_scores.json
- `company`: company folder name.
- `ifrs18_oras_0_100`: principal score.
- `reporting_adjustment_gap_0_100`: 100 minus principal score.
- `evidence_coverage_pct`: backwards-compatible alias for `main_evidence_coverage_pct`.
- `main_evidence_coverage_pct`: percentage of applicable main-score items with evidence.
- `supplementary_D_evidence_coverage_pct`: percentage of applicable supplementary IAS 7 dimension D items with evidence.
- `total_evidence_coverage_pct`: percentage of all applicable items, including supplementary D, with evidence.
- `dimension_A_profit_or_loss`: dimension A score.
- `dimension_B_mpm_candidate`: dimension B score or N/A.
- `dimension_C_disaggregation_expenses`: dimension C score.
- `dimension_E_transition_transparency`: dimension E score.
- `supplementary_D_ias7`: supplementary D score.
- `mpm_candidate_detected`: deterministic trigger flag.
- `function_expenses_detected`: deterministic trigger flag.
- `documents_scored`: count of scoring-eligible source documents used in scoring.
- `company_processing_status`: `ok`, `warning_low_text`, `warning_excluded_documents`, or `unscorable_no_usable_text`.
- `usable_documents`: count of scoring-eligible source documents.
- `excluded_documents`: count of technically unusable source documents excluded from scoring.

## dimension_scores.csv
Company, dimension ID/label, main-score weight, applicable and total item counts, applicable item weight, and dimension score.

## item_scores.csv
Company, item ID, dimension, label, IFRS reference, applicability rule, applicable flag, score, weight, weighted score, evidence count, strongest evidence type, and explanatory note.

## evidence_log.csv
Company, document filename, document SHA-256, item ID, dimension, match type, regex pattern, page number, source format, source locator type, source locator, block index, XPath, matched text, and contextual snippet. PDF rows use page numbers; XHTML/HTML rows write `N/A` for page number and use block/XPath locators.

## extraction_manifest.csv
Company, document filename, SHA-256, source format, MIME type, parser backend, Inline XBRL detection flag, block count, page count, extracted character count, low-text warning flag, processing status, scoring-eligible flag, exclusion reason, and error message. `scoring_eligible=false` means the document was excluded from scoring because it was technically unusable (for example, no extractable text or extraction error).

## run_manifest.json
UTC timestamp, software version, Python version, package versions, platform, codebook filename/version/hash, input and output paths, processed companies, source PDF hashes retained for backwards compatibility, source document hashes, disclaimer, and exact command.


## validation_summary.csv
Manual-validation coded-observation count, exact agreement rate, applicability agreement rate, mean absolute score difference, disagreement count, missing manual labels, applicability confusion-matrix counts, and Cohen's kappa.

## validation_by_item.csv
Item-level coded-observation count, exact agreement rate, and mean absolute score difference.

## disagreement_log.csv
Company, item ID, disagreement issue, automatic applicability and score, manual applicability and score, reviewer, review date, and review note.

## validation_manifest.json
Validation timestamp, input paths, output path, and summary metrics.

A technically unreadable source document is not evidence of low IFRS 18 alignment. IFRS18-ORAS reports the company as unscorable when no usable text-native document is available. A zero score means readable documents were analysed and no matching evidence was found; `N/A` means the source package was technically insufficient for automatic scoring. OCR is not applied silently, and replacement text-native PDF, XHTML, HTML, or Inline XBRL sources should be obtained.

Extraction exclusions include `duplicate_sha256`, `non_preferred_format`, `xhtml_parser_unavailable`, `no_extractable_text`, and `extraction_error`.
