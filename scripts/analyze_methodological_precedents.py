from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

CANONICAL_FIELDS = {
    "title",
    "authors",
    "year",
    "source_title",
    "abstract",
    "author_keywords",
    "index_keywords",
    "doi",
    "cited_by",
    "document_type",
    "link",
    "eid",
}

FIELD_ALIASES = {
    "title": "title",
    "article title": "title",
    "authors": "authors",
    "author full names": "authors",
    "year": "year",
    "source title": "source_title",
    "journal": "source_title",
    "journal title": "source_title",
    "abstract": "abstract",
    "author keywords": "author_keywords",
    "index keywords": "index_keywords",
    "doi": "doi",
    "cited by": "cited_by",
    "citation count": "cited_by",
    "document type": "document_type",
    "link": "link",
    "eid": "eid",
}

FAMILY_DEFINITIONS = {
    "A": {
        "label": "automated textual analysis / NLP / text mining",
        "patterns": [
            r"\btextual analysis\b",
            r"\btext mining\b",
            r"\bnatural language processing\b",
            r"\bnlp\b",
            r"\breadability\b",
            r"\bsentiment\b",
            r"\btone\b",
            r"\blinguistic\b",
            r"\btopic model(?:ing)?\b",
            r"\blatent dirichlet allocation\b",
            r"\bcomputational analysis\b",
            r"\bautomated analysis of financial text\b",
        ],
    },
    "B": {
        "label": "disclosure index / disclosure scoring / content analysis",
        "patterns": [
            r"\bcontent analysis\b",
            r"\bdisclosure index\b",
            r"\bdisclosure score(?:s)?\b",
            r"\bdisclosure scoring\b",
            r"\bdisclosure quality\b",
            r"\btransparency\b",
            r"\balignment\b",
            r"\bcompliance\b",
            r"\breadiness\b",
            r"\bchecklist\b",
        ],
    },
    "C": {
        "label": "dictionary-based / keyword-based / rule-based measurement",
        "patterns": [
            r"\bdictionary\b",
            r"\bword list(?:s)?\b",
            r"\blexicon\b",
            r"\bkeyword-based\b",
            r"\brule-based\b",
            r"\brule based\b",
            r"\bkeyword scoring\b",
            r"\btext analytics\b",
        ],
    },
    "D": {
        "label": "machine learning / supervised classification / BERT / LSTM",
        "patterns": [
            r"\bmachine learning\b",
            r"\bsupervised\b",
            r"\bclassification\b",
            r"\bdeep learning\b",
            r"\bneural network\b",
            r"\bdeep neural\b",
            r"\bbert\b",
            r"\blstm\b",
            r"\bnaive bayes(?:ian)?\b",
            r"\btransfer learning\b",
        ],
    },
    "E": {
        "label": "XBRL / Inline XBRL / ESEF / XHTML / machine-readable reporting",
        "patterns": [
            r"\bxbrl\b",
            r"\bixbrl\b",
            r"\binline xbrl\b",
            r"\besef\b",
            r"\bxhtml\b",
            r"\bmachine-readable\b",
            r"\bmachine readable\b",
            r"\bxml\b",
            r"\btaxonomy\b",
            r"\binstance document\b",
        ],
    },
    "F": {
        "label": "IFRS / standard-adoption / compliance / readiness",
        "patterns": [
            r"\bifrs\b",
            r"\binternational financial reporting standards\b",
            r"\badoption\b",
            r"\bmandatory adoption\b",
            r"\bstandard(?:s)? adoption\b",
            r"\baccounting standard(?:s)?\b",
            r"\breadiness\b",
            r"\bcompliance\b",
        ],
    },
    "G": {
        "label": "IFRS 18 / MPM / operating income / presentation categories",
        "patterns": [
            r"\bifrs 18\b",
            r"\bmanagement performance measure(?:s)?\b",
            r"\bmpm(?:s)?\b",
            r"\boperating income\b",
            r"\boperating profit\b",
            r"\bnon-gaap\b",
            r"\bearnings subtotal(?:s)?\b",
            r"\bprimary financial statements\b",
            r"\bpresentation categor(?:y|ies)\b",
        ],
    },
}

