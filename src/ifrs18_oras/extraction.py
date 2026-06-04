from __future__ import annotations

import importlib.util
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from ifrs18_oras.hashing import sha256_file
from ifrs18_oras.models import DocumentManifest, PageText

LOW_TEXT_CHARACTER_THRESHOLD = 50
SUPPORTED_DOCUMENT_EXTENSIONS = (".pdf", ".xhtml", ".html", ".htm")
XHTML_EXTENSIONS = (".xhtml", ".html", ".htm")
_BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
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
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "summary",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
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


class _VisibleTextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        local = tag.rsplit(":", 1)[-1].lower()
        attributes = {key.lower(): (value or "").lower() for key, value in attrs}
        style = attributes.get("style", "").replace(" ", "")
        hidden = (
            local in _REMOVED_TAGS
            or local == "hidden"
            or "hidden" in attributes
            or attributes.get("aria-hidden") == "true"
            or "display:none" in style
            or "visibility:hidden" in style
        )
        if hidden or self._hidden_depth:
            self._hidden_depth += 1
            return
        if local in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        local = tag.rsplit(":", 1)[-1].lower()
        if self._hidden_depth:
            self._hidden_depth -= 1
            return
        if local in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._hidden_depth:
            self.parts.append(data)


def _extract_html_text_with_stdlib(source: str) -> str:
    parser = _VisibleTextHTMLParser()
    parser.feed(source)
    parser.close()
    return normalize_text(" ".join(parser.parts))


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


def build_manifest(
    *,
    company: str,
    filename: str,
    digest: str,
    page_count: int,
    char_count: int,
    processing_status: str,
    error_message: str = "",
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
            exclusion_reason="extraction_error",
            error_message=error_message,
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
    )


def extract_pdf(company: str, path: Path) -> tuple[list[PageText], DocumentManifest]:
    digest = sha256_file(path)
    pages: list[PageText] = []
    try:
        pymupdf = _pymupdf()
        with pymupdf.open(path) as doc:
            page_count = doc.page_count
            for index, page in enumerate(doc, start=1):
                text = normalize_text(page.get_text("text"))
                pages.append(PageText(path.name, digest, index, text))
        char_count = sum(len(page.text) for page in pages)
        manifest = build_manifest(
            company=company,
            filename=path.name,
            digest=digest,
            page_count=page_count,
            char_count=char_count,
            processing_status="ok",
        )
        return pages if manifest.scoring_eligible else [], manifest
    except Exception as exc:  # controlled manifest; caller can continue with other docs
        return [], build_manifest(
            company=company,
            filename=path.name,
            digest=digest,
            page_count=0,
            char_count=0,
            processing_status="error",
            error_message=str(exc),
        )


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1].lower()


def _is_hidden_element(element: Any) -> bool:
    tag = _local_name(element.tag)
    if tag in _REMOVED_TAGS:
        return True
    if tag == "hidden" and (element.prefix == "ix" or str(element.tag).lower().startswith("ix:")):
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


def _append_element_text(element: Any, parts: list[str]) -> None:
    tag = _local_name(element.tag)
    if element.text:
        parts.append(element.text)
    for child in element:
        _append_element_text(child, parts)
        if child.tail:
            parts.append(child.tail)
    if tag in _BLOCK_TAGS:
        parts.append("\n")


def extract_xhtml(company: str, path: Path) -> tuple[list[PageText], DocumentManifest]:
    digest = sha256_file(path)
    try:
        if importlib.util.find_spec("lxml") is None:
            text = _extract_html_text_with_stdlib(
                path.read_text(encoding="utf-8", errors="replace")
            )
        else:
            lxml_html = _lxml_html()
            parser = lxml_html.HTMLParser(encoding="utf-8", remove_comments=True)
            root = lxml_html.document_fromstring(path.read_bytes(), parser=parser)
            _prune_hidden_elements(root)
            body = root.find("body")
            if body is None:
                body = root
            parts: list[str] = []
            _append_element_text(body, parts)
            text = normalize_text(" ".join(parts))
        page_count = 1 if text else 0
        pages = [PageText(path.name, digest, 1, text)] if text else []
        manifest = build_manifest(
            company=company,
            filename=path.name,
            digest=digest,
            page_count=page_count,
            char_count=len(text),
            processing_status="ok",
        )
        return pages if manifest.scoring_eligible else [], manifest
    except Exception as exc:  # controlled manifest; caller can continue with other docs
        return [], build_manifest(
            company=company,
            filename=path.name,
            digest=digest,
            page_count=0,
            char_count=0,
            processing_status="error",
            error_message=str(exc),
        )


def extract_document(company: str, path: Path) -> tuple[list[PageText], DocumentManifest]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(company, path)
    if suffix in XHTML_EXTENSIONS:
        return extract_xhtml(company, path)
    digest = sha256_file(path)
    return [], build_manifest(
        company=company,
        filename=path.name,
        digest=digest,
        page_count=0,
        char_count=0,
        processing_status="error",
        error_message=f"Unsupported document extension: {path.suffix}",
    )
