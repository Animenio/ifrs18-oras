from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Literal

from ifrs18_oras.config import load_codebook
from ifrs18_oras.detection import any_pattern, find_pattern_evidence
from ifrs18_oras.extraction import (
    SUPPORTED_DOCUMENT_EXTENSIONS,
    extract_document,
    mime_type_for_format,
    source_format_for_path,
)
from ifrs18_oras.hashing import sha256_file
from ifrs18_oras.models import (
    Codebook,
    CompanyScore,
    DimensionConfig,
    DimensionScore,
    DocumentManifest,
    Evidence,
    ItemConfig,
    ItemScore,
    PageText,
    RunResult,
)

PreferredFormat = Literal["all", "xhtml", "pdf"]

DIMENSION_COLUMNS = {
    "A": "dimension_A_profit_or_loss",
    "B": "dimension_B_mpm_candidate",
    "C": "dimension_C_disaggregation_expenses",
    "E": "dimension_E_transition_transparency",
    "D": "supplementary_D_ias7",
}


def score_input(
    input_dir: Path, codebook_path: Path, preferred_format: PreferredFormat = "all"
) -> tuple[RunResult, Codebook, str]:
    if preferred_format not in {"all", "xhtml", "pdf"}:
        raise ValueError(f"Unknown preferred format: {preferred_format}")
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    company_dirs = sorted(
        [path for path in input_dir.iterdir() if path.is_dir()], key=lambda p: p.name.lower()
    )
    if not company_dirs:
        raise ValueError(f"No company folders found in input directory: {input_dir}")
    codebook, codebook_hash = load_codebook(codebook_path)
    result = RunResult()
    for company_dir in company_dirs:
        documents = discover_source_documents(company_dir)
        if not documents:
            supported = ", ".join(SUPPORTED_DOCUMENT_EXTENSIONS)
            raise ValueError(
                f"Company folder contains no supported document files ({supported}): {company_dir}"
            )
        pages: list[PageText] = []
        manifests: list[DocumentManifest] = []
        seen_hashes: set[str] = set()
        selected_formats = selected_source_formats(documents, preferred_format)
        for document in documents:
            relative_name = document.relative_to(company_dir).as_posix()
            digest = sha256_file(document)
            source_format = source_format_for_path(document)
            if digest in seen_hashes:
                manifests.append(
                    excluded_manifest(
                        company=company_dir.name,
                        filename=relative_name,
                        digest=digest,
                        source_format=source_format,
                        exclusion_reason="duplicate_sha256",
                    )
                )
                continue
            seen_hashes.add(digest)
            if source_format not in selected_formats:
                manifests.append(
                    excluded_manifest(
                        company=company_dir.name,
                        filename=relative_name,
                        digest=digest,
                        source_format=source_format,
                        exclusion_reason="non_preferred_format",
                    )
                )
                continue
            doc_pages, manifest = extract_document(company_dir.name, document)
            doc_pages = [replace(page, document_filename=relative_name) for page in doc_pages]
            manifest = replace(manifest, document_filename=relative_name)
            if manifest.scoring_eligible:
                pages.extend(doc_pages)
            manifests.append(manifest)
        company_result = score_company(company_dir.name, pages, manifests, codebook)
        result.company_scores.extend(company_result.company_scores)
        result.dimension_scores.extend(company_result.dimension_scores)
        result.item_scores.extend(company_result.item_scores)
        result.evidence.extend(company_result.evidence)
        result.manifests.extend(manifests)
    return result, codebook, codebook_hash


def discover_source_documents(company_dir: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in company_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
        ],
        key=lambda p: p.relative_to(company_dir).as_posix().lower(),
    )


def selected_source_formats(documents: list[Path], preferred_format: PreferredFormat) -> set[str]:
    formats = {source_format_for_path(path) for path in documents}
    has_xhtml = bool(formats & {"xhtml", "html"})
    has_pdf = "pdf" in formats
    if preferred_format == "xhtml" and has_xhtml:
        return {"xhtml", "html"}
    if preferred_format == "pdf" and has_pdf:
        return {"pdf"}
    return {"pdf", "xhtml", "html"}


def excluded_manifest(
    *, company: str, filename: str, digest: str, source_format: str, exclusion_reason: str
) -> DocumentManifest:
    parser_backend = "pymupdf" if source_format == "pdf" else "lxml"
    return DocumentManifest(
        company=company,
        document_filename=filename,
        sha256=digest,
        page_count=0 if source_format == "pdf" else None,
        extracted_character_count=0,
        low_text_warning=False,
        processing_status="excluded",
        scoring_eligible=False,
        exclusion_reason=exclusion_reason,
        error_message="",
        source_format=source_format,
        mime_type=mime_type_for_format(source_format),
        parser_backend=parser_backend,
        inline_xbrl_detected=False,
        block_count=None if source_format == "pdf" else 0,
    )


