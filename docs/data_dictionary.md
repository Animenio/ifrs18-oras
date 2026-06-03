# Data dictionary

## company_scores.csv / company_scores.json
- `company`: company folder name.
- `ifrs18_oras_0_100`: principal score.
- `reporting_adjustment_gap_0_100`: 100 minus principal score.
- `evidence_coverage_pct`: percentage of applicable items with evidence.
- `dimension_A_profit_or_loss`: dimension A score.
- `dimension_B_mpm_candidate`: dimension B score or N/A.
- `dimension_C_disaggregation_expenses`: dimension C score.
- `dimension_E_transition_transparency`: dimension E score.
- `supplementary_D_ias7`: supplementary D score.
- `mpm_candidate_detected`: deterministic trigger flag.
- `function_expenses_detected`: deterministic trigger flag.
- `documents_scored`: count of scoring-eligible PDF documents used in scoring.
- `company_processing_status`: `ok`, `warning_low_text`, `warning_excluded_documents`, or `unscorable_no_usable_text`.
- `usable_documents`: count of scoring-eligible PDFs.
- `excluded_documents`: count of technically unusable PDFs excluded from scoring.

## dimension_scores.csv
Company, dimension ID/label, main-score weight, applicable and total item counts, applicable item weight, and dimension score.

## item_scores.csv
Company, item ID, dimension, label, IFRS reference, applicability rule, applicable flag, score, weight, weighted score, evidence count, strongest evidence type, and explanatory note.

## evidence_log.csv
Company, document filename, document SHA-256, item ID, dimension, match type, regex pattern, page number, matched text, and contextual snippet.

## extraction_manifest.csv
Company, document filename, SHA-256, page count, extracted character count, low-text warning flag, processing status, scoring-eligible flag, exclusion reason, and error message. `scoring_eligible=false` means the document was excluded from scoring because it was technically unusable (for example, no extractable text or extraction error).

## run_manifest.json
UTC timestamp, software version, Python version, package versions, platform, codebook filename/version/hash, input and output paths, processed companies, source PDF hashes, disclaimer, and exact command.


## validation_summary.csv
Manual-validation coded-observation count, exact agreement rate, applicability agreement rate, mean absolute score difference, disagreement count, missing manual labels, applicability confusion-matrix counts, and Cohen's kappa.

## validation_by_item.csv
Item-level coded-observation count, exact agreement rate, and mean absolute score difference.

## disagreement_log.csv
Company, item ID, disagreement issue, automatic applicability and score, manual applicability and score, reviewer, review date, and review note.

## validation_manifest.json
Validation timestamp, input paths, output path, and summary metrics.

A technically unreadable PDF is not evidence of low IFRS 18 alignment. IFRS18-ORAS reports the company as unscorable when no usable text-native document is available. A zero score means readable documents were analysed and no matching evidence was found; `N/A` means the source package was technically insufficient for automatic scoring. OCR is not applied silently, and replacement text-native PDFs, XHTML or XBRL sources should be obtained.
