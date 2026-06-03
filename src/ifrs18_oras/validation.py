from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

REQUIRED_MANUAL_COLUMNS = {
    "company",
    "item_id",
    "manual_applicable",
    "manual_score",
    "reviewer",
    "review_date",
    "review_note",
}


def parse_bool(value: str) -> bool | None:
    value = value.strip().lower()
    if value in {"true", "1", "yes", "y"}:
        return True
    if value in {"false", "0", "no", "n"}:
        return False
    if value in {"", "n/a", "na", "none"}:
        return None
    raise ValueError(f"Cannot parse boolean value: {value!r}")


def parse_score(value: str) -> float | None:
    value = value.strip()
    if value.lower() in {"", "n/a", "na", "none"}:
        return None
    parsed = float(value)
    if parsed not in {0.0, 0.5, 1.0}:
        raise ValueError(f"manual_score must be 0, 0.5, 1, or N/A; got {value!r}")
    return parsed


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def cohen_kappa(tp: int, tn: int, fp: int, fn: int) -> float | None:
    total = tp + tn + fp + fn
    if total == 0:
        return None
    observed = (tp + tn) / total
    auto_true = (tp + fp) / total
    auto_false = (fn + tn) / total
    manual_true = (tp + fn) / total
    manual_false = (fp + tn) / total
    expected = auto_true * manual_true + auto_false * manual_false
    if expected == 1:
        return 1.0
    return round((observed - expected) / (1 - expected), 6)


def validate_subsample(
    automatic_item_scores: Path, manual_coding: Path, output_dir: Path
) -> dict[str, object]:
    auto_rows = read_csv(automatic_item_scores)
    manual_rows = read_csv(manual_coding)
    if manual_rows:
        missing_columns = REQUIRED_MANUAL_COLUMNS - set(manual_rows[0])
        if missing_columns:
            raise ValueError(f"Manual coding CSV missing columns: {sorted(missing_columns)}")
    output_dir.mkdir(parents=True, exist_ok=True)
    auto_by_key = {(row["company"], row["item_id"]): row for row in auto_rows}
    manual_by_key = {(row["company"], row["item_id"]): row for row in manual_rows}
    keys = sorted(set(auto_by_key) | set(manual_by_key))

    coded = 0
    exact_agree = 0
    applicability_agree = 0
    score_diffs: list[float] = []
    disagreements: list[dict[str, object]] = []
    missing_manual = 0
    by_item: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    tp = tn = fp = fn = 0

    for company, item_id in keys:
        auto = auto_by_key.get((company, item_id))
        manual = manual_by_key.get((company, item_id))
        if manual is None:
            missing_manual += 1
            disagreements.append(
                {
                    "company": company,
                    "item_id": item_id,
                    "issue": "missing_manual_label",
                    "automatic_applicable": auto.get("applicable") if auto else "missing",
                    "manual_applicable": "missing",
                    "automatic_score": auto.get("score") if auto else "missing",
                    "manual_score": "missing",
                    "reviewer": "",
                    "review_date": "",
                    "review_note": "",
                }
            )
            continue
        coded += 1
        auto_app = parse_bool(auto["applicable"]) if auto else None
        manual_app = parse_bool(manual["manual_applicable"])
        auto_score = parse_score(auto["score"]) if auto and auto["score"] != "N/A" else None
        manual_score = parse_score(manual["manual_score"])
        app_match = auto_app == manual_app
        score_match = auto_score == manual_score
        exact_match = app_match and score_match
        applicability_agree += int(app_match)
        exact_agree += int(exact_match)
        by_item[item_id]["coded"] += 1
        by_item[item_id]["exact_agree"] += int(exact_match)
        if auto_app is True and manual_app is True:
            tp += 1
        elif auto_app is False and manual_app is False:
            tn += 1
        elif auto_app is True and manual_app is False:
            fp += 1
        elif auto_app is False and manual_app is True:
            fn += 1
        if auto_score is not None and manual_score is not None:
            diff = abs(auto_score - manual_score)
            score_diffs.append(diff)
            by_item[item_id]["score_diff_sum"] += diff
            by_item[item_id]["score_diff_n"] += 1
        if not exact_match:
            disagreements.append(
                {
                    "company": company,
                    "item_id": item_id,
                    "issue": "score_or_applicability_disagreement",
                    "automatic_applicable": auto_app,
                    "manual_applicable": manual_app,
                    "automatic_score": auto_score if auto_score is not None else "N/A",
                    "manual_score": manual_score if manual_score is not None else "N/A",
                    "reviewer": manual.get("reviewer", ""),
                    "review_date": manual.get("review_date", ""),
                    "review_note": manual.get("review_note", ""),
                }
            )

    summary = {
        "coded_observations": coded,
        "exact_agreement_rate": round(exact_agree / coded, 6) if coded else "N/A",
        "applicability_agreement_rate": round(applicability_agree / coded, 6) if coded else "N/A",
        "mean_absolute_score_difference": round(sum(score_diffs) / len(score_diffs), 6)
        if score_diffs
        else "N/A",
        "disagreement_count": len(disagreements),
        "missing_manual_label_count": missing_manual,
        "applicability_true_positive": tp,
        "applicability_true_negative": tn,
        "applicability_false_positive": fp,
        "applicability_false_negative": fn,
        "applicability_cohens_kappa": cohen_kappa(tp, tn, fp, fn),
    }
    by_item_rows = []
    for item_id, stats in sorted(by_item.items()):
        coded_n = int(stats["coded"])
        diff_n = int(stats.get("score_diff_n", 0))
        by_item_rows.append(
            {
                "item_id": item_id,
                "coded_observations": coded_n,
                "exact_agreement_rate": round(stats["exact_agree"] / coded_n, 6)
                if coded_n
                else "N/A",
                "mean_absolute_score_difference": round(stats["score_diff_sum"] / diff_n, 6)
                if diff_n
                else "N/A",
            }
        )
    write_csv(output_dir / "validation_summary.csv", [summary], list(summary.keys()))
    write_csv(
        output_dir / "validation_by_item.csv",
        by_item_rows,
        [
            "item_id",
            "coded_observations",
            "exact_agreement_rate",
            "mean_absolute_score_difference",
        ],
    )
    write_csv(
        output_dir / "disagreement_log.csv",
        disagreements,
        [
            "company",
            "item_id",
            "issue",
            "automatic_applicable",
            "manual_applicable",
            "automatic_score",
            "manual_score",
            "reviewer",
            "review_date",
            "review_note",
        ],
    )
    manifest = {
        "timestamp_utc": datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "automatic_item_scores": str(automatic_item_scores),
        "manual_coding": str(manual_coding),
        "output_dir": str(output_dir),
        "summary": summary,
    }
    (output_dir / "validation_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return summary
