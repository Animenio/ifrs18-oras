# Methodological positioning of IFRS18-ORAS

## 1. Purpose of the search

This search was conducted before any empirical use of IFRS18-ORAS in order to position the instrument conservatively within prior literature and to avoid overstating novelty. The question was not whether prior research has used automation in general, but whether Business, Management, Accounting, or adjacent Social Sciences literature has already used automated textual analysis, content analysis, NLP, machine learning, dictionary-based or rule-based scoring, disclosure indices, or machine-readable reporting files in ways that are methodologically comparable to IFRS18-ORAS.

The aim is therefore methodological rather than promotional. If comparable traditions already exist, IFRS18-ORAS should be presented as building on them. If no exact prior configuration is found, that absence should be stated narrowly and only within the reviewed search corpus.

## 2. Search levels and corpus

Three structured Scopus search levels were reviewed.

Level 1 captured broad automated textual-analysis, disclosure-analysis, and NLP-related research on corporate reporting and related disclosures. It contained 2,475 records, of which 2,470 remained after within-level deduplication.

Level 2 captured XBRL, Inline XBRL, ESEF, XHTML, XML, and other machine-readable reporting research. It contained 160 records, with no within-level duplicates removed.

Level 3 captured IFRS 18, management performance measures, operating-income, and closely related standard-adoption material. It contained 10 records, with no within-level duplicates removed.

Across all three levels, the combined corpus contained 2,645 records and 2,633 deduplicated records after DOI-first and normalized-title fallback matching. The combined year range was 2001-2026. The corpus is broad, but it is not methodologically empty: it contains substantial prior work on automated reading of disclosures, content-analysis protocols, dictionary-based measurement, machine-learning classification, and machine-readable filing environments.

## 3. Automated textual analysis in disclosure research

The Level 1 corpus shows that automated textual analysis is already well established in disclosure research. Selected papers in the corpus examine readability, tone, textual complexity, topic structure, and predictive content in annual reports, 10-K filings, and other reporting narratives. Examples include `Measuring readability in financial disclosures` (2014), `Textual analysis and international financial reporting: Large sample evidence` (2015), and `The information content of forward-looking statements in corporate filings - A naive Bayesian machine learning approach` (2010).

Methodologically, these studies matter because they normalize narrative reporting text, convert it into analyzable features, and use those features to measure observable reporting constructs. This means IFRS18-ORAS does not introduce automation into disclosure research for the first time. Rather, it enters an established literature in which machine-assisted reading of financial-reporting narratives is already accepted, provided that the construct being measured is clearly specified.

## 4. Rule-based and dictionary-based disclosure measurement

The reviewed corpus also shows a clear methodological tradition of transparent, codified textual measurement. `The Use of Word Lists in Textual Analysis` (2015), `Disclosure Sentiment: Machine Learning vs. Dictionary Methods` (2022), and `Lifting the lid on the use of content analysis to investigate intellectual capital disclosures` (2007) are especially useful here. Together, they show that dictionary-based, word-list-based, and structured content-analysis approaches are methodologically acceptable when researchers define the construct carefully, disclose the coding logic, and treat the output as a measurable proxy rather than as direct legal truth.

That point is central for IFRS18-ORAS. Its logic is not that keyword rules are perfect, but that a transparent and version-controlled rule system can be preferable to opaque classification where auditability and replication matter. A codebook-based protocol is methodologically defensible when the matching rules, applicability rules, exclusions, and limitations are visible, versioned, and open to validation.

## 5. Machine-readable reporting, XBRL and ESEF

The Level 2 corpus provides strong support for treating machine-readable reporting files as a legitimate empirical input. The selected set includes `The production and use of semantically rich accounting reports on the Internet: XML and XBRL` (2001), `Measuring accounting reporting complexity with XBRL` (2018), and `The roles of XBRL and processed XBRL in 10-K readability` (2022). These papers do not replicate IFRS18-ORAS, but they show that XBRL and related digital reporting formats are not peripheral artifacts. They are themselves analyzable reporting objects that can be used to study reporting structure, complexity, transparency, and information effects.

This is especially important for IFRS18-ORAS because the instrument is designed to operate across both PDF reporting packages and native ESEF/XHTML reporting packages. The methodological value of native machine-readable filings is that they can preserve structural reporting signals that may be noisier or harder to trace in PDF alone. Prior literature therefore supports the inclusion of ESEF/XHTML as evidence input, even if the reviewed corpus does not reveal a prior paper that combines this with IFRS 18-specific ex ante scoring.

