from __future__ import annotations

import json
from pathlib import Path

import pytest

from ifrs18_oras.config import load_codebook
from ifrs18_oras.detection import find_pattern_evidence
from ifrs18_oras.extraction import extract_pdf, extract_xhtml, normalize_text
from ifrs18_oras.hashing import sha256_file, sha256_text
from ifrs18_oras.models import PageText
from ifrs18_oras.scoring import is_applicable, score_company

CODEBOOK = Path("config/codebook_v0.1.1.json")
OLD_CODEBOOK = Path("config/codebook_v0.1.0.json")


def test_text_normalisation() -> None:
    assert normalize_text(" A\u00a0  B\r\n C ") == "A B\nC"


def test_sha256_hashing(tmp_path: Path) -> None:
    path = tmp_path / "x.txt"
    path.write_text("abc", encoding="utf-8")
    assert sha256_file(path) == sha256_text("abc")


def test_strong_weak_and_no_match() -> None:
    pages = [PageText("x.pdf", "h", 1, "Operating profit and EBIT")]
    strong = find_pattern_evidence(
        company="C",
        pages=pages,
        item_id="A1",
        dimension="A",
        match_type="strong",
        patterns=[r"\boperating\s+profit\b"],
    )
    weak = find_pattern_evidence(
        company="C",
        pages=pages,
        item_id="A1",
        dimension="A",
        match_type="weak",
        patterns=[r"\bEBIT\b"],
    )
    none = find_pattern_evidence(
        company="C",
        pages=pages,
        item_id="A1",
        dimension="A",
        match_type="strong",
        patterns=[r"not here"],
    )
    assert strong and weak and not none


def write_mutated_codebook(tmp_path: Path, mutate) -> Path:  # type: ignore[no-untyped-def]
    data = json.loads(CODEBOOK.read_text(encoding="utf-8"))
    mutate(data)
    path = tmp_path / "codebook.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_invalid_regex_handling(tmp_path: Path) -> None:
    path = write_mutated_codebook(
        tmp_path,
        lambda data: data["dimensions"][3]["items"][0]["patterns"]["strong"].__setitem__(0, "["),
    )
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        load_codebook(path)


def test_malformed_dimension_weights(tmp_path: Path) -> None:
    path = write_mutated_codebook(
        tmp_path, lambda data: data["dimensions"][0].__setitem__("main_score_weight", 0)
    )
    with pytest.raises(ValueError, match="dimension weights"):
        load_codebook(path)


def test_duplicate_item_ids(tmp_path: Path) -> None:
    def mutate(data: dict) -> None:
        data["dimensions"][0]["items"][1]["id"] = data["dimensions"][0]["items"][0]["id"]

    with pytest.raises(ValueError, match="item IDs must be unique"):
        load_codebook(write_mutated_codebook(tmp_path, mutate))


def test_status_validation(tmp_path: Path) -> None:
    path = write_mutated_codebook(tmp_path, lambda data: data.__setitem__("status", "final"))
    with pytest.raises(ValueError, match="status"):
        load_codebook(path)


def test_codebook_validation_and_deterministic_hash() -> None:
    codebook, digest_one = load_codebook(CODEBOOK)
    _, digest_two = load_codebook(CODEBOOK)
    assert codebook.version == "0.1.1-provisional"
    assert digest_one == digest_two
    assert len(digest_one) == 64


def test_historical_codebook_v0_1_0_still_validates() -> None:
    codebook, digest = load_codebook(OLD_CODEBOOK)
    assert codebook.version == "0.1.0-provisional"
    assert len(digest) == 64