SELECTION_GROUPS = [
    {
        "name": "textual_foundation",
        "target": 2,
        "levels": {"Level 1"},
        "families": {"A", "F"},
        "priority_patterns": [
            r"measuring readability in financial disclosures",
            r"textual analysis and international financial reporting",
            r"the evolution of 10-k textual disclosure",
            r"measuring qualitative information in capital markets research",
        ],
        "include_patterns": [
            r"\breadability\b",
            r"\btextual analysis\b",
            r"\bnarrative disclosure\b",
            r"\bfinancial text\b",
            r"\bqualitative information\b",
            r"\binternational financial reporting\b",
        ],
        "exclude_patterns": [r"\bxbrl\b", r"\bmachine learning\b", r"\bdictionary\b"],
    },
    {
        "name": "disclosure_scoring",
        "target": 2,
        "levels": {"Level 1", "Level 3"},
        "families": {"B"},
        "priority_patterns": [
            r"lifting the lid on the use of content analysis",
            r"saudi banks level of compliance",
            r"how integrated thinking can be detected in management disclosures in annual reports",
            r"the impact of climate risk information disclosure on corporate financing costs",
        ],
        "include_patterns": [
            r"\bcontent analysis\b",
            r"\bdisclosure quality\b",
            r"\bdisclosure score(?:s)?\b",
            r"\bcompliance\b",
            r"\bannual reports?\b",
            r"\bfinancial statements?\b",
        ],
        "exclude_patterns": [r"\bxbrl\b"],
    },
    {
        "name": "dictionary_rule",
        "target": 2,
        "levels": {"Level 1"},
        "families": {"C"},
        "priority_patterns": [
            r"the use of word lists in textual analysis",
            r"disclosure sentiment: machine learning vs\. dictionary methods",
            r"the role of text analytics and information retrieval in the accounting domain",
            r"content analysis of business communication: introducing a german dictionary",
        ],
        "include_patterns": [
            r"\bdictionary\b",
            r"\bword list(?:s)?\b",
            r"\blexicon\b",
            r"\btext analytics\b",
            r"\brule-based\b",
            r"\bkeyword-based\b",
        ],
        "exclude_patterns": [r"\bxbrl\b"],
    },
    {
        "name": "ml_nlp",
        "target": 2,
        "levels": {"Level 1"},
        "families": {"D"},
        "priority_patterns": [
            r"the information content of forward- looking statements in corporate filings",
            r"decision support from financial disclosures with deep neural networks and transfer learning",
            r"what are you saying\? using topic to detect financial misreporting",
            r"a multilabel text classification algorithm for labeling risk factors in sec form 10-k",
        ],
        "include_patterns": [
            r"\bmachine learning\b",
            r"\bnaive bayes(?:ian)?\b",
            r"\bdeep neural\b",
            r"\bbert\b",
            r"\blstm\b",
            r"\btransfer learning\b",
            r"\bclassification\b",
            r"\btopic to detect\b",
        ],
        "exclude_patterns": [r"\bxbrl\b"],
    },
    {
        "name": "xbrl_machine_readable",
        "target": 3,
        "levels": {"Level 2"},
        "families": {"E"},
        "priority_patterns": [
            r"the production and use of semantically rich accounting reports on the internet: xml and xbrl",
            r"measuring accounting reporting complexity with xbrl",
            r"the roles of xbrl and processed xbrl in 10-k readability",
            r"initial evidence on the market impact of the xbrl mandate",
            r"towards the global adoption of xbrl using international financial reporting standards",
        ],
        "include_patterns": [
            r"\bxbrl\b",
            r"\besef\b",
            r"\bxhtml\b",
            r"\binline xbrl\b",
            r"\bxml\b",
        ],
        "exclude_patterns": [],
    },
    {
        "name": "ifrs18_emerging",
        "target": 4,
        "levels": {"Level 3"},
        "families": {"F", "G"},
        "priority_patterns": [
            r"boundaries of management performance measures",
            r"discretionary reporting and analyst forecasts of operating income under ifrs",
            r"does ifrs 18 operating income improve",
            r"non-gaap disclosure empirical and institutional perspectives under ifrs",
            r"ifrs 18 changes in the presentation of categories that shape comprehensive income",
        ],
        "include_patterns": [
            r"\bifrs 18\b",
            r"\bmanagement performance measure(?:s)?\b",
            r"\bmpm(?:s)?\b",
            r"\boperating income\b",
            r"\bnon-gaap\b",
            r"\bearnings subtotal(?:s)?\b",
        ],
        "exclude_patterns": [],
    },
]