## 6. IFRS 18 as an emerging research setting

The Level 3 corpus is small. That matters. It suggests that IFRS 18 remains an emerging setting rather than a mature literature with standardized empirical designs. The strongest directly related items in the reviewed set concern management performance measures, operating income, non-GAAP reporting under IFRS, and the informational role of earnings subtotals. Examples include `Boundaries of management performance measures (MPMs) disclosed in primary financial statements prepared in accordance with new standard planned to supersede IAS 1` (2024), `Discretionary reporting and analyst forecasts of operating income under IFRS` (2025), `Non-GAAP Disclosure Empirical and Institutional Perspectives under IFRS` (2025), and `Does IFRS 18 Operating Income Improve the Earnings Response Coefficient?` (2026).

These papers support the substantive relevance of IFRS 18, MPMs, and operating-income presentation, but they do not amount to a mature methodological replication of IFRS18-ORAS. They are closer to conceptual, institutional, and capital-markets studies than to a documentary screening protocol that traces observable reporting alignment item by item.

## 7. Gap and contribution

The reviewed literature supports a conservative middle position. IFRS18-ORAS is not methodologically ungrounded. The component traditions already exist: automated textual analysis, structured disclosure scoring, dictionary-based measurement, and machine-readable filing analysis are all present in the corpus. At the same time, the reviewed search does not reveal an exact prior study that operationalises the same bundle of features as IFRS18-ORAS.

Within the structured Scopus searches reviewed for this study, no prior work was identified that operationalises an ex ante, rule-based and audit-traceable score of observable documentary alignment with IFRS 18 using both PDF reporting packages and native ESEF/XHTML filings.

Accordingly, the most defensible positioning is that IFRS18-ORAS is methodologically grounded but substantively original. The novelty claim should remain narrow: it concerns the specific institutional adaptation and audit-traceable implementation of existing methodological traditions, not the invention of automated disclosure analysis as such.

## 8. Implications for empirical use of IFRS18-ORAS

IFRS18-ORAS builds on established traditions of automated disclosure analysis and dictionary-based textual measurement, while adapting them to the specific institutional context of IFRS 18. Its contribution is not the use of automation per se, but the development of a transparent, version-controlled and audit-traceable scoring protocol that captures observable documentary alignment with IFRS 18 across both PDF and native ESEF/XHTML reporting packages.

IFRS18-ORAS is an ex ante screening tool for observable documentary alignment, not a legal compliance assessment.

Before the empirical EU pilot, the following conditions should be verified and documented:

- CI should be green on the target branch.
- The operative codebook should remain version-controlled, with v0.1.1 available as default and earlier versions preserved.
- Each run should preserve an audit trail including source-file provenance, hashes, command line, timestamps, and evidence logs.
- Evidence-log outputs should be reviewed manually before substantive interpretation.
- A manually validated subsample should be used to assess false positives, false negatives, and applicability-rule behavior.
- Any empirical conclusions should be phrased cautiously, because documentary alignment is narrower than legal compliance, implementation readiness, or reporting quality in the broad sense.

## 9. Selected methodological precedents

