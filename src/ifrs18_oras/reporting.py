from __future__ import annotations

import csv
import html
import json
import platform
import sys
from dataclasses import asdict
from importlib import metadata
from pathlib import Path

from ifrs18_oras import DISCLAIMER, __version__
from ifrs18_oras.models import Codebook, RunResult


def package_versions() -> dict[str, str]:
    packages = ["PyMuPDF", "lxml"]
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def none_to_na(value: object) -> object:
    return "N/A" if value is None else value


def write_outputs(
    *,
    output_dir: Path,
    input_dir: Path,
    codebook_path: Path,
    codebook: Codebook,
    codebook_hash: str,
    result: RunResult,
    command: str,
    timestamp_utc: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "html_reports").mkdir(exist_ok=True)
    company_rows = [
        {key: none_to_na(value) for key, value in asdict(row).items()}
        for row in result.company_scores
    ]
    dimension_rows = [
        {key: none_to_na(value) for key, value in asdict(row).items()}
        for row in result.dimension_scores
    ]
    item_rows = [
        {key: none_to_na(value) for key, value in asdict(row).items()} for row in result.item_scores
    ]
    evidence_rows = [
        {key: none_to_na(value) for key, value in asdict(row).items()} for row in result.evidence
    ]
    manifest_rows = [
        {key: none_to_na(value) for key, value in asdict(row).items()} for row in result.manifests
    ]

    write_csv(output_dir / "company_scores.csv", company_rows, list(company_rows[0].keys()))
    (output_dir / "company_scores.json").write_text(
        json.dumps(company_rows, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_csv(output_dir / "dimension_scores.csv", dimension_rows, list(dimension_rows[0].keys()))
    write_csv(output_dir / "item_scores.csv", item_rows, list(item_rows[0].keys()))
    write_csv(
        output_dir / "evidence_log.csv",
        evidence_rows,
        [
            "company",
            "document_filename",
            "document_sha256",
            "item_id",
            "dimension",
            "match_type",
            "regex_pattern",
            "page_number",
            "source_format",
            "source_locator_type",
            "source_locator",
            "block_index",
            "xpath",
            "matched_text",
            "contextual_snippet",
        ],
    )
    write_csv(
        output_dir / "extraction_manifest.csv",
        manifest_rows,
        [
            "company",
            "document_filename",
            "sha256",
            "source_format",
            "mime_type",
            "parser_backend",
            "inline_xbrl_detected",
            "block_count",
            "page_count",
            "extracted_character_count",
            "low_text_warning",
            "processing_status",
            "scoring_eligible",
            "exclusion_reason",
            "error_message",
        ],
    )
    manifest = {
        "timestamp_utc": timestamp_utc,
        "software_version": __version__,
        "python_version": sys.version,
        "package_versions": package_versions(),
        "platform": platform.platform(),
        "codebook_filename": str(codebook_path),
        "codebook_version": codebook.version,
        "codebook_sha256": codebook_hash,
        "input_directory_path": str(input_dir),
        "output_directory_path": str(output_dir),
        "processed_companies": [row.company for row in result.company_scores],
        "source_pdf_hashes": sorted(
            {
                row.sha256
                for row in result.manifests
                if row.document_filename.lower().endswith(".pdf")
            }
        ),
        "source_document_hashes": sorted({row.sha256 for row in result.manifests}),
        "methodological_disclaimer": DISCLAIMER,
        "exact_command": command,
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    for company in [row.company for row in result.company_scores]:
        write_html_company(
            output_dir / "html_reports" / f"{company}.html", company, result, codebook_hash
        )


def write_html_company(path: Path, company: str, result: RunResult, codebook_hash: str) -> None:
    score = next(row for row in result.company_scores if row.company == company)
    dimensions = [row for row in result.dimension_scores if row.company == company]
    items = [row for row in result.item_scores if row.company == company]
    evidence = [row for row in result.evidence if row.company == company]
    manifests = [row for row in result.manifests if row.company == company]
    body = [
        "<html><head><meta charset='utf-8'><title>IFRS18-ORAS audit trail</title>",
        "<style>body{font-family:sans-serif}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:4px}</style>",
        "</head><body>",
        f"<h1>{html.escape(company)} IFRS18-ORAS audit trail</h1>",
        f"<p><strong>Disclaimer:</strong> {html.escape(DISCLAIMER)}</p>",
        f"<p>Main score: {none_to_na(score.ifrs18_oras_0_100)}; adjustment gap: {none_to_na(score.reporting_adjustment_gap_0_100)}; main evidence coverage: {none_to_na(score.main_evidence_coverage_pct)}%; supplementary D evidence coverage: {none_to_na(score.supplementary_D_evidence_coverage_pct)}%; total evidence coverage: {none_to_na(score.total_evidence_coverage_pct)}%</p>",
        f"<p>Company processing status: {html.escape(score.company_processing_status)}; usable documents: {score.usable_documents}; excluded documents: {score.excluded_documents}</p>",
        f"<p>Codebook SHA-256: {html.escape(codebook_hash)}</p>",
        "<h2>Source documents</h2><ul>",
    ]
    for manifest in manifests:
        body.append(
            f"<li>{html.escape(manifest.document_filename)} — {html.escape(manifest.sha256)} — low text: {manifest.low_text_warning} — scoring eligible: {manifest.scoring_eligible} — exclusion reason: {html.escape(manifest.exclusion_reason)}</li>"
        )
    body.extend(
        ["</ul><h2>Dimension scores</h2><table><tr><th>ID</th><th>Label</th><th>Score</th></tr>"]
    )
    for dimension in dimensions:
        body.append(
            f"<tr><td>{dimension.dimension_id}</td><td>{html.escape(dimension.dimension_label)}</td><td>{dimension.dimension_score}</td></tr>"
        )
    body.extend(
        [
            "</table><h2>Item scores</h2><table><tr><th>Item</th><th>Label</th><th>Applicable</th><th>Score</th><th>Evidence</th></tr>"
        ]
    )
    for item in items:
        body.append(
            f"<tr><td>{item.item_id}</td><td>{html.escape(item.label)}</td><td>{item.applicable}</td><td>{item.score}</td><td>{item.evidence_count}</td></tr>"
        )
    body.extend(
        [
            "</table><h2>Evidence</h2><table><tr><th>Item</th><th>Document</th><th>Locator</th><th>Type</th><th>Pattern</th><th>Snippet</th></tr>"
        ]
    )
    for row in evidence:
        body.append(
            "<tr>"
            f"<td>{row.item_id}</td><td>{html.escape(row.document_filename)}</td>"
            f"<td>{html.escape(row.source_locator_type)}: {html.escape(str(row.source_locator or none_to_na(row.page_number)))}</td>"
            f"<td>{row.match_type}</td><td><code>{html.escape(row.regex_pattern)}</code></td>"
            f"<td>{html.escape(row.contextual_snippet)}</td></tr>"
        )
    body.append("</table></body></html>")
    path.write_text("\n".join(body), encoding="utf-8")
