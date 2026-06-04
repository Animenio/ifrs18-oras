from __future__ import annotations

import csv
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from ifrs18_oras.cli import generate_demo_pdf, generate_fictional_fixture_input
from ifrs18_oras.hashing import sha256_file
from ifrs18_oras.reporting import package_versions

CODEBOOK = "config/codebook_v0.1.0.json"
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ifrs18_oras", *args], text=True, capture_output=True, check=False
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_pyproject_dependencies_are_well_formed() -> None:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["dependencies"] == ["PyMuPDF>=1.24,<2", "lxml>=5.0,<7"]
    assert data["project"]["optional-dependencies"]["dev"] == ["pytest>=8.0", "ruff>=0.5"]
    all_deps = data["project"]["dependencies"] + data["project"]["optional-dependencies"]["dev"]
    assert all(dep and not dep.startswith(">=") for dep in all_deps)


def test_package_versions_has_no_empty_package_key() -> None:
    versions = package_versions()
    assert set(versions) == {"PyMuPDF", "lxml"}
    assert "" not in versions


def test_no_local_dependency_shadowing() -> None:
    forbidden = {"fitz.py", "pymupdf.py", "yaml.py", "pydantic.py"}
    found = {path.name for path in SRC_ROOT.glob("*.py") if path.name in forbidden}
    assert not found


def test_real_pymupdf_backend_is_used() -> None:
    import pymupdf

    module_path = Path(pymupdf.__file__).resolve()
    print(module_path)
    assert not module_path.is_relative_to(SRC_ROOT.resolve())


def test_real_pymupdf_pdf_generation_reopen_hash_and_evidence(tmp_path: Path) -> None:
    import pymupdf

    pdf = tmp_path / "demo.pdf"
    generate_demo_pdf(pdf)
    assert pdf.exists()
    with pymupdf.open(pdf) as doc:
        texts = [page.get_text("text") for page in doc]
    assert any("FICTIONAL SYNTHETIC REPORTING PACKAGE" in text for text in texts)
    digest = sha256_file(pdf)
    input_root = tmp_path / "raw" / "Fictional_Aero_Demo"
    input_root.mkdir(parents=True)
    pdf.replace(input_root / "fictional_reporting_package.pdf")
    out = tmp_path / "out"
    result = run_cli(
        "score",
        "--input-dir",
        str(tmp_path / "raw"),
        "--output-dir",
        str(out),
        "--codebook",
        CODEBOOK,
    )
    assert result.returncode == 0, result.stderr
    manifest = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
    assert digest in manifest["source_pdf_hashes"]
    evidence = read_rows(out / "evidence_log.csv")
    assert evidence
    assert all(int(row["page_number"]) >= 1 for row in evidence)


def test_demo_command_outputs_and_snapshot(tmp_path: Path) -> None:
    out = tmp_path / "demo"
    result = run_cli("demo", "--output-dir", str(out))
    assert result.returncode == 0, result.stderr
    required = [
        "company_scores.csv",
        "company_scores.json",
        "dimension_scores.csv",
        "item_scores.csv",
        "evidence_log.csv",
        "extraction_manifest.csv",
        "run_manifest.json",
        "html_reports/Fictional_Aero_Demo.html",
        "synthetic_input/Fictional_Aero_Demo/fictional_reporting_package.pdf",
    ]
    for rel in required:
        assert (out / rel).exists(), rel
    row = read_rows(out / "company_scores.csv")[0]
    assert row["company"] == "Fictional_Aero_Demo"
    assert float(row["ifrs18_oras_0_100"]) == pytest.approx(100.0)
    assert row["documents_scored"] == "1"
    manifest = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["package_versions"]) == {"PyMuPDF", "lxml"}
    assert manifest["package_versions"]["PyMuPDF"]
    assert manifest["package_versions"]["lxml"]
    assert "" not in manifest["package_versions"]


