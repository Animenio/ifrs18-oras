from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ifrs18_oras.hashing import sha256_file
from ifrs18_oras.models import DocumentManifest, SourceTextBlock

LOW_TEXT_CHARACTER_THRESHOLD = 50
SUPPORTED_DOCUMENT_EXTENSIONS = (".pdf", ".xhtml", ".html", ".htm")
XHTML_EXTENSIONS = (".xhtml", ".html", ".htm")
_BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "caption",
    "dd",
    "details",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "nav",
    "p",
    "pre",
    "section",
    "summary",
    "td",
    "th",
}
_REMOVED_TAGS = {
    "head",
    "script",
    "style",
    "noscript",
    "template",
    "title",
    "meta",
    "link",
    "svg",
    "canvas",
}


def _pymupdf() -> Any:
    import pymupdf

    return pymupdf


def _lxml_html() -> Any:
    from lxml import html

    return html


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[\t\r\f\v]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()


def source_format_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".xhtml":
        return "xhtml"
    if suffix in {".html", ".htm"}:
        return "html"
    return "unknown"


def mime_type_for_format(source_format: str) -> str:
    if source_format == "pdf":
        return "application/pdf"
    if source_format == "xhtml":
        return "application/xhtml+xml"
    if source_format == "html":
        return "text/html"
    return "application/octet-stream"


def build_manifest(
    *,
    company: str,
    filename: str,
    digest: str,
    page_count: int | None,
    char_count: int,
    processing_status: str,
    error_message: str = "",
    exclusion_reason: str = "",
    source_format: str = "pdf",
    mime_type: str = "application/pdf",
    parser_backend: str = "pymupdf",
    inline_xbrl_detected: bool = False,
    block_count: int | None = None,
) -> DocumentManifest:
    if processing_status == "error":
        return DocumentManifest(
            company=company,
            document_filename=filename,
            sha256=digest,
            page_count=page_count,
            extracted_character_count=char_count,
            low_text_warning=True,
            processing_status="error",
            scoring_eligible=False,
            exclusion_reason=exclusion_reason or "extraction_error",
            error_message=error_message,
            source_format=source_format,
            mime_type=mime_type,
            parser_backend=parser_backend,
            inline_xbrl_detected=inline_xbrl_detected,
            block_count=block_count,
        )
    if char_count == 0:
        return DocumentManifest(
            company=company,
            document_filename=filename,
            sha256=digest,
            page_count=page_count,
            extracted_character_count=char_count,
            low_text_warning=True,
            processing_status="no_extractable_text",
            scoring_eligible=False,
            exclusion_reason="no_extractable_text",
            source_format=source_format,
            mime_type=mime_type,
            parser_backend=parser_backend,
            inline_xbrl_detected=inline_xbrl_detected,
            block_count=block_count,
        )
    if char_count < LOW_TEXT_CHARACTER_THRESHOLD:
        return DocumentManifest(
            company=company,
            document_filename=filename,
            sha256=digest,
            page_count=page_count,
            extracted_character_count=char_count,
            low_text_warning=True,
            processing_status="warning_low_text",
            scoring_eligible=True,
            source_format=source_format,
            mime_type=mime_type,
            parser_backend=parser_backend,
            inline_xbrl_detected=inline_xbrl_detected,
            block_count=block_count,
        )
    return DocumentManifest(
        company=company,
        document_filename=filename,
        sha256=digest,
        page_count=page_count,
        extracted_character_count=char_count,
        low_text_warning=False,
        processing_status="ok",
        scoring_eligible=True,
        source_format=source_format,
        mime_type=mime_type,
        parser_backend=parser_backend,
        inline_xbrl_detected=inline_xbrl_detected,
        block_count=block_count,
    )


def extract_pdf(company: str, path: Path) -> tuple[list[SourceTextBlock], DocumentManifest]:
    digest = sha256_file(path)
    blocks: list[SourceTextBlock] = []
    try:
        pymupdf = _pymupdf()
        with pymupdf.open(path) as doc:
            page_count = doc.page_count
            for index, page in enumerate(doc, start=1):
                text = normalize_text(page.get_text("text"))
                blocks.append(
                    SourceTextBlock(
                        path.name,
                        digest,
                        index,
                        text,
                        source_format="pdf",
                        source_locator_type="page_number",
                        source_locator=str(index),
                    )
                )
        char_count = sum(len(block.text) for block in blocks)
        manifest = build_manifest(
            company=company,
            filename=path.name,
            digest=digest,
            page_count=page_count,
            char_count=char_count,
            processing_status="ok",
            source_format="pdf",
            mime_type="application/pdf",
            parser_backend="pymupdf",
            inline_xbrl_detected=False,
            block_count=None,
        )
        return blocks if manifest.scoring_eligible else [], manifest
    except Exception as exc:  # controlled manifest; caller can continue with other docs
        return [], build_manifest(
            company=company,
            filename=path.name,
            digest=digest,
            page_count=0,
            char_count=0,
            processing_status="error",
            error_message=str(exc),
            source_format="pdf",
            mime_type="application/pdf",
            parser_backend="pymupdf",
            inline_xbrl_detected=False,
            block_count=None,
        )


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1].lower()


def _is_inline_xbrl_element(element: Any) -> bool:
    tag_text = str(element.tag).lower()
    return element.prefix == "ix" or "inlinexbrl" in tag_text or tag_text.startswith("ix:")