| Paper | Area | Method | Data source | Output / construct | Relevance to IFRS18-ORAS | Limitation |
| --- | --- | --- | --- | --- | --- | --- |
| Measuring readability in financial disclosures (2014) | Automated textual analysis | Readability-based textual analysis | 10-K filings / corporate filings | Textual complexity | Shows that narrative features in reporting documents can be measured systematically. | Readability is not the same as item-level IFRS 18 alignment. |
| Textual analysis and international financial reporting: Large sample evidence (2015) | Automated textual analysis in accounting | Automated textual analysis | Annual reports | Reporting-text attributes in an IFRS setting | Connects computational textual analysis directly to international financial reporting research. | Broader reporting constructs than IFRS 18 observables. |
| Lifting the lid on the use of content analysis to investigate intellectual capital disclosures (2007) | Disclosure scoring / content analysis | Structured content analysis | Annual reports | Disclosure quantity / quality proxy | Supports systematic coding of disclosures from annual-report text. | Focuses on intellectual-capital disclosure rather than IFRS 18 presentation rules. |
| Saudi Banks Level of Compliance with Accounting Standards of Accounting and Auditing Organization for Islamic Financial Institutions (2023) | Compliance scoring | Content-analysis checklist | Annual reports | Disclosure compliance level | Shows that standards-based documentary compliance/readiness scoring is methodologically familiar. | Different institutional regime and not automated at the PDF plus ESEF level. |
| The Use of Word Lists in Textual Analysis (2015) | Dictionary-based measurement | Word-list / dictionary method | 10-K filings / corporate filings | Tone-related textual construct | Supports transparent dictionary protocols as legitimate measurement tools. | Generic methodological foundation, not an IFRS 18 application. |
| Disclosure Sentiment: Machine Learning vs. Dictionary Methods (2022) | Dictionary and ML comparison | Dictionary versus ML comparison | 10-K filings / corporate filings | Disclosure sentiment | Useful for positioning rule-based scoring against black-box alternatives. | Measures sentiment, not documentary alignment with a reporting standard. |
| The information content of forward-looking statements in corporate filings - A naive Bayesian machine learning approach (2010) | Financial disclosure ML / NLP | Naive Bayesian classification | Corporate filings | Informational content in disclosure text | Shows that machine learning on reporting narratives is already established. | Predictive modeling is less audit-traceable than deterministic rule coding. |
| Decision support from financial disclosures with deep neural networks and transfer learning (2017) | Financial disclosure ML / NLP | Deep-learning classification | Corporate disclosures | Decision-support signal from disclosure text | Demonstrates that complex automated analysis of financial disclosures is already in the literature. | Methodological opacity differs from the audit-safe aims of IFRS18-ORAS. |
| The production and use of semantically rich accounting reports on the Internet: XML and XBRL (2001) | Machine-readable reporting | XBRL / XML reporting analysis | XBRL / XML reports | Structured digital-reporting use case | Early foundation for treating machine-readable reports as analyzable accounting artifacts. | Not an IFRS 18 study and not a scoring protocol. |
| Measuring accounting reporting complexity with XBRL (2018) | Machine-readable reporting | XBRL-based structural analysis | 10-K filings / corporate filings | Reporting complexity | Supports the idea that filing structure itself can be measured from machine-readable reports. | Measures complexity rather than IFRS 18 alignment. |
| The roles of XBRL and processed XBRL in 10-K readability (2022) | Machine-readable reporting and textual analysis | XBRL-informed textual analysis | 10-K filings / corporate filings | Readability under machine-readable processing | Particularly relevant to combining text analysis with native structured reporting files. | U.S. 10-K setting, not IFRS 18 or ESEF-specific scoring. |
| Boundaries of management performance measures (MPMs) disclosed in primary financial statements prepared in accordance with new standard planned to supersede IAS 1 (2024) | IFRS 18 / MPM | Standard-analysis and case-based interpretation | Financial statements / standard materials | MPM boundary / presentation construct | Directly relevant to the IFRS 18 MPM concept that underlies one dimension of IFRS18-ORAS. | Conceptual boundary study, not automated measurement. |
| Discretionary reporting and analyst forecasts of operating income under IFRS (2025) | IFRS operating-income reporting | Empirical analysis of subtotal reporting | IFRS reporting setting | Operating-income reporting effects | Substantively close to the operating-income rationale behind IFRS 18. | Studies market effects, not documentary alignment scoring. |
| Non-GAAP Disclosure Empirical and Institutional Perspectives under IFRS (2025) | IFRS non-GAAP / MPM context | Institutional and empirical synthesis | IFRS reporting setting | Non-GAAP disclosure and guideline context | Helps situate IFRS 18 within the broader European non-GAAP and ESMA discussion. | Not an automated scoring design. |
| Does IFRS 18 Operating Income Improve the Earnings Response Coefficient? (2026) | IFRS 18 emerging evidence | Capital-markets test of operating-income presentation | IFRS reporting setting | Value relevance of IFRS 18 operating income | Shows that IFRS 18 is beginning to generate direct empirical work. | Outcome study rather than ex ante documentary screening. |

## 10. Audit-safe positioning statement

IFRS18-ORAS builds on established traditions of automated disclosure analysis, structured content analysis, dictionary-based measurement, and machine-readable reporting research, while adapting those methods to the specific institutional setting of IFRS 18. Within the structured Scopus searches reviewed for this study, no prior work was identified that operationalises an ex ante, rule-based and audit-traceable score of observable documentary alignment with IFRS 18 using both PDF reporting packages and native ESEF/XHTML filings. The tool should therefore be positioned not as a claim to automation novelty in general, but as a transparent and version-controlled screening protocol for observable documentary alignment. IFRS18-ORAS is an ex ante screening tool for observable documentary alignment, not a legal compliance assessment.
