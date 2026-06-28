# Validation-Calibrated Notes For v0.1.5

Codebook `config/codebook_v0.1.5.json` incorporates manual-validation findings from the 10-company European aerospace and defence pilot as general deterministic rule refinements. The calibration is intentionally conservative: it tightens known false-positive paths, restores a narrow set of false negatives, and preserves the observable-alignment boundary of IFRS18-ORAS. After PR #11 merged, the same file received a narrow post-merge hotfix for the unresolved A3 and E5 review comments without changing the codebook identifier. It is now preserved as the historical post-PR-12 version after `config/codebook_v0.1.6.json` was created for the final baseline.

The calibration does not hardcode company-specific scores. It updates reusable pattern logic for IFRS 18 transition transparency, MPM/APM evidence, profit-or-loss architecture guardrails, and disaggregation evidence so that a fresh automatic pilot remains transparent, reproducible, and auditable.

The accompanying validation reference file stores only lightweight company-level manual outcomes that are safe to archive in the repository. It does not include report excerpts, proprietary source text, or any legal/accounting conclusion beyond the manual-validation status recorded for the pilot.
