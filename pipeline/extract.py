"""
PDF -> structured figures. ARCHITECTURE.md §4.1 / PLAN.md Phase 2.

Two extraction paths behind one function signature (`extract_source_document`), selected by
`config.use_document_ai`:
  - Document AI (real path, off by default — API not yet enabled on the project; see README)
  - PyMuPDF + regex (fallback path, always available, no GCP dependency)

This module is proven end-to-end against a REAL government PDF: see the __main__ block, which
extracts the Dwarka Expressway civil-cost and per-km-cost figures from
data/raw_pdfs/cag_report_19_2023_bharatmala.pdf (CAG Report No. 19 of 2023, p.51) — the same
figures hand-transcribed into pipeline/generate_seed.py. Running this file reproduces those
numbers from the raw PDF, which is the Phase 2 acceptance criterion.

Indian budget/audit PDFs often render the rupee sign (₹) as a stray backtick or similar glyph
due to font encoding (observed directly in this PDF: "civil cost of ` 7,287.29 crore") — the
regex below accounts for this along with the proper ₹ character and "Rs."/"Rs" spellings.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import fitz  # PyMuPDF

from pipeline.config import config
from pipeline.schema import ExtractionMethod, SourceDocument, SourceType

# Matches a rupee-crore figure however the PDF happened to render the rupee glyph.
_CRORE_FIGURE_RE = re.compile(
    r"(?:₹|`|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s*crore", re.IGNORECASE
)


@dataclass
class ExtractedFigure:
    value_cr: float
    context: str  # the surrounding text window, for auditability/debugging


def extract_text_by_page(pdf_path) -> list[str]:
    doc = fitz.open(pdf_path)
    try:
        return [page.get_text() for page in doc]
    finally:
        doc.close()


def find_figures_near_keyword(
    full_text: str, keyword: str, window: int = 250
) -> list[ExtractedFigure]:
    """Find every crore-denominated figure within `window` characters after an occurrence of
    `keyword` (case-insensitive). Returns all matches — caller decides which to trust (e.g.
    first match, or the one with the tightest proximity)."""
    results: list[ExtractedFigure] = []
    lowered = full_text.lower()
    keyword_lower = keyword.lower()

    start = 0
    while True:
        idx = lowered.find(keyword_lower, start)
        if idx == -1:
            break
        snippet = full_text[idx : idx + window]
        for m in _CRORE_FIGURE_RE.finditer(snippet):
            try:
                value = float(m.group(1).replace(",", ""))
            except ValueError:
                continue
            results.append(ExtractedFigure(value_cr=value, context=snippet.strip()))
        start = idx + len(keyword)

    return results


def extract_project_figures_pymupdf(
    pdf_path, keyword_hints: dict[str, list[str]]
) -> dict[str, float | None]:
    """keyword_hints maps a target field ('sanctioned_cr', 'disbursed_cr', 'utilized_cr') to a
    list of candidate keywords to search near, in priority order (first keyword that yields a
    match wins). Returns the best-effort figure per field, or None if nothing was found.
    """
    pages = extract_text_by_page(pdf_path)
    full_text = "\n".join(pages)

    out: dict[str, float | None] = {}
    for field, keywords in keyword_hints.items():
        value = None
        for kw in keywords:
            matches = find_figures_near_keyword(full_text, kw)
            if matches:
                value = matches[0].value_cr
                break
        out[field] = value
    return out


def extract_project_figures_document_ai(pdf_path, keyword_hints: dict) -> dict[str, float | None]:
    """Real Document AI path — requires USE_DOCUMENT_AI=true, the API enabled on the GCP
    project, and DOCUMENT_AI_PROCESSOR_ID configured. Not exercised in this session (Document
    AI is not yet enabled on personal-hackthon-tests — see README "Going live on Google Cloud").
    Kept here with the same signature as the PyMuPDF path so callers never need to branch.
    """
    from google.cloud import documentai_v1 as documentai  # local import: optional dependency

    client = documentai.DocumentProcessorServiceClient()
    name = client.processor_path(
        config.gcp_project, config.gcp_location, config.document_ai_processor_id
    )
    with open(pdf_path, "rb") as f:
        raw_document = documentai.RawDocument(content=f.read(), mime_type="application/pdf")
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    result = client.process_document(request=request)
    full_text = result.document.text

    out: dict[str, float | None] = {}
    for field, keywords in keyword_hints.items():
        value = None
        for kw in keywords:
            matches = find_figures_near_keyword(full_text, kw)
            if matches:
                value = matches[0].value_cr
                break
        out[field] = value
    return out


def extract_source_document(
    pdf_path,
    project_id: str,
    source_type: SourceType,
    title: str,
    keyword_hints: dict[str, list[str]] | None = None,
) -> SourceDocument:
    """Main entry point: PDF -> SourceDocument. Selects Document AI or PyMuPDF automatically
    based on config.use_document_ai. Default keyword_hints cover common Indian budget/audit
    document phrasing; pass overrides per-document if needed.
    """
    hints = keyword_hints or {
        "sanctioned_cr": ["civil cost of", "sanctioned cost", "approved cost", "sanctioned"],
        "disbursed_cr": ["disbursed", "released"],
        "utilized_cr": ["utilized", "utilised", "expenditure incurred", "actual expenditure"],
    }

    if config.use_document_ai:
        figures = extract_project_figures_document_ai(pdf_path, hints)
        method = ExtractionMethod.DOCUMENT_AI
    else:
        figures = extract_project_figures_pymupdf(pdf_path, hints)
        method = ExtractionMethod.PYMUPDF

    return SourceDocument(
        doc_id=f"{project_id}-{pdf_path.stem if hasattr(pdf_path, 'stem') else 'doc'}",
        project_id=project_id,
        source_type=source_type,
        title=title,
        url_or_path=str(pdf_path),
        claimed_sanctioned_cr=figures.get("sanctioned_cr"),
        claimed_disbursed_cr=figures.get("disbursed_cr"),
        claimed_utilized_cr=figures.get("utilized_cr"),
        extraction_method=method,
    )


if __name__ == "__main__":
    # Proof of real, end-to-end extraction (Phase 2 acceptance criterion). Reproduces the
    # Dwarka Expressway figures hand-transcribed in pipeline/generate_seed.py, but this time
    # pulled directly from the raw government PDF.
    pdf_path = config.raw_pdf_dir / "cag_report_19_2023_bharatmala.pdf"
    if not pdf_path.exists():
        print(f"Real PDF not found at {pdf_path} — download it first (see README).")
    else:
        print(f"Extracting from real PDF: {pdf_path.name}\n")

        pages = extract_text_by_page(pdf_path)
        full_text = "\n".join(pages)

        # This is a 264-page report covering MANY highway projects, so a bare keyword search
        # for "civil cost of" matches dozens of unrelated projects (see below for the full,
        # unscoped list — instructive but not what we want for a single project's figure).
        # A real extraction pipeline scopes to the relevant section first; we do that here by
        # slicing the text to the "3.5.2.2 Dwarka Expressway" section before searching.
        section_start = full_text.find("3.5.2.2 Dwarka Expressway")
        section_end = full_text.find("3.5.2.3", section_start) if section_start != -1 else -1
        dwarka_section = (
            full_text[section_start:section_end] if section_start != -1 and section_end != -1
            else full_text
        )

        print("All 'civil cost of' matches, unscoped (illustrates why section-scoping matters "
              "in a multi-project document):")
        for f in find_figures_near_keyword(full_text, "civil cost of")[:3]:
            print(f"  ₹{f.value_cr:,.2f} cr  |  context: {f.context[:100]!r}")
        print(f"  ... ({len(find_figures_near_keyword(full_text, 'civil cost of'))} total matches "
              f"across the whole report)")

        print("\nScoped to the Dwarka Expressway section — 'civil cost of' matches:")
        for f in find_figures_near_keyword(dwarka_section, "civil cost of"):
            print(f"  ₹{f.value_cr:,.2f} cr  |  context: {f.context[:120]!r}")

        print("\nScoped: per-km cost matches near 'per km cost of':")
        for f in find_figures_near_keyword(dwarka_section, "per km cost of"):
            print(f"  ₹{f.value_cr:,.2f} cr/km  |  context: {f.context[:120]!r}")

        print("\nScoped: CCEA-approved benchmark matches near 'CCEA approved per km cost':")
        for f in find_figures_near_keyword(dwarka_section, "CCEA approved per km cost"):
            print(f"  ₹{f.value_cr:,.2f} cr/km  |  context: {f.context[:120]!r}")

        doc = extract_source_document(
            pdf_path,
            project_id="in-hr-roads-dwarka-expressway-2018",
            source_type=SourceType.CAG_REPORT,
            title="CAG Report No. 19 of 2023 — Bharatmala Pariyojana Phase-I",
            keyword_hints={"sanctioned_cr": ["civil cost of"]},
        )
        print("\nExtracted SourceDocument (unscoped, whole-report search — matches the first "
              "occurrence of 'civil cost of' in the entire 264-page report, NOT necessarily "
              "Dwarka's own figure; this demonstrates why real production use needs the "
              "section-scoping shown above, or Document AI's structured field extraction):")
        print(doc.model_dump_json(indent=2))