def test_four_fictional_fixture_golden_outputs(tmp_path: Path) -> None:
    input_root = tmp_path / "fixtures"
    generate_fictional_fixture_input(input_root)
    out = tmp_path / "out"
    result = run_cli(
        "score", "--input-dir", str(input_root), "--output-dir", str(out), "--codebook", CODEBOOK
    )
    assert result.returncode == 0, result.stderr
    rows = {row["company"]: row for row in read_rows(out / "company_scores.csv")}
    expected = {
        "Fictional_High_Alignment": {
            "ifrs18_oras_0_100": "100.0",
            "dimension_B_mpm_candidate": "100.0",
            "documents_scored": "1",
        },
        "Fictional_Partial_Alignment": {
            "ifrs18_oras_0_100": "35.2408",
            "dimension_B_mpm_candidate": "38.0",
            "documents_scored": "1",
        },
        "Fictional_No_MPM_Candidate": {
            "ifrs18_oras_0_100": "80.7778",
            "dimension_B_mpm_candidate": "N/A",
            "documents_scored": "1",
        },
        "Fictional_Low_Text_PDF": {
            "company_processing_status": "unscorable_no_usable_text",
            "ifrs18_oras_0_100": "N/A",
            "reporting_adjustment_gap_0_100": "N/A",
            "evidence_coverage_pct": "N/A",
            "dimension_B_mpm_candidate": "N/A",
            "usable_documents": "0",
            "excluded_documents": "1",
        },
    }
    assert rows.keys() == expected.keys()
    for company, fields in expected.items():
        for field, value in fields.items():
            assert rows[company][field] == value
    assert (
        0
        < float(rows["Fictional_Partial_Alignment"]["ifrs18_oras_0_100"])
        < float(rows["Fictional_High_Alignment"]["ifrs18_oras_0_100"])
    )
    manifest_rows = {row["company"]: row for row in read_rows(out / "extraction_manifest.csv")}
    assert manifest_rows["Fictional_Low_Text_PDF"]["low_text_warning"] == "True"
    assert manifest_rows["Fictional_Low_Text_PDF"]["scoring_eligible"] == "False"
    assert manifest_rows["Fictional_Low_Text_PDF"]["exclusion_reason"] == "no_extractable_text"
    assert (out / "html_reports" / "Fictional_High_Alignment.html").exists()


def test_repeated_outputs_are_deterministic(tmp_path: Path) -> None:
    input_root = tmp_path / "fixtures"
    generate_fictional_fixture_input(input_root)
    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    for out in [out1, out2]:
        result = run_cli(
            "score",
            "--input-dir",
            str(input_root),
            "--output-dir",
            str(out),
            "--codebook",
            CODEBOOK,
        )
        assert result.returncode == 0, result.stderr
    for rel in [
        "company_scores.csv",
        "dimension_scores.csv",
        "item_scores.csv",
        "evidence_log.csv",
        "extraction_manifest.csv",
    ]:
        assert (out1 / rel).read_text(encoding="utf-8") == (out2 / rel).read_text(encoding="utf-8")


def test_image_only_low_text_warning(tmp_path: Path) -> None:
    import pymupdf

    company = tmp_path / "raw" / "ImageOnly"
    company.mkdir(parents=True)
    doc = pymupdf.open()
    doc.new_page()
    doc.save(company / "blank.pdf")
    doc.close()
    out = tmp_path / "out"
    result = run_cli(
        "score",
        "--input-dir",
        str(tmp_path / "raw"),
        "--output-dir",
        str(out),
        "--codebook",
        CODEBOOK,
    )
    assert result.returncode == 0, result.stderr
    row = read_rows(out / "extraction_manifest.csv")[0]
    assert row["low_text_warning"] == "True"
    assert row["scoring_eligible"] == "False"
    assert row["exclusion_reason"] == "no_extractable_text"
    company = read_rows(out / "company_scores.csv")[0]
    assert company["company_processing_status"] == "unscorable_no_usable_text"
    assert company["ifrs18_oras_0_100"] == "N/A"


def test_invalid_pdf_unscorable_without_crash(tmp_path: Path) -> None:
    company = tmp_path / "raw" / "InvalidOnly"
    company.mkdir(parents=True)
    (company / "invalid.pdf").write_text("not a pdf", encoding="utf-8")
    out = tmp_path / "out"
    result = run_cli(
        "score",
        "--input-dir",
        str(tmp_path / "raw"),
        "--output-dir",
        str(out),
        "--codebook",
        CODEBOOK,
    )
    assert result.returncode == 0, result.stderr
    manifest = read_rows(out / "extraction_manifest.csv")[0]
    assert manifest["processing_status"] == "error"
    assert manifest["scoring_eligible"] == "False"
    score = read_rows(out / "company_scores.csv")[0]
    assert score["company_processing_status"] == "unscorable_no_usable_text"
    assert score["ifrs18_oras_0_100"] == "N/A"


def test_mixed_package_excludes_unusable_and_scores_readable_pdf(tmp_path: Path) -> None:
    company = tmp_path / "raw" / "MixedPackage"
    generate_demo_pdf(company / "readable.pdf")
    (company / "invalid.pdf").write_text("not a pdf", encoding="utf-8")
    out = tmp_path / "out"
    result = run_cli(
        "score",
        "--input-dir",
        str(tmp_path / "raw"),
        "--output-dir",
        str(out),
        "--codebook",
        CODEBOOK,
    )
    assert result.returncode == 0, result.stderr
    manifests = {
        row["document_filename"]: row for row in read_rows(out / "extraction_manifest.csv")
    }
    assert manifests["readable.pdf"]["scoring_eligible"] == "True"
    assert manifests["invalid.pdf"]["scoring_eligible"] == "False"
    score = read_rows(out / "company_scores.csv")[0]
    assert score["company_processing_status"] == "warning_excluded_documents"
    assert score["usable_documents"] == "1"
    assert score["excluded_documents"] == "1"
    assert score["ifrs18_oras_0_100"] != "N/A"