def company_processing_status(manifests: list[DocumentManifest], has_pages: bool = False) -> str:
    usable_documents = sum(1 for manifest in manifests if manifest.scoring_eligible)
    excluded_documents = len(manifests) - usable_documents
    if usable_documents == 0 and not has_pages:
        return "unscorable_no_usable_text"
    if excluded_documents:
        return "warning_excluded_documents"
    if any(manifest.processing_status == "warning_low_text" for manifest in manifests):
        return "warning_low_text"
    return "ok"


def unscorable_company(
    company: str, manifests: list[DocumentManifest], codebook: Codebook
) -> RunResult:
    result = RunResult()
    for dimension in codebook.dimensions:
        result.dimension_scores.append(
            DimensionScore(
                company=company,
                dimension_id=dimension.id,
                dimension_label=dimension.label,
                dimension_weight_in_main_score=dimension.main_score_weight,
                applicable_item_count=0,
                total_item_count=len(dimension.items),
                applicable_item_weight=0.0,
                dimension_score=None,
            )
        )
        for item in dimension.items:
            result.item_scores.append(
                ItemScore(
                    company=company,
                    item_id=item.id,
                    dimension=dimension.id,
                    label=item.label,
                    ifrs_reference=item.ifrs_reference,
                    applicability_rule=item.applicability_rule,
                    applicable=False,
                    score=None,
                    weight=item.weight,
                    weighted_score=None,
                    evidence_count=0,
                    strongest_evidence_type="N/A",
                    explanatory_note="Company unscorable: no scoring-eligible text-native PDF/XHTML document.",
                )
            )
    result.company_scores.append(
        CompanyScore(
            company=company,
            ifrs18_oras_0_100=None,
            reporting_adjustment_gap_0_100=None,
            evidence_coverage_pct=None,
            main_evidence_coverage_pct=None,
            supplementary_D_evidence_coverage_pct=None,
            total_evidence_coverage_pct=None,
            dimension_A_profit_or_loss=None,
            dimension_B_mpm_candidate=None,
            dimension_C_disaggregation_expenses=None,
            dimension_E_transition_transparency=None,
            supplementary_D_ias7=None,
            mpm_candidate_detected=False,
            function_expenses_detected=False,
            documents_scored=0,
            company_processing_status="unscorable_no_usable_text",
            usable_documents=0,
            excluded_documents=len(manifests),
        )
    )
    return result


def is_applicable(item: ItemConfig, triggers: dict[str, bool]) -> bool:
    rule = item.applicability_rule
    if rule == "always":
        return True
    if rule == "requires_mpm_candidate":
        return triggers["mpm_candidate"]
    if rule == "requires_discontinued_operations":
        return triggers["discontinued_operations"]
    if rule == "requires_equity_method":
        return triggers["equity_method"]
    if rule == "requires_function_expenses":
        return triggers["function_expenses"]
    raise ValueError(f"Unknown applicability rule for {item.id}: {rule}")


def evidence_coverage(
    rows: list[ItemScore], dimensions: list[DimensionConfig], include_supplementary: bool | None
) -> float:
    supplementary_by_dimension = {dimension.id: dimension.supplementary for dimension in dimensions}
    applicable = [
        row
        for row in rows
        if row.applicable
        and (
            include_supplementary is None
            or supplementary_by_dimension[row.dimension] == include_supplementary
        )
    ]
    if not applicable:
        return 0.0
    covered = [row for row in applicable if row.evidence_count > 0]
    return round(100 * len(covered) / len(applicable), 4)