TITLE_BONUS_PATTERNS = [
    (r"\bifrs 18\b", 24),
    (r"\bmanagement performance measure(?:s)?\b", 18),
    (r"\boperating income\b", 16),
    (r"\bnon-gaap\b", 15),
    (r"\bxbrl\b", 15),
    (r"\besef\b", 15),
    (r"\btextual analysis\b", 14),
    (r"\bcontent analysis\b", 12),
    (r"\bdictionary\b", 12),
    (r"\brule-based\b", 12),
    (r"\bannual report(?:s)?\b", 10),
    (r"\b10-k\b", 10),
    (r"\bfinancial statement(?:s)?\b", 10),
    (r"\bmachine learning\b", 10),
    (r"\breadability\b", 8),
    (r"\btone\b", 8),
    (r"\bsentiment\b", 8),
]

SOURCE_SCOPE_PATTERNS = [
    r"\bannual report(?:s)?\b",
    r"\b10-k\b",
    r"\bfinancial statement(?:s)?\b",
    r"\bdisclosure(?:s)?\b",
    r"\breport(?:ing|s)?\b",
    r"\bfiling(?:s)?\b",
    r"\bmd&a\b",
    r"\bmanagement discussion\b",
    r"\bxbrl\b",
    r"\besef\b",
    r"\bxhtml\b",
    r"\bifrs 18\b",
    r"\boperating income\b",
    r"\boperating profit\b",
    r"\bmanagement performance measure(?:s)?\b",
]


@dataclass
class Record:
    level: str
    source_file: str
    title: str
    authors: str
    year: int | None
    source_title: str
    abstract: str
    author_keywords: str
    index_keywords: str
    doi: str
    cited_by: int
    document_type: str
    link: str
    eid: str
    normalized_title: str
    combined_text: str
    keyword_list: list[str]
    families: set[str]
    relevance_score: float
    dedupe_key: str
    broad_area: str
    method: str
    data_source: str
    output_construct: str
    relevance_note: str
    limitation_note: str
    similarity_level: str