def test_xhtml_esef_package_scores_visible_text_and_excludes_hidden_ixbrl(tmp_path: Path) -> None:
    company = tmp_path / "raw" / "XhtmlIssuer"
    company.mkdir(parents=True)
    report = company / "annual_report.xhtml"
    report.write_text(
        """<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
  <head><title>ignored title</title><style>.x{display:none}</style></head>
  <body>
    <ix:hidden><ix:nonNumeric name="ifrs-full:Description">adjusted EBIT reconciliation tax effect</ix:nonNumeric></ix:hidden>
    <p>Operating profit is presented.</p>
    <p>Profit before financing and income taxes is disclosed. Income tax expense and finance costs are shown.</p>
    <p>IFRS 18 planned adoption is disclosed with an impact assessment.</p>
  </body>
</html>
""",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    result = run_cli(
        "score",
        "--input-dir",
        str(tmp_path / "raw"),
        "--output-dir",
        str(out),
        "--codebook",
        CODEBOOK,
    )
    assert result.returncode == 0, result.stderr
    score = read_rows(out / "company_scores.csv")[0]
    assert score["company"] == "XhtmlIssuer"
    assert score["documents_scored"] == "1"
    assert score["dimension_A_profit_or_loss"] != "N/A"
    assert score["dimension_B_mpm_candidate"] == "N/A"
    manifest_row = read_rows(out / "extraction_manifest.csv")[0]
    assert manifest_row["document_filename"] == "annual_report.xhtml"
    assert manifest_row["scoring_eligible"] == "True"
    run_manifest = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest_row["sha256"] in run_manifest["source_document_hashes"]
    assert run_manifest["source_pdf_hashes"] == []
    evidence_text = (out / "evidence_log.csv").read_text(encoding="utf-8")
    assert "adjusted EBIT" not in evidence_text


def test_mixed_pdf_and_xhtml_package_scores_both_formats(tmp_path: Path) -> None:
    company = tmp_path / "raw" / "MixedFormats"
    generate_demo_pdf(company / "readable.pdf")
    (company / "annual_report.html").write_text(
        "<html><body><p>Operating category, investing category and financing category are traceable.</p></body></html>",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    result = run_cli(
        "score",
        "--input-dir",
        str(tmp_path / "raw"),
        "--output-dir",
        str(out),
        "--codebook",
        CODEBOOK,
    )
    assert result.returncode == 0, result.stderr
    score = read_rows(out / "company_scores.csv")[0]
    assert score["documents_scored"] == "2"
    manifests = {
        row["document_filename"]: row for row in read_rows(out / "extraction_manifest.csv")
    }
    assert manifests["readable.pdf"]["scoring_eligible"] == "True"
    assert manifests["annual_report.html"]["scoring_eligible"] == "True"


def test_company_folder_without_supported_documents_fails_clearly(tmp_path: Path) -> None:
    (tmp_path / "raw" / "NoPdfs").mkdir(parents=True)
    result = run_cli(
        "score",
        "--input-dir",
        str(tmp_path / "raw"),
        "--output-dir",
        str(tmp_path / "out"),
        "--codebook",
        CODEBOOK,
    )
    assert result.returncode == 1
    assert "contains no supported document files" in result.stderr


def test_manual_validation_cli_outputs(tmp_path: Path) -> None:
    auto = tmp_path / "item_scores.csv"
    auto.write_text(
        "company,item_id,applicable,score\nA,A1,True,1.0\nA,A2,True,0.5\nA,B1,False,N/A\n",
        encoding="utf-8",
    )
    manual = tmp_path / "manual.csv"
    manual.write_text(
        "company,item_id,manual_applicable,manual_score,reviewer,review_date,review_note\n"
        "A,A1,True,1.0,R,2026-06-03,agree\n"
        "A,A2,True,1.0,R,2026-06-03,score disagreement\n",
        encoding="utf-8",
    )
    out = tmp_path / "validation"
    result = run_cli(
        "validate-subsample",
        "--automatic-item-scores",
        str(auto),
        "--manual-coding",
        str(manual),
        "--output-dir",
        str(out),
    )
    assert result.returncode == 0, result.stderr
    for rel in [
        "validation_summary.csv",
        "validation_by_item.csv",
        "disagreement_log.csv",
        "validation_manifest.json",
    ]:
        assert (out / rel).exists()
    summary = read_rows(out / "validation_summary.csv")[0]
    assert summary["coded_observations"] == "2"
    assert summary["missing_manual_label_count"] == "1"
