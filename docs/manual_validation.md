# Manual-validation workflow

The `validate-subsample` command supports methodological validation of the automated IFRS18-ORAS proxy on a manually coded subsample. It evaluates software output against reviewer-coded item-level labels; it does not validate the accounting correctness of the provisional codebook by itself.

Run:

```bash
python -m ifrs18_oras validate-subsample \
  --automatic-item-scores outputs/run_001/item_scores.csv \
  --manual-coding validation/manual_item_scores.csv \
  --output-dir outputs/validation_run_001
```

The manual-coding CSV must include:

```text
company,item_id,manual_applicable,manual_score,reviewer,review_date,review_note
```

`manual_applicable` accepts true/false style values. `manual_score` accepts `1`, `0.5`, `0`, or `N/A`. Missing manual labels are not hidden: they are counted in `validation_summary.csv` and listed in `disagreement_log.csv`.

Generated files:

- `validation_summary.csv`: coded observations, exact agreement rate, applicability agreement rate, mean absolute score difference, disagreement count, missing manual labels, binary applicability confusion-matrix counts, and Cohen's kappa where defined.
- `validation_by_item.csv`: agreement metrics by codebook item.
- `disagreement_log.csv`: missing labels and score/applicability disagreements with reviewer notes.
- `validation_manifest.json`: paths, timestamp, and summary metrics.

This workflow is intended for transparent validation on a manually reviewed subsample before freezing an empirical codebook.