def _is_hidden_element(element: Any) -> bool:
    tag = _local_name(element.tag)
    if tag in _REMOVED_TAGS:
        return True
    if tag == "hidden" and _is_inline_xbrl_element(element):
        return True
    attributes = {str(key).lower(): str(value).lower() for key, value in element.attrib.items()}
    if "hidden" in attributes or attributes.get("aria-hidden") == "true":
        return True
    style = attributes.get("style", "").replace(" ", "")
    return "display:none" in style or "visibility:hidden" in style


def _prune_hidden_elements(root: Any) -> None:
    for element in list(root.iter()):
        if element is root:
            continue
        if _is_hidden_element(element):
            parent = element.getparent()
            if parent is not None:
                tail = element.tail or ""
                index = parent.index(element)
                parent.remove(element)
                if tail:
                    if index:
                        previous = parent[index - 1]
                        previous.tail = (previous.tail or "") + tail
                    else:
                        parent.text = (parent.text or "") + tail


def _element_has_block_descendant(element: Any) -> bool:
    for descendant in element.iterdescendants():
        if _local_name(descendant.tag) in _BLOCK_TAGS and normalize_text(descendant.text_content()):
            return True
    return False


def _xpath_for_element(element: Any) -> str:
    try:
        return element.getroottree().getpath(element)
    except Exception:
        return ""


def _extract_visible_xhtml_blocks(
    *,
    root: Any,
    path: Path,
    digest: str,
    source_format: str,
) -> list[SourceTextBlock]:
    blocks: list[SourceTextBlock] = []
    elements = list(root.iter())
    for element in elements:
        if _local_name(element.tag) not in _BLOCK_TAGS:
            continue
        if _element_has_block_descendant(element):
            continue
        text = normalize_text(element.text_content())
        if not text:
            continue
        block_index = len(blocks) + 1
        xpath = _xpath_for_element(element)
        locator = xpath or f"block:{block_index}"
        blocks.append(
            SourceTextBlock(
                document_filename=path.name,
                document_sha256=digest,
                page_number=None,
                text=text,
                source_format=source_format,
                source_locator_type="xpath_or_block_index",
                source_locator=locator,
                block_index=block_index,
                xpath=xpath,
            )
        )
    if not blocks:
        text = normalize_text(root.text_content())
        if text:
            blocks.append(
                SourceTextBlock(
                    document_filename=path.name,
                    document_sha256=digest,
                    page_number=None,
                    text=text,
                    source_format=source_format,
                    source_locator_type="xpath_or_block_index",
                    source_locator="block:1",
                    block_index=1,
                    xpath="",
                )
            )
    return blocks


def extract_xhtml(company: str, path: Path) -> tuple[list[SourceTextBlock], DocumentManifest]:
    digest = sha256_file(path)
    source_format = source_format_for_path(path)
    mime_type = mime_type_for_format(source_format)
    try:
        lxml_html = _lxml_html()
    except ImportError as exc:
        return [], build_manifest(
            company=company,
            filename=path.name,
            digest=digest,
            page_count=None,
            char_count=0,
            processing_status="error",
            error_message=f"lxml parser backend unavailable: {exc}",
            exclusion_reason="xhtml_parser_unavailable",
            source_format=source_format,
            mime_type=mime_type,
            parser_backend="lxml",
            inline_xbrl_detected=False,
            block_count=0,
        )
    try:
        parser = lxml_html.HTMLParser(encoding="utf-8", remove_comments=True)
        root = lxml_html.document_fromstring(path.read_bytes(), parser=parser)
        inline_xbrl_detected = any(_is_inline_xbrl_element(element) for element in root.iter())
        _prune_hidden_elements(root)
        blocks = _extract_visible_xhtml_blocks(
            root=root, path=path, digest=digest, source_format=source_format
        )
        char_count = sum(len(block.text) for block in blocks)
        manifest = build_manifest(
            company=company,
            filename=path.name,
            digest=digest,
            page_count=None,
            char_count=char_count,
            processing_status="ok",
            source_format=source_format,
            mime_type=mime_type,
            parser_backend="lxml",
            inline_xbrl_detected=inline_xbrl_detected,
            block_count=len(blocks),
        )
        return blocks if manifest.scoring_eligible else [], manifest
    except Exception as exc:  # controlled manifest; caller can continue with other docs
        return [], build_manifest(
            company=company,
            filename=path.name,
            digest=digest,
            page_count=None,
            char_count=0,
            processing_status="error",
            error_message=str(exc),
            source_format=source_format,
            mime_type=mime_type,
            parser_backend="lxml",
            inline_xbrl_detected=False,
            block_count=0,
        )


def extract_document(company: str, path: Path) -> tuple[list[SourceTextBlock], DocumentManifest]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(company, path)
    if suffix in XHTML_EXTENSIONS:
        return extract_xhtml(company, path)
    digest = sha256_file(path)
    source_format = source_format_for_path(path)
    return [], build_manifest(
        company=company,
        filename=path.name,
        digest=digest,
        page_count=None,
        char_count=0,
        processing_status="error",
        error_message=f"Unsupported document extension: {path.suffix}",
        source_format=source_format,
        mime_type=mime_type_for_format(source_format),
        parser_backend="unsupported",
    )
