# Methodology

IFRS18-ORAS measures observable documentary alignment in public reporting packages. The construct is narrower than full organisational readiness because it observes only public text, not internal systems, audit evidence, accounting judgements, or legal compliance.

Main dimensions are A profit-or-loss architecture (40), B MPM-candidate disclosure alignment (25), C aggregation/disaggregation and expense disclosure (25), and E transition transparency (10). Supplementary D IAS 7 consequential changes is reported separately and excluded from the principal score.

Formulas:

```text
DimensionScore(i,d) = 100 × Σ(ItemWeight(j) × ItemScore(i,j)) / Σ(ItemWeight(j))
IFRS18_ORAS(i) = Σ(DimensionWeight(d) × DimensionScore(i,d)) / Σ(DimensionWeight(d))
ReportingAdjustmentGap(i) = 100 - IFRS18_ORAS(i)
```

Denominators include only applicable items/dimensions. Item values are 1.0 strong evidence, 0.5 weak evidence, 0.0 absent evidence, and N/A where conditional items are not applicable. Evidence coverage is applicable scored items with at least one evidence match divided by total applicable scored items.

Applicability is deterministic: B requires an MPM-candidate trigger; A5 requires a discontinued-operations trigger; A6 requires an equity-method/associate/joint-venture trigger; C4-C10 require a function-of-expense trigger. The software does not infer IFRS materiality. Any future materiality screen must be labelled a research screening threshold, not an IFRS threshold.

The codebook is stored as JSON because JSON is human-readable, versionable, deterministic to parse with the Python standard library, and dependency-light. Matching uses visible regex patterns stored in the JSON codebook, deterministic text normalisation, and text-native PDF extraction through the installed PyMuPDF package. OCR is not applied by default. Image-only or near-empty PDFs generate low-text warnings; researchers should obtain text-native PDF, XHTML, or XBRL sources.

Codebook v0.1.0 is provisional pending accounting review. IFRS 18 references, item wording, weights, exclusions, strong/weak regex patterns, and triggers require accounting-specialist review before empirical deployment. Regex screening can produce false positives and false negatives, and automated scoring must be validated on a manually reviewed subsample. The demo fixtures validate software behaviour, not accounting validity.

US GAAP firms should not be scored as IFRS readiness by implication; a future separate convergence score may be developed.

A technically unreadable PDF is not evidence of low IFRS 18 alignment. IFRS18-ORAS reports the company as unscorable when no usable text-native document is available. A zero score means readable documents were analysed and no matching evidence was found; `N/A` means the source package was technically insufficient for automatic scoring. OCR is not applied silently, and replacement text-native PDFs, XHTML or XBRL sources should be obtained.
 The low-text warning threshold is a technical extraction-screening parameter, not an IFRS threshold or materiality threshold.
