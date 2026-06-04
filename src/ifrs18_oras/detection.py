from __future__ import annotations

import re
from collections.abc import Iterable

from ifrs18_oras.models import Evidence, PageText


def compile_pattern(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


def contextual_snippet(text: str, start: int, end: int, radius: int = 90) -> str:
    snippet = text[max(0, start - radius) : min(len(text), end + radius)]
    return " ".join(snippet.split())


def find_pattern_evidence(
    *,
    company: str,
    pages: Iterable[PageText],
    item_id: str,
    dimension: str,
    match_type: str,
    patterns: Iterable[str],
    limit_per_pattern: int = 5,
) -> list[Evidence]:
    evidence: list[Evidence] = []
    for pattern in patterns:
        regex = compile_pattern(pattern)
        count = 0
        for page in pages:
            for match in regex.finditer(page.text):
                evidence.append(
                    Evidence(
                        company=company,
                        document_filename=page.document_filename,
                        document_sha256=page.document_sha256,
                        item_id=item_id,
                        dimension=dimension,
                        match_type=match_type,  # type: ignore[arg-type]
                        regex_pattern=pattern,
                        page_number=page.page_number,
                        matched_text=match.group(0),
                        contextual_snippet=contextual_snippet(
                            page.text, match.start(), match.end()
                        ),
                        source_format=page.source_format,
                        source_locator_type=page.source_locator_type,
                        source_locator=page.source_locator,
                        block_index=page.block_index,
                        xpath=page.xpath,
                    )
                )
                count += 1
                if count >= limit_per_pattern:
                    break
            if count >= limit_per_pattern:
                break
    return evidence


def any_pattern(pages: Iterable[PageText], patterns: Iterable[str]) -> bool:
    page_list = list(pages)
    return any(
        compile_pattern(pattern).search(page.text) for pattern in patterns for page in page_list
    )
