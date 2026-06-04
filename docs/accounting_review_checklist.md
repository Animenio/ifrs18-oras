# Accounting review checklist

- Confirm IFRS 18 references for each item.
- Review item wording against intended construct.
- Review applicability triggers for B, A5, A6, and C4-C10.
- Review strong and weak regex patterns, including English and Italian synonyms.
- Review all item and dimension weights.
- Confirm exclusions and N/A treatment, especially B when no MPM candidate is detected.
- Identify likely false positives and false negatives.
- Confirm APM/MPM candidate wording does not imply legal MPM status.
- Review IAS 7 supplementary D items and their separation from the main score.
- Review E transition-transparency items so they are not presented as completed implementation.
- Approve future codebook revision process, versioning, changelog, tests, and comparability warnings.


## ESEF/XHTML source handling review
- Confirm that native ESEF XHTML/Inline XBRL extraction and hidden-section exclusion are appropriate for the empirical design.
- Confirm whether EU samples should use the recommended `--preferred-format xhtml` setting or default `all` setting.
- Review examples of PDF page locators and XHTML block/XPath locators in the HTML audit trail.
- Confirm that duplicate SHA-256 exclusion and non-preferred-format exclusion are technical source-selection controls, not accounting judgements.
- Interpret `main_evidence_coverage_pct` separately from supplementary IAS 7 dimension D coverage.


## Codebook v0.1.1 review
- Review the corrected `adjusted EBIT(?:DA)?` regex for MPM-candidate triggering and B1 evidence.
- Review the added E2, E3, and E4 IFRS 18 transition-disclosure patterns for false positives and false negatives.
- Review examples where XHTML evidence uses a three-block context window and confirm the joined evidence remains auditable.