def test_adjusted_ebit_regex_and_mpm_applicability() -> None:
    codebook, _ = load_codebook(CODEBOOK)
    for text in ["Adjusted EBIT", "Adjusted EBITDA"]:
        result = score_company("C", [PageText("x.pdf", "h", 1, text)], [], codebook)
        score = result.company_scores[0]
        items = {row.item_id: row for row in result.item_scores}
        assert score.mpm_candidate_detected
        assert (
            next(row for row in result.dimension_scores if row.dimension_id == "B").dimension_score
            is not None
        )
        assert items["B1"].applicable
        assert items["B1"].strongest_evidence_type == "strong"
    result = score_company("C", [PageText("x.pdf", "h", 1, "Adjusted EBITD")], [], codebook)
    assert not result.company_scores[0].mpm_candidate_detected
    assert (
        next(row for row in result.dimension_scores if row.dimension_id == "B").dimension_score
        is None
    )


def item_score_for_text(item_id: str, text: str) -> float | None:
    codebook, _ = load_codebook(CODEBOOK)
    result = score_company("C", [PageText("x.pdf", "h", 1, text)], [], codebook)
    return next(row for row in result.item_scores if row.item_id == item_id).score


def test_e2_effective_date_patterns() -> None:
    assert (
        item_score_for_text("E2", "IFRS 18 applies to annual periods beginning on 1 January 2027.")
        == 1.0
    )
    assert (
        item_score_for_text(
            "E2",
            "IFRS 18 is effective for annual reporting periods beginning on or after 1 January 2027.",
        )
        == 1.0
    )
    assert item_score_for_text("E2", "The annual report discusses current trading periods.") == 0.0


def test_e3_impact_assessment_patterns() -> None:
    assert item_score_for_text("E3", "The Group is assessing the impact of IFRS 18.") == 1.0
    assert item_score_for_text("E3", "The Group is evaluating the impact of IFRS 18.") == 1.0
    assert (
        item_score_for_text(
            "E3", "IFRS 18 is mentioned and impact appears in another unrelated paragraph."
        )
        == 0.0
    )


def test_e4_affected_reporting_area_patterns() -> None:
    assert (
        item_score_for_text(
            "E4",
            "The impact of IFRS 18 concerns presentation, aggregation, disaggregation and management-defined performance measures.",
        )
        == 1.0
    )
    assert (
        item_score_for_text("E4", "IFRS 18 affects presentation and aggregation requirements.")
        == 1.0
    )
    assert item_score_for_text("E4", "IFRS 18 is a new standard.") == 0.0
    assert (
        item_score_for_text(
            "E4", "Aggregation and presentation are discussed without naming the standard."
        )
        == 0.0
    )


def test_conditional_applicability() -> None:
    codebook, _ = load_codebook(CODEBOOK)
    a5 = next(item for dim in codebook.dimensions for item in dim.items if item.id == "A5")
    assert not is_applicable(
        a5,
        {
            "mpm_candidate": False,
            "discontinued_operations": False,
            "equity_method": False,
            "function_expenses": False,
        },
    )
    assert is_applicable(
        a5,
        {
            "mpm_candidate": False,
            "discontinued_operations": True,
            "equity_method": False,
            "function_expenses": False,
        },
    )


def test_mpm_dimension_exclusion_when_no_trigger() -> None:
    codebook, _ = load_codebook(CODEBOOK)
    result = score_company(
        "C", [PageText("x.pdf", "h", 1, "Operating profit. IFRS 18.")], [], codebook
    )
    b = next(row for row in result.dimension_scores if row.dimension_id == "B")
    assert b.dimension_score is None
    assert not result.company_scores[0].mpm_candidate_detected


def test_discontinued_equity_and_function_conditionals() -> None:
    codebook, _ = load_codebook(CODEBOOK)
    text = "Discontinued operations. Associates. Expenses by function. Cost of sales."
    result = score_company("C", [PageText("x.pdf", "h", 1, text)], [], codebook)
    items = {row.item_id: row for row in result.item_scores}
    assert items["A5"].applicable
    assert items["A6"].applicable
    assert items["C4"].applicable
    assert items["C10"].applicable


