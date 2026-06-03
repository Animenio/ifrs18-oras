from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ifrs18_oras.hashing import sha256_file
from ifrs18_oras.models import DocumentManifest, PageText

LOW_TEXT_CHARACTER_THRESHOLD = 50


def _pymupdf() -> Any:
    import pymupdf

    return pymupdf


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
