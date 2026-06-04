from __future__ import annotations

import argparse
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ifrs18_oras import DISCLAIMER
from ifrs18_oras.config import load_codebook
from ifrs18_oras.reporting import write_outputs
from ifrs18_oras.scoring import score_input
from ifrs18_oras.validation import validate_subsample

DEFAULT_CODEBOOK = Path("config/codebook_v0.1.1.json")


def _pymupdf() -> Any:
    import pymupdf

    return pymupdf


def utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_score(
    input_dir: Path,
    output_dir: Path,
    codebook_path: Path,
    command: str,
    preferred_format: str = "all",
) -> None:
    result, codebook, codebook_hash = score_input(input_dir, codebook_path, preferred_format)
    write_outputs(
        output_dir=output_dir,
        input_dir=input_dir,
        codebook_path=codebook_path,
        codebook=codebook,
        codebook_hash=codebook_hash,
        result=result,
        command=command,
        timestamp_utc=utc_timestamp(),
    )


def create_pdf(path: Path, pages: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pymupdf = _pymupdf()
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_textbox(pymupdf.Rect(50, 50, 545, 780), text, fontsize=10)
    doc.save(path)
    doc.close()


def generate_demo_pdf(path: Path) -> None:
    create_pdf(path, demo_pages())


def demo_pages() -> list[str]:
    return [
        "FICTIONAL SYNTHETIC REPORTING PACKAGE - NOT A REAL COMPANY REPORT\n"
        "Aero Demo S.p.A. consolidated statement of profit or loss. Operating profit was presented. "
        "Profit before financing and income taxes is disclosed. Operating category, investing category "
        "and financing category are traceable. Income tax expense and finance costs are separately shown. "
        "Discontinued operations are discussed. The result of equity method associates and joint ventures is separately observable.\n"
        "The group presents expenses by function. Cost of sales is shown and notes explain the nature of expenses "
        "included in function line items, including employee benefits, depreciation, amortisation, impairment losses, "
        "and inventory write-downs. Note 7 cross-references line items. Other expenses include litigation settlement and restructuring costs.",
        "Alternative performance measure section: adjusted EBIT is used by management because it provides management's view "
        "of recurring operating performance. The calculation method starts from operating profit and adds restructuring costs. "
        "A reconciliation to IFRS operating profit is provided. Reconciling items are disaggregated between restructuring costs "
        "and impairment losses. Tax effect of reconciling items and non-controlling interest effect are disclosed. "
        "The company explains changes in measures and comparative information.\n"
        "Rendiconto finanziario: interest received classified as investing, interest paid classified as financing, "
        "dividends received classified as investing, dividends paid classified as financing. Indirect cash-flow reconciliation starts from operating profit.",
        "IFRS 18 transition transparency: IFRS 18 is mentioned with planned adoption for annual periods beginning on 1 January 2027. "
        "An impact assessment and implementation project are underway. Affected reporting areas include subtotals, note disclosures, "
        "aggregation and disaggregation, and management-defined performance measure disclosures. Expected qualitative effects are disclosed.",
    ]


def generate_fictional_fixture_input(root: Path) -> None:
    """Generate deterministic fictional reporting packages for tests and validation examples."""
    create_pdf(root / "Fictional_High_Alignment" / "reporting_package.pdf", demo_pages())
    create_pdf(
        root / "Fictional_Partial_Alignment" / "annual_report.pdf",
        [
            "FICTIONAL PARTIAL ALIGNMENT REPORT - NOT A REAL COMPANY REPORT\n"
            "EBIT is presented as a performance subtotal. Tax expense is disclosed. Interest expense is shown. "
            "Other expenses are listed without a detailed explanation. The entity presents expenses by function and reports cost of goods sold. "
            "Staff costs and impairment are mentioned. IFRS 18 adoption is being assessed.",
            "Alternative performance measure disclosure: non-GAAP underlying earnings are described as a performance measure used internally. "
            "A reconciliation table is included, but tax impact details and non-controlling interests are not provided.",
        ],
    )
    create_pdf(
        root / "Fictional_No_MPM_Candidate" / "annual_report.pdf",
        [
            "FICTIONAL STANDARD METRICS REPORT - NOT A REAL COMPANY REPORT\n"
            "Operating profit is presented. Profit before financing and income taxes is disclosed. Operating category, investing category and financing category are traceable. "
            "Income tax expense and finance costs are separately shown. The statement includes expenses by nature. IFRS 18 planned adoption is disclosed with an impact assessment.",
            "Aggregation and disaggregation are discussed in the notes. Other income includes insurance proceeds. No non-standard performance terminology is used.",
        ],
    )
    create_pdf(root / "Fictional_Low_Text_PDF" / "blank.pdf", [""])


def command_validate(args: argparse.Namespace) -> int:
    codebook, digest = load_codebook(args.codebook)
    print(f"Codebook valid: version={codebook.version} sha256={digest}")
    return 0


def command_describe(args: argparse.Namespace) -> int:
    codebook, digest = load_codebook(args.codebook)
    print(f"{codebook.name} version {codebook.version} ({codebook.status})")
    print(f"SHA-256: {digest}")
    print(codebook.methodology_note)
    for dimension in codebook.dimensions:
        role = (
            "supplementary"
            if dimension.supplementary
            else f"main weight {dimension.main_score_weight}"
        )
        print(f"\n{dimension.id} - {dimension.label} [{role}]")
        for item in dimension.items:
            print(
                f"  {item.id}: {item.label} (weight {item.weight}, rule {item.applicability_rule})"
            )
    return 0


def command_score(args: argparse.Namespace) -> int:
    run_score(
        args.input_dir,
        args.output_dir,
        args.codebook,
        " ".join(sys.argv),
        args.preferred_format,
    )
    print(f"Scoring complete. Outputs written to {args.output_dir}")
    print(DISCLAIMER)
    return 0


def command_demo(args: argparse.Namespace) -> int:
    if args.output_dir.exists():
        shutil.rmtree(args.output_dir)
    input_dir = args.output_dir / "synthetic_input" / "Fictional_Aero_Demo"
    generate_demo_pdf(input_dir / "fictional_reporting_package.pdf")
    run_score(
        args.output_dir / "synthetic_input",
        args.output_dir,
        args.codebook,
        " ".join(sys.argv),
    )
    print(f"Demo complete. Synthetic fictional PDF and outputs written to {args.output_dir}")
    return 0


def command_validate_subsample(args: argparse.Namespace) -> int:
    summary = validate_subsample(args.automatic_item_scores, args.manual_coding, args.output_dir)
    print(f"Manual-validation summary written to {args.output_dir}: {summary}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ifrs18-oras")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-codebook")
    validate.add_argument("--codebook", type=Path, required=True)
    validate.set_defaults(func=command_validate)
    describe = sub.add_parser("describe-codebook")
    describe.add_argument("--codebook", type=Path, required=True)
    describe.set_defaults(func=command_describe)
    score = sub.add_parser("score")
    score.add_argument("--input-dir", type=Path, required=True)
    score.add_argument("--output-dir", type=Path, required=True)
    score.add_argument("--codebook", type=Path, required=True)
    score.add_argument("--preferred-format", choices=["all", "xhtml", "pdf"], default="all")
    score.set_defaults(func=command_score)
    demo = sub.add_parser("demo")
    demo.add_argument("--output-dir", type=Path, required=True)
    demo.add_argument("--codebook", type=Path, default=DEFAULT_CODEBOOK)
    demo.set_defaults(func=command_demo)
    subsample = sub.add_parser("validate-subsample")
    subsample.add_argument("--automatic-item-scores", type=Path, required=True)
    subsample.add_argument("--manual-coding", type=Path, required=True)
    subsample.add_argument("--output-dir", type=Path, required=True)
    subsample.set_defaults(func=command_validate_subsample)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