def test_formulas_gap_coverage_and_supplementary_d_exclusion() -> None:
    codebook, _ = load_codebook(CODEBOOK)
    text = "Operating profit. Profit before financing and income taxes. Income tax expense. Finance costs. IFRS 18."
    result = score_company("C", [PageText("x.pdf", "h", 1, text)], [], codebook)
    a = next(row for row in result.dimension_scores if row.dimension_id == "A")
    d = next(row for row in result.dimension_scores if row.dimension_id == "D")
    score = result.company_scores[0]
    assert a.dimension_score == pytest.approx(75.7576)
    assert d.dimension_score == pytest.approx(0.0)
    main_without_d = ((40 * a.dimension_score) + (25 * 0) + (10 * 20)) / (40 + 25 + 10)
    assert score.ifrs18_oras_0_100 == pytest.approx(main_without_d, abs=0.0001)
    assert score.reporting_adjustment_gap_0_100 == pytest.approx(100 - score.ifrs18_oras_0_100)
    main_applicable = [row for row in result.item_scores if row.applicable and row.dimension != "D"]
    main_covered = [row for row in main_applicable if row.evidence_count]
    all_applicable = [row for row in result.item_scores if row.applicable]
    all_covered = [row for row in all_applicable if row.evidence_count]
    assert score.evidence_coverage_pct == score.main_evidence_coverage_pct
    assert score.main_evidence_coverage_pct == pytest.approx(
        100 * len(main_covered) / len(main_applicable), abs=0.0001
    )
    assert score.total_evidence_coverage_pct == pytest.approx(
        100 * len(all_covered) / len(all_applicable), abs=0.0001
    )


def test_invalid_pdf_controlled_handling(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pdf"
    bad.write_text("not a real pdf", encoding="utf-8")
    pages, manifest = extract_pdf("Bad", bad)
    assert pages == []
    assert manifest.processing_status == "error"
    assert manifest.low_text_warning


def test_deterministic_scoring_repeated() -> None:
    codebook, _ = load_codebook(CODEBOOK)
    pages = [
        PageText(
            "x.pdf", "h", 1, "Operating profit. IFRS 18. adjusted EBIT reconciliation tax effect"
        )
    ]
    one = score_company("C", pages, [], codebook).company_scores[0].ifrs18_oras_0_100
    two = score_company("C", pages, [], codebook).company_scores[0].ifrs18_oras_0_100
    assert one == two


def test_xhtml_extraction_normalises_visible_text_and_uses_blocks_and_locators(
    tmp_path: Path,
) -> None:
    path = tmp_path / "report.htm"
    pytest.importorskip("lxml")
    path.write_text(
        "<html><body><p>Operating&nbsp;profit</p><script>Hidden adjusted EBIT</script><table><tr><td>IFRS 18</td></tr></table></body></html>",
        encoding="utf-8",
    )
    pages, manifest = extract_xhtml("HtmlCo", path)
    assert manifest.scoring_eligible
    assert manifest.page_count is None
    assert manifest.block_count == len(pages)
    assert pages[0].page_number is None
    assert pages[0].block_index == 1
    assert pages[0].source_locator_type == "xpath_or_block_index"
    assert pages[0].xpath
    visible = " ".join(page.text for page in pages)
    assert "Operating profit" in visible
    assert "IFRS 18" in visible
    assert "Hidden adjusted EBIT" not in visible


def test_missing_lxml_is_controlled_manifest_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ifrs18_oras.extraction as extraction

    path = tmp_path / "report.xhtml"
    path.write_text("<html><body><p>Operating profit</p></body></html>", encoding="utf-8")

    def missing_lxml() -> None:
        raise ImportError("No module named lxml")

    monkeypatch.setattr(extraction, "_lxml_html", missing_lxml)
    pages, manifest = extract_xhtml("HtmlCo", path)
    assert pages == []
    assert manifest.processing_status == "error"
    assert not manifest.scoring_eligible
    assert manifest.exclusion_reason == "xhtml_parser_unavailable"
    assert "lxml parser backend unavailable" in manifest.error_message
