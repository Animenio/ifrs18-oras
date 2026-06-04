from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from ifrs18_oras.models import Evidence, PageText

XHTML_CONTEXT_WINDOW_BLOCKS = 3
XHTML_CONTEXT_SEPARATOR = "\n"
LOCATOR_SEPARATOR = " | "


@dataclass(frozen=True)
class SearchContext:
    text: str
    page: PageText
    context_block_start: int | None
    context_block_end: int | None
    context_locators: str
    contributing_blocks: tuple[PageText, ...]


def compile_pattern(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


def contextual_snippet(text: str, start: int, end: int, radius: int = 90) -> str:
    snippet = text[max(0, start - radius) : min(len(text), end + radius)]
    return " ".join(snippet.split())


def source_locator(page: PageText) -> str:
    return page.source_locator or (str(page.page_number) if page.page_number is not None else "")


def single_block_context(page: PageText) -> SearchContext:
    return SearchContext(
        text=page.text,
        page=page,
        context_block_start=page.block_index,
        context_block_end=page.block_index,
        context_locators=source_locator(page),
        contributing_blocks=(page,),
    )


def are_consecutive_xhtml_blocks(blocks: tuple[PageText, ...]) -> bool:
    if not blocks or blocks[0].source_format not in {"xhtml", "html"}:
        return False
    first = blocks[0]
    if first.block_index is None:
        return False
    for offset, block in enumerate(blocks):
        if block.document_filename != first.document_filename:
            return False
        if block.document_sha256 != first.document_sha256:
            return False
        if block.source_format != first.source_format:
            return False
        if block.block_index != first.block_index + offset:
            return False
    return True


def xhtml_contexts(pages: list[PageText]) -> Iterable[SearchContext]:
    for start_index, page in enumerate(pages):
        if page.source_format not in {"xhtml", "html"} or page.block_index is None:
            continue
        for window_size in range(2, XHTML_CONTEXT_WINDOW_BLOCKS + 1):
            blocks = tuple(pages[start_index : start_index + window_size])
            if len(blocks) != window_size or not are_consecutive_xhtml_blocks(blocks):
                continue
            locators = LOCATOR_SEPARATOR.join(source_locator(block) for block in blocks)
            yield SearchContext(
                text=XHTML_CONTEXT_SEPARATOR.join(block.text for block in blocks),
                page=page,
                context_block_start=blocks[0].block_index,
                context_block_end=blocks[-1].block_index,
                context_locators=locators,
                contributing_blocks=blocks,
            )


def match_spans_multiple_blocks(context: SearchContext, start: int, end: int) -> bool:
    if len(context.contributing_blocks) <= 1:
        return False
    cursor = 0
    matched_blocks = 0
    for index, block in enumerate(context.contributing_blocks):
        block_start = cursor
        block_end = cursor + len(block.text)
        if start < block_end and end > block_start:
            matched_blocks += 1
        cursor = block_end
        if index < len(context.contributing_blocks) - 1:
            cursor += len(XHTML_CONTEXT_SEPARATOR)
    return matched_blocks > 1


def evidence_from_match(
    *,
    company: str,
    context: SearchContext,
    item_id: str,
    dimension: str,
    match_type: str,
    pattern: str,
    match: re.Match[str],
) -> Evidence:
    page = context.page
    return Evidence(
        company=company,
        document_filename=page.document_filename,
        document_sha256=page.document_sha256,
        item_id=item_id,
        dimension=dimension,
        match_type=match_type,  # type: ignore[arg-type]
        regex_pattern=pattern,
        page_number=page.page_number,
        matched_text=match.group(0),
        contextual_snippet=contextual_snippet(context.text, match.start(), match.end()),
        source_format=page.source_format,
        source_locator_type=page.source_locator_type,
        source_locator=source_locator(page),
        block_index=page.block_index,
        xpath=page.xpath,
        context_block_start=context.context_block_start,
        context_block_end=context.context_block_end,
        context_locators=context.context_locators,
    )


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
    page_list = list(pages)
    evidence: list[Evidence] = []
    for pattern in patterns:
        regex = compile_pattern(pattern)
        count = 0
        seen_context_matches: set[tuple[str, int | None, int | None, str]] = set()
        for page in page_list:
            context = single_block_context(page)
            for match in regex.finditer(context.text):
                evidence.append(
                    evidence_from_match(
                        company=company,
                        context=context,
                        item_id=item_id,
                        dimension=dimension,
                        match_type=match_type,
                        pattern=pattern,
                        match=match,
                    )
                )
                count += 1
                if count >= limit_per_pattern:
                    break
            if count >= limit_per_pattern:
                break
        if count >= limit_per_pattern:
            continue
        for context in xhtml_contexts(page_list):
            for match in regex.finditer(context.text):
                if not match_spans_multiple_blocks(context, match.start(), match.end()):
                    continue
                key = (
                    context.page.document_sha256,
                    context.context_block_start,
                    context.context_block_end,
                    match.group(0),
                )
                if key in seen_context_matches:
                    continue
                seen_context_matches.add(key)
                evidence.append(
                    evidence_from_match(
                        company=company,
                        context=context,
                        item_id=item_id,
                        dimension=dimension,
                        match_type=match_type,
                        pattern=pattern,
                        match=match,
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
    for pattern in patterns:
        regex = compile_pattern(pattern)
        if any(regex.search(page.text) for page in page_list):
            return True
        for context in xhtml_contexts(page_list):
            for match in regex.finditer(context.text):
                if match_spans_multiple_blocks(context, match.start(), match.end()):
                    return True
    return False
