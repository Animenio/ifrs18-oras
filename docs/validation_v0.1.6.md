# Validation-Calibrated Notes For v0.1.6

Codebook `config/codebook_v0.1.6.json` is the final validation-calibrated baseline created after PR #12. It preserves `config/codebook_v0.1.5.json` as the historical post-PR-12 version while versioning the score-affecting A3 and E5 hotfixes into a new reproducible baseline.

Relative to v0.1.5, v0.1.6 keeps the A3 collective wording fix for `statement of profit or loss ... operating, investing and financing categories` and restores direct E5 IFRS 18 expected-impact matches such as `IFRS 18 has an expected material impact` and `IFRS 18 is expected to have a material impact`, while continuing to reject generic unanchored `The new standard will not have a material impact` wording.

The calibration remains deterministic and auditable. It does not hardcode company-specific scores and does not change the observable-alignment boundary of IFRS18-ORAS.