def normalize_header(value: str) -> str:
    value = value.strip().lower().replace("\ufeff", "")
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_text(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()


def normalize_doi(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = cleaned.removeprefix("https://doi.org/")
    cleaned = cleaned.removeprefix("http://doi.org/")
    return cleaned


def split_keywords(*values: str) -> list[str]:
    keywords: list[str] = []
    for value in values:
        if not value:
            continue
        pieces = [piece.strip() for piece in value.split(";")]
        if len(pieces) == 1 and "|" in value:
            pieces = [piece.strip() for piece in value.split("|")]
        for piece in pieces:
            cleaned = re.sub(r"\s+", " ", piece)
            if cleaned:
                keywords.append(cleaned)
    return keywords


def try_read_rows(path: Path) -> tuple[list[dict[str, str]], list[str], str]:
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    last_error: UnicodeDecodeError | None = None
    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                headers = reader.fieldnames or []
            return rows, headers, encoding
        except UnicodeDecodeError as error:
            last_error = error
    if last_error is None:
        raise ValueError(f"Could not decode {path}")
    raise last_error


def canonical_row(raw_row: dict[str, str], field_map: dict[str, str]) -> dict[str, str]:
    row = {field: "" for field in CANONICAL_FIELDS}
    for original_header, value in raw_row.items():
        canonical_name = field_map.get(normalize_header(original_header))
        if canonical_name:
            row[canonical_name] = (value or "").strip()
    return row


def compile_family_patterns() -> dict[str, list[re.Pattern[str]]]:
    compiled: dict[str, list[re.Pattern[str]]] = {}
    for family, definition in FAMILY_DEFINITIONS.items():
        compiled[family] = [
            re.compile(pattern, re.IGNORECASE) for pattern in definition["patterns"]
        ]
    return compiled


def detect_families(text: str, compiled_patterns: dict[str, list[re.Pattern[str]]]) -> set[str]:
    families: set[str] = set()
    for family, patterns in compiled_patterns.items():
        if any(pattern.search(text) for pattern in patterns):
            families.add(family)
    return families


def matches_any_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def priority_index(text: str, patterns: list[str]) -> int:
    for index, pattern in enumerate(patterns):
        if re.search(pattern, text, re.IGNORECASE):
            return index
    return len(patterns)


def score_record(record: dict[str, str], families: set[str]) -> float:
    title = record["title"].lower()
    combined = " ".join(
        [
            record["title"],
            record["abstract"],
            record["author_keywords"],
            record["index_keywords"],
        ]
    ).lower()
    score = 0.0
    family_weights = {"A": 8, "B": 7, "C": 9, "D": 7, "E": 9, "F": 5, "G": 12}
    score += sum(family_weights.get(family, 0) for family in families)
    for pattern, bonus in TITLE_BONUS_PATTERNS:
        if re.search(pattern, title):
            score += bonus
    if any(re.search(pattern, combined) for pattern in SOURCE_SCOPE_PATTERNS):
        score += 8
    citations = parse_int(record["cited_by"])
    score += min(math.sqrt(max(citations, 0)), 12)
    year = parse_int(record["year"])
    if year:
        score += max(0, (year - 2000) / 10)
    if record["document_type"].lower() == "review":
        score += 2
    if "corporate social responsibility" in combined and "annual report" not in combined:
        score -= 3
    return round(score, 3)


def parse_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def infer_broad_area(record: Record) -> str:
    families = record.families
    if "G" in families:
        return "IFRS 18 / non-GAAP subtotal reporting"
    if "E" in families:
        return "Machine-readable financial reporting"
    if "D" in families:
        return "Financial disclosure ML / NLP"
    if "C" in families:
        return "Dictionary-based disclosure measurement"
    if "B" in families:
        return "Disclosure scoring / content analysis"
    if "A" in families:
        return "Automated textual analysis of reporting narratives"
    if "F" in families:
        return "IFRS adoption and reporting standard effects"
    return "Corporate reporting research"


def infer_method(record: Record) -> str:
    text = record.combined_text
    if "xbrl" in text or "esef" in text or "xhtml" in text:
        if "quality" in text or "taxonomy" in text:
            return "Automated assessment of machine-readable reporting standards"
        return "Machine-readable filing analysis"
    if "dictionary" in text or "word list" in text or "lexicon" in text:
        return "Dictionary-based textual measurement"
    if "rule-based" in text or "keyword-based" in text:
        return "Rule-based keyword scoring"
    if any(
        term in text for term in ["machine learning", "deep neural", "bert", "lstm", "naive bayes"]
    ):
        return "Machine learning / NLP classification"
    if "content analysis" in text:
        return "Structured content analysis"
    if any(
        term in text
        for term in ["textual analysis", "readability", "sentiment", "tone", "topic model"]
    ):
        return "Automated textual analysis"
    if "ifrs 18" in text or "operating income" in text:
        return "IFRS / operating-income reporting analysis"
    return "Disclosure-analysis method"


def infer_data_source(record: Record) -> str:
    text = record.combined_text
    if "10-k" in text:
        return "10-K filings / corporate filings"
    if "annual report" in text:
        return "Annual reports"
    if "xbrl" in text or "ixbrl" in text:
        return "XBRL / iXBRL filings or taxonomies"
    if "esef" in text or "xhtml" in text:
        return "ESEF / XHTML filings"
    if "integrated report" in text:
        return "Integrated reports"
    if "financial statement" in text:
        return "Financial statements"
    if "ifrs" in text:
        return "IFRS reporting setting"
    return "Corporate disclosures"


def infer_output_construct(record: Record) -> str:
    text = record.combined_text
    if "readability" in text:
        return "Readability / textual complexity"
    if "sentiment" in text or "tone" in text:
        return "Disclosure tone / sentiment"
    if "operating income" in text or "earnings subtotal" in text:
        return "Operating-income / subtotal reporting effects"
    if "management performance measure" in text or "mpm" in text:
        return "MPM boundary / presentation construct"
    if "xbrl" in text or "taxonomy" in text:
        return "Filing quality / interoperability / transparency"
    if "compliance" in text or "readiness" in text or "alignment" in text:
        return "Disclosure compliance / readiness / alignment"
    if "content analysis" in text or "disclosure index" in text:
        return "Disclosure quantity / quality index"
    return "Observable disclosure attribute"


def infer_relevance(record: Record) -> str:
    if "G" in record.families:
        return "Closest substantive setting for IFRS 18 subtotals, MPMs, or operating-income presentation."
    if "E" in record.families:
        return (
            "Supports the use of native machine-readable filings as analyzable reporting evidence."
        )
    if "C" in record.families:
        return "Supports transparent keyword or dictionary protocols rather than opaque black-box scoring."
    if "D" in record.families:
        return "Shows that automated classification of disclosure narratives is established in prior literature."
    if "B" in record.families:
        return "Supports structured disclosure scoring and content-analysis approaches for reporting quality."
    if "A" in record.families:
        return "Supports automated extraction of meaning from reporting narratives and filings."
    if "F" in record.families:
        return "Provides institutional context for standard adoption, comparability, or reporting effects under IFRS."
    return "Provides adjacent methodological support for disclosure analysis."


def infer_limitation(record: Record) -> str:
    if "G" in record.families and "ifrs 18" in record.combined_text:
        return "Substantively close but not an automated, audit-traceable PDF plus ESEF scoring protocol."
    if "E" in record.families:
        return "Focuses on filing standards, transparency, or market effects rather than IFRS 18 alignment scoring."
    if "D" in record.families:
        return "Often uses predictive or black-box models rather than deterministic rule-based evidence tracing."
    if "C" in record.families:
        return "Typically measures tone or topic constructs rather than codified IFRS 18 documentary alignment."
    if "B" in record.families:
        return "Usually examines broader disclosure quality or volume rather than item-level IFRS 18 observables."
    if "A" in record.families:
        return "Textual-analysis settings are broader than ex ante IFRS 18 screening."
    if "F" in record.families:
        return "Institutional adoption evidence does not by itself operationalize documentary scoring rules."
    return "Methodologically adjacent but not a direct replication."


def infer_similarity(record: Record) -> str:
    if "G" in record.families or ("E" in record.families and {"B", "C"} & record.families):
        return "high"
    if {"A", "B", "C", "D", "E"} & record.families:
        return "medium"
    return "low"


def build_record(
    level: str,
    source_file: str,
    row: dict[str, str],
    compiled_patterns: dict[str, list[re.Pattern[str]]],
) -> Record:
    combined_text = " ".join(
        [
            row["title"],
            row["abstract"],
            row["author_keywords"],
            row["index_keywords"],
            row["source_title"],
        ]
    ).strip()
    families = detect_families(combined_text, compiled_patterns)
    normalized_title = normalize_text(row["title"])
    doi = normalize_doi(row["doi"])
    keyword_list = split_keywords(row["author_keywords"], row["index_keywords"])
    temp_record = Record(
        level=level,
        source_file=source_file,
        title=row["title"],
        authors=row["authors"],
        year=parse_int(row["year"]) or None,
        source_title=row["source_title"],
        abstract=row["abstract"],
        author_keywords=row["author_keywords"],
        index_keywords=row["index_keywords"],
        doi=doi,
        cited_by=parse_int(row["cited_by"]),
        document_type=row["document_type"],
        link=row["link"],
        eid=row["eid"],
        normalized_title=normalized_title,
        combined_text=combined_text.lower(),
        keyword_list=keyword_list,
        families=families,
        relevance_score=score_record(row, families),
        dedupe_key=doi or normalized_title,
        broad_area="",
        method="",
        data_source="",
        output_construct="",
        relevance_note="",
        limitation_note="",
        similarity_level="low",
    )
    temp_record.broad_area = infer_broad_area(temp_record)
    temp_record.method = infer_method(temp_record)
    temp_record.data_source = infer_data_source(temp_record)
    temp_record.output_construct = infer_output_construct(temp_record)
    temp_record.relevance_note = infer_relevance(temp_record)
    temp_record.limitation_note = infer_limitation(temp_record)
    temp_record.similarity_level = infer_similarity(temp_record)
    return temp_record


def load_level(
    level: str, path: Path, compiled_patterns: dict[str, list[re.Pattern[str]]]
) -> tuple[list[Record], dict[str, object]]:
    raw_rows, headers, encoding = try_read_rows(path)
    normalized_headers = {normalize_header(header): header for header in headers}
    field_map = {
        normalized: FIELD_ALIASES[normalized]
        for normalized in normalized_headers
        if normalized in FIELD_ALIASES
    }
    missing_fields = sorted(CANONICAL_FIELDS - set(field_map.values()))
    records = []
    for raw_row in raw_rows:
        row = canonical_row(raw_row, field_map)
        if not row["title"].strip():
            continue
        records.append(build_record(level, path.name, row, compiled_patterns))
    metadata = {
        "headers": headers,
        "encoding": encoding,
        "missing_fields": missing_fields,
        "record_count": len(records),
    }
    return records, metadata


def deduplicate_records(records: Iterable[Record]) -> list[Record]:
    deduped: dict[str, Record] = {}
    level_rank = {"Level 1": 1, "Level 2": 2, "Level 3": 3}
    for record in records:
        existing = deduped.get(record.dedupe_key)
        if existing is None:
            deduped[record.dedupe_key] = record
            continue
        current_key = (
            level_rank.get(record.level, 0),
            record.relevance_score,
            record.year or 0,
            record.cited_by,
            record.title.lower(),
        )
        existing_key = (
            level_rank.get(existing.level, 0),
            existing.relevance_score,
            existing.year or 0,
            existing.cited_by,
            existing.title.lower(),
        )
        if current_key > existing_key:
            deduped[record.dedupe_key] = record
    return list(deduped.values())


def summarize_level(records: list[Record], deduped_records: list[Record]) -> dict[str, object]:
    years = [record.year for record in records if record.year]
    journal_counts = Counter(record.source_title for record in records if record.source_title)
    keyword_counts = Counter(
        keyword.lower() for record in records for keyword in record.keyword_list
    )
    return {
        "record_count": len(records),
        "deduplicated_count": len(deduped_records),
        "year_min": min(years) if years else "",
        "year_max": max(years) if years else "",
        "top_journals": journal_counts.most_common(10),
        "top_keywords": keyword_counts.most_common(15),
    }


def family_rows(records: list[Record]) -> list[dict[str, object]]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for record in records:
        for family in sorted(record.families):
            counts[(record.level, family)] += 1
    rows = []
    for level, family in sorted(counts):
        rows.append(
            {
                "level": level,
                "family": family,
                "family_label": FAMILY_DEFINITIONS[family]["label"],
                "count": counts[(level, family)],
            }
        )
    return rows


def candidate_rows(records: list[Record]) -> list[Record]:
    scoped_records: list[Record] = []
    for record in records:
        if record.level == "Level 2" or record.level == "Level 3":
            scoped_records.append(record)
            continue
        if record.families & {"A", "B", "C", "D"} and any(
            re.search(pattern, record.combined_text) for pattern in SOURCE_SCOPE_PATTERNS
        ):
            scoped_records.append(record)
    scoped_records.sort(
        key=lambda record: (
            record.level,
            -record.relevance_score,
            -(record.year or 0),
            -record.cited_by,
            record.title.lower(),
        )
    )
    return scoped_records


def select_precedents(records: list[Record]) -> list[Record]:
    selected: list[Record] = []
    seen_keys: set[str] = set()
    sorted_records = sorted(
        records,
        key=lambda record: (
            -record.relevance_score,
            -(record.year or 0),
            -record.cited_by,
            record.title.lower(),
        ),
    )
    for config in SELECTION_GROUPS:
        priority_records = [
            record
            for record in sorted_records
            if record.dedupe_key not in seen_keys
            and record.level in config["levels"]
            and record.families & config["families"]
            and matches_any_pattern(record.title.lower(), config["priority_patterns"])
            and not matches_any_pattern(record.combined_text, config["exclude_patterns"])
        ]
        priority_records.sort(
            key=lambda record: (
                priority_index(record.title.lower(), config["priority_patterns"]),
                -record.relevance_score,
                -(record.year or 0),
                -record.cited_by,
                record.title.lower(),
            )
        )
        fallback_records = [
            record
            for record in sorted_records
            if record.dedupe_key not in seen_keys
            and record.level in config["levels"]
            and record.families & config["families"]
            and matches_any_pattern(record.combined_text, config["include_patterns"])
            and not matches_any_pattern(record.combined_text, config["exclude_patterns"])
        ]
        merged_records = priority_records[:]
        existing_keys = {record.dedupe_key for record in merged_records}
        for record in fallback_records:
            if record.dedupe_key not in existing_keys:
                merged_records.append(record)
                existing_keys.add(record.dedupe_key)
        for record in merged_records[: config["target"]]:
            selected.append(record)
            seen_keys.add(record.dedupe_key)
    for record in sorted_records:
        if len(selected) >= 14:
            break
        if record.dedupe_key in seen_keys:
            continue
        selected.append(record)
        seen_keys.add(record.dedupe_key)
    selected.sort(
        key=lambda record: (
            record.level,
            {"high": 0, "medium": 1, "low": 2}[record.similarity_level],
            -record.relevance_score,
            -(record.year or 0),
            -record.cited_by,
            record.title.lower(),
        )
    )
    return selected


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_level_summary(path: Path, summaries: dict[str, dict[str, object]]) -> None:
    rows = []
    for level in sorted(summaries):
        summary = summaries[level]
        rows.append(
            {
                "level": level,
                "record_count": summary["record_count"],
                "deduplicated_count": summary["deduplicated_count"],
                "year_min": summary["year_min"],
                "year_max": summary["year_max"],
                "top_journals": "; ".join(
                    f"{name} ({count})" for name, count in summary["top_journals"][:5]
                ),
                "top_keywords": "; ".join(
                    f"{name} ({count})" for name, count in summary["top_keywords"][:10]
                ),
            }
        )
    write_csv(
        path,
        rows,
        [
            "level",
            "record_count",
            "deduplicated_count",
            "year_min",
            "year_max",
            "top_journals",
            "top_keywords",
        ],
    )


def write_family_summary(path: Path, rows: list[dict[str, object]]) -> None:
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            row["level"],
            row["family"],
            -int(row["count"]),
        ),
    )
    write_csv(path, sorted_rows, ["level", "family", "family_label", "count"])


