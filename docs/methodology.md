# Methodology

IFRS18-ORAS measures observable documentary alignment in public reporting packages. The construct is narrower than full organisational readiness because it observes only public text, not internal systems, audit evidence, accounting judgements, or legal compliance.

Main dimensions are A profit-or-loss architecture (40), B MPM-candidate disclosure alignment (25), C aggregation/disaggregation and expense disclosure (25), and E transition transparency (10). Supplementary D IAS 7 consequential changes is reported separately and excluded from the principal score.

Formulas:

```text
DimensionScore(i,d) = 100 × Σ(ItemWeight(j) × ItemScore(i,j)) / Σ(ItemWeight(j))
IFRS18_ORAS(i) = Σ(DimensionWeight(d) × DimensionScore(i,d)) / Σ(DimensionWeight(d))
ReportingAdjustmentGap(i) = 100 - IFRS18_ORAS(i)
```

Denominators include only applicable items/dimensions. Item values are 1.0 strong evidence, 0.5 weak evidence, 0.0 absent evidence, and N/A where conditional items are not applicable. Main evidence coverage is applicable main-score items with at least one evidence match divided by total applicable main-score items. Supplementary D evidence coverage is reported separately because IAS 7 dimension D does not enter the principal IFRS18-ORAS score. `evidence_coverage_pct` is retained as a backwards-compatible alias for main evidence coverage.

Applicability is deterministic: B requires an MPM-candidate trigger; A5 requires a discontinued-operations trigger; A6 requires an equity-method/associate/joint-venture trigger; C4-C10 require a function-of-expense trigger. The software does not infer IFRS materiality. Any future materiality screen must be labelled a research screening threshold, not an IFRS threshold.

The codebook is stored as JSON because JSON is human-readable, versionable, deterministic to parse with the Python standard library, and dependency-light. Matching uses visible regex patterns stored in the JSON codebook, deterministic text normalisation, and text-native PDF extraction through the installed PyMuPDF package, and native XHTML/HTML/Inline XBRL extraction through the required lxml backend. There is no silent standard-library parser fallback during scoring; unavailable lxml produces a controlled manifest exclusion. PDF evidence uses page-number locators, while XHTML/HTML evidence uses deterministic block indexes and XPath locators where available. Recursive source discovery, duplicate SHA-256 exclusion, and `--preferred-format` selection are technical source-selection rules, not scoring rules. OCR is not applied by default. Image-only or near-empty PDFs and empty XHTML/HTML files generate low-text warnings or exclusions; researchers should obtain text-native PDF, XHTML, HTML, or Inline XBRL sources.

Codebook v0.1.0 is provisional pending accounting review. IFRS 18 references, item wording, weights, exclusions, strong/weak regex patterns, and triggers require accounting-specialist review before empirical deployment. Regex screening can produce false positives and false negatives, and automated scoring must be validated on a manually reviewed subsample. The demo fixtures validate software behaviour, not accounting validity.

US GAAP firms should not be scored as IFRS readiness by implication; a future separate convergence score may be developed.

A technically unreadable source document is not evidence of low IFRS 18 alignment. IFRS18-ORAS reports the company as unscorable when no usable text-native document is available. A zero score means readable documents were analysed and no matching evidence was found; `N/A` means the source package was technically insufficient for automatic scoring. OCR is not applied silently, and replacement text-native PDF, XHTML, HTML, or Inline XBRL sources should be obtained.
 The low-text warning threshold is a technical extraction-screening parameter, not an IFRS threshold or materiality threshold.