def score_company(
    company: str, pages: list[PageText], manifests: list[DocumentManifest], codebook: Codebook
) -> RunResult:
    status = company_processing_status(manifests, bool(pages))
    usable_documents = sum(1 for manifest in manifests if manifest.scoring_eligible)
    if usable_documents == 0 and pages:
        usable_documents = 1
    excluded_documents = len(manifests) - sum(
        1 for manifest in manifests if manifest.scoring_eligible
    )
    if usable_documents == 0:
        return unscorable_company(company, manifests, codebook)
    triggers = {
        "mpm_candidate": any_pattern(pages, codebook.triggers.mpm_candidate),
        "discontinued_operations": any_pattern(pages, codebook.triggers.discontinued_operations),
        "equity_method": any_pattern(pages, codebook.triggers.equity_method),
        "function_expenses": any_pattern(pages, codebook.triggers.function_expenses),
    }
    result = RunResult()
    by_dimension_items: dict[str, list[ItemScore]] = {}
    all_evidence: list[Evidence] = []
    for dimension in codebook.dimensions:
        by_dimension_items[dimension.id] = []
        for item in dimension.items:
            applicable = is_applicable(item, triggers)
            item_evidence: list[Evidence] = []
            if applicable:
                strong = find_pattern_evidence(
                    company=company,
                    pages=pages,
                    item_id=item.id,
                    dimension=dimension.id,
                    match_type="strong",
                    patterns=item.patterns.strong,
                )
                weak = find_pattern_evidence(
                    company=company,
                    pages=pages,
                    item_id=item.id,
                    dimension=dimension.id,
                    match_type="weak",
                    patterns=item.patterns.weak,
                )
                item_evidence = strong + weak
                score = 1.0 if strong else 0.5 if weak else 0.0
                strongest = "strong" if strong else "weak" if weak else "none"
                weighted = item.weight * score
            else:
                score = None
                strongest = "N/A"
                weighted = None
            all_evidence.extend(item_evidence)
            row = ItemScore(
                company=company,
                item_id=item.id,
                dimension=dimension.id,
                label=item.label,
                ifrs_reference=item.ifrs_reference,
                applicability_rule=item.applicability_rule,
                applicable=applicable,
                score=score,
                weight=item.weight,
                weighted_score=weighted,
                evidence_count=len(item_evidence),
                strongest_evidence_type=strongest,
                explanatory_note=item.explanatory_note,
            )
            result.item_scores.append(row)
            by_dimension_items[dimension.id].append(row)
    result.evidence.extend(
        sorted(
            all_evidence,
            key=lambda e: (
                e.item_id,
                e.document_filename,
                e.source_locator,
                e.page_number or 0,
                e.regex_pattern,
            ),
        )
    )

    dimension_values: dict[str, float | None] = {}
    main_numerator = 0.0
    main_denominator = 0.0
    for dimension in codebook.dimensions:
        rows = by_dimension_items[dimension.id]
        applicable_rows = [row for row in rows if row.applicable]
        weight_sum = sum(row.weight for row in applicable_rows)
        score_sum = sum((row.weighted_score or 0.0) for row in applicable_rows)
        dim_score = round(100 * score_sum / weight_sum, 4) if weight_sum else None
        dimension_values[dimension.id] = dim_score
        if not dimension.supplementary and dim_score is not None:
            main_numerator += (dimension.main_score_weight or 0.0) * dim_score
            main_denominator += dimension.main_score_weight or 0.0
        result.dimension_scores.append(
            DimensionScore(
                company=company,
                dimension_id=dimension.id,
                dimension_label=dimension.label,
                dimension_weight_in_main_score=dimension.main_score_weight,
                applicable_item_count=len(applicable_rows),
                total_item_count=len(rows),
                applicable_item_weight=weight_sum,
                dimension_score=dim_score,
            )
        )
    oras = round(main_numerator / main_denominator, 4) if main_denominator else None
    gap = round(100 - oras, 4) if oras is not None else None
    main_coverage = evidence_coverage(result.item_scores, codebook.dimensions, False)
    supplementary_coverage = evidence_coverage(result.item_scores, codebook.dimensions, True)
    total_coverage = evidence_coverage(result.item_scores, codebook.dimensions, None)
    result.company_scores.append(
        CompanyScore(
            company=company,
            ifrs18_oras_0_100=oras,
            reporting_adjustment_gap_0_100=gap,
            evidence_coverage_pct=main_coverage,
            main_evidence_coverage_pct=main_coverage,
            supplementary_D_evidence_coverage_pct=supplementary_coverage,
            total_evidence_coverage_pct=total_coverage,
            dimension_A_profit_or_loss=dimension_values.get("A"),
            dimension_B_mpm_candidate=dimension_values.get("B"),
            dimension_C_disaggregation_expenses=dimension_values.get("C"),
            dimension_E_transition_transparency=dimension_values.get("E"),
            supplementary_D_ias7=dimension_values.get("D"),
            mpm_candidate_detected=triggers["mpm_candidate"],
            function_expenses_detected=triggers["function_expenses"],
            documents_scored=usable_documents,
            company_processing_status=status,
            usable_documents=usable_documents,
            excluded_documents=excluded_documents,
        )
    )
    return result
