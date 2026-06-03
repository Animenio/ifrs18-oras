from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

EvidenceType = Literal["strong", "weak", "trigger"]


@dataclass
class PatternSet:
    strong: list[str] = field(default_factory=list)
    weak: list[str] = field(default_factory=list)


@dataclass
class ItemConfig:
    id: str
    label: str
    weight: float
    ifrs_reference: str = ""
    applicability_rule: str = "always"
    patterns: PatternSet = field(default_factory=PatternSet)
    explanatory_note: str = ""


@dataclass
class DimensionConfig:
    id: str
    label: str
    items: list[ItemConfig]
    main_score_weight: float | None = None
    supplementary: bool = False


@dataclass
class TriggerConfig:
    mpm_candidate: list[str]
    discontinued_operations: list[str]
    equity_method: list[str]
    function_expenses: list[str]

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "mpm_candidate": self.mpm_candidate,
            "discontinued_operations": self.discontinued_operations,
            "equity_method": self.equity_method,
            "function_expenses": self.function_expenses,
        }


@dataclass
class Codebook:
    name: str
    version: str
    status: str
    methodology_note: str
    triggers: TriggerConfig
    dimensions: list[DimensionConfig]


@dataclass(frozen=True)
class PageText:
    document_filename: str
    document_sha256: str
    page_number: int
    text: str


@dataclass(frozen=True)
class DocumentManifest:
    company: str
    document_filename: str
    sha256: str
    page_count: int
    extracted_character_count: int
    low_text_warning: bool
    processing_status: str
    scoring_eligible: bool
    exclusion_reason: str = ""
    error_message: str = ""


@dataclass(frozen=True)
class Evidence:
    company: str
    document_filename: str
    document_sha256: str
    item_id: str
    dimension: str
    match_type: EvidenceType
    regex_pattern: str
    page_number: int
    matched_text: str
    contextual_snippet: str


@dataclass
class ItemScore:
    company: str
    item_id: str
    dimension: str
    label: str
    ifrs_reference: str
    applicability_rule: str
    applicable: bool
    score: float | None
    weight: float
    weighted_score: float | None
    evidence_count: int
    strongest_evidence_type: str
    explanatory_note: str


@dataclass
class DimensionScore:
    company: str
    dimension_id: str
    dimension_label: str
    dimension_weight_in_main_score: float | None
    applicable_item_count: int
    total_item_count: int
    applicable_item_weight: float
    dimension_score: float | None


@dataclass
class CompanyScore:
    company: str
    ifrs18_oras_0_100: float | None
    reporting_adjustment_gap_0_100: float | None
    evidence_coverage_pct: float | None
    dimension_A_profit_or_loss: float | None = None
    dimension_B_mpm_candidate: float | None = None
    dimension_C_disaggregation_expenses: float | None = None
    dimension_E_transition_transparency: float | None = None
    supplementary_D_ias7: float | None = None
    mpm_candidate_detected: bool = False
    function_expenses_detected: bool = False
    documents_scored: int = 0
    company_processing_status: str = "ok"
    usable_documents: int = 0
    excluded_documents: int = 0


@dataclass
class RunResult:
    company_scores: list[CompanyScore] = field(default_factory=list)
    dimension_scores: list[DimensionScore] = field(default_factory=list)
    item_scores: list[ItemScore] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    manifests: list[DocumentManifest] = field(default_factory=list)