def write_candidate_precedents(path: Path, records: list[Record]) -> None:
    rows = []
    for record in records:
        rows.append(
            {
                "level": record.level,
                "family_codes": ",".join(sorted(record.families)),
                "relevance_score": record.relevance_score,
                "year": record.year or "",
                "cited_by": record.cited_by,
                "title": record.title,
                "source_title": record.source_title,
                "doi": record.doi,
                "broad_area": record.broad_area,
                "method": record.method,
                "data_source": record.data_source,
                "output_construct": record.output_construct,
                "relevance_to_ifrs18_oras": record.relevance_note,
                "limitation_for_use": record.limitation_note,
                "similarity_level": record.similarity_level,
                "source_file": record.source_file,
            }
        )
    write_csv(
        path,
        rows,
        [
            "level",
            "family_codes",
            "relevance_score",
            "year",
            "cited_by",
            "title",
            "source_title",
            "doi",
            "broad_area",
            "method",
            "data_source",
            "output_construct",
            "relevance_to_ifrs18_oras",
            "limitation_for_use",
            "similarity_level",
            "source_file",
        ],
    )


def write_selected_precedents(path: Path, records: list[Record]) -> None:
    rows = []
    for record in records:
        rows.append(
            {
                "paper_title": record.title,
                "year": record.year or "",
                "journal_source": record.source_title,
                "broad_area": record.broad_area,
                "method": record.method,
                "data_source": record.data_source,
                "output_construct_measured": record.output_construct,
                "relevance_to_ifrs18_oras": record.relevance_note,
                "limitation_for_use": record.limitation_note,
                "similarity_level": record.similarity_level,
                "doi": record.doi,
                "level": record.level,
                "family_codes": ",".join(sorted(record.families)),
                "relevance_score": record.relevance_score,
                "cited_by": record.cited_by,
            }
        )
    write_csv(
        path,
        rows,
        [
            "paper_title",
            "year",
            "journal_source",
            "broad_area",
            "method",
            "data_source",
            "output_construct_measured",
            "relevance_to_ifrs18_oras",
            "limitation_for_use",
            "similarity_level",
            "doi",
            "level",
            "family_codes",
            "relevance_score",
            "cited_by",
        ],
    )


