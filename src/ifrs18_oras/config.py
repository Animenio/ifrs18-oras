from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ifrs18_oras.hashing import sha256_file
from ifrs18_oras.models import Codebook, DimensionConfig, ItemConfig, PatternSet, TriggerConfig


def load_codebook(path: Path) -> tuple[Codebook, str]:
    if not path.exists():
        raise FileNotFoundError(f"Codebook does not exist: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        codebook = build_codebook(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON codebook: {exc}") from exc
    validate_codebook_schema(codebook)
    validate_regexes(codebook)
    return codebook, sha256_file(path)


def build_codebook(raw: dict[str, Any]) -> Codebook:
    triggers = TriggerConfig(**raw["triggers"])
    dimensions: list[DimensionConfig] = []
    for dim in raw["dimensions"]:
        items = []
        for item in dim["items"]:
            patterns = PatternSet(**item.get("patterns", {}))
            item_data = {k: v for k, v in item.items() if k != "patterns"}
            items.append(ItemConfig(patterns=patterns, **item_data))
        dim_data = {k: v for k, v in dim.items() if k != "items"}
        dimensions.append(DimensionConfig(items=items, **dim_data))
    return Codebook(
        name=raw["name"],
        version=raw["version"],
        status=raw["status"],
        methodology_note=raw["methodology_note"],
        triggers=triggers,
        dimensions=dimensions,
    )


def validate_codebook_schema(codebook: Codebook) -> None:
    if codebook.status != "provisional_pending_accounting_review":
        raise ValueError(
            "Invalid codebook schema: status must be provisional_pending_accounting_review"
        )
    dim_ids = [dimension.id for dimension in codebook.dimensions]
    if len(dim_ids) != len(set(dim_ids)):
        raise ValueError("Invalid codebook schema: dimension IDs must be unique")
    item_ids = [item.id for dimension in codebook.dimensions for item in dimension.items]
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("Invalid codebook schema: item IDs must be unique")
    for dimension in codebook.dimensions:
        if not dimension.supplementary and (
            dimension.main_score_weight is None or dimension.main_score_weight <= 0
        ):
            raise ValueError(f"dimension weights are malformed for {dimension.id}")
        for item in dimension.items:
            if item.weight <= 0:
                raise ValueError(f"Invalid codebook schema: item {item.id} weight must be positive")


def validate_regexes(codebook: Codebook) -> None:
    patterns: list[str] = []
    for trigger_patterns in codebook.triggers.as_dict().values():
        patterns.extend(trigger_patterns)
    for dimension in codebook.dimensions:
        for item in dimension.items:
            patterns.extend(item.patterns.strong)
            patterns.extend(item.patterns.weak)
    for pattern in patterns:
        try:
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern {pattern!r}: {exc}") from exc