def write_manifest(
    path: Path,
    inputs: dict[str, Path],
    metadata: dict[str, dict[str, object]],
    summaries: dict[str, dict[str, object]],
    family_summary_rows: list[dict[str, object]],
    selected_records: list[Record],
) -> None:
    manifest = {
        "inputs": {level: str(path_value) for level, path_value in inputs.items()},
        "metadata": metadata,
        "summaries": summaries,
        "family_counts": family_summary_rows,
        "selected_titles": [record.title for record in selected_records],
        "notes": [
            "Deterministic keyword rules rank candidate precedents; final interpretation remains researcher-reviewed.",
            "Deduplication uses DOI where present and normalized title otherwise.",
            "No web requests, random sampling, or LLM APIs are used.",
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level1", type=Path, required=True)
    parser.add_argument("--level2", type=Path, required=True)
    parser.add_argument("--level3", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inputs = {
        "Level 1": args.level1,
        "Level 2": args.level2,
        "Level 3": args.level3,
    }
    compiled_patterns = compile_family_patterns()
    metadata: dict[str, dict[str, object]] = {}
    level_records: dict[str, list[Record]] = {}
    summaries: dict[str, dict[str, object]] = {}

    for level, path in inputs.items():
        records, level_metadata = load_level(level, path, compiled_patterns)
        metadata[level] = level_metadata
        level_records[level] = records
        summaries[level] = summarize_level(records, deduplicate_records(records))

    all_records = [record for records in level_records.values() for record in records]
    deduped_records = deduplicate_records(all_records)
    candidate_records = candidate_rows(deduped_records)
    selected_records = select_precedents(candidate_records)
    family_summary = family_rows(deduped_records)

    output_dir = args.output_dir
    write_level_summary(output_dir / "level_summary.csv", summaries)
    write_family_summary(output_dir / "methodological_families.csv", family_summary)
    write_candidate_precedents(output_dir / "candidate_precedents.csv", candidate_records)
    write_selected_precedents(output_dir / "selected_precedents_table.csv", selected_records)
    write_manifest(
        output_dir / "literature_review_manifest.json",
        inputs,
        metadata,
        summaries,
        family_summary,
        selected_records,
    )
    print(f"Wrote literature review outputs to {output_dir}")
    print(f"Combined records: {len(all_records)}")
    print(f"Deduplicated records: {len(deduped_records)}")
    print(f"Selected precedents: {len(selected_records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
