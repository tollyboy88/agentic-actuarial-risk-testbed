from __future__ import annotations

import re
import json
from pathlib import Path

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P


ROOT = Path(__file__).resolve().parents[1]
PAPER2 = ROOT.parent / "bayesian-multistate-actuarial-workflows"
P1 = ROOT / "papers" / "paper1_naaj" / "FINAL_SUBMISSION_NAAJ"
P2 = PAPER2 / "submission" / "FINAL_SUBMISSION_SAJ"


def document_text(path: Path) -> str:
    document = Document(path)
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    cells = [cell.text for table in document.tables for row in table.rows for cell in row.cells]
    return "\n".join(paragraphs + cells)


def check_anonymous(path: Path) -> None:
    document = Document(path)
    text = document_text(path).lower()
    forbidden = [
        "adebayo", "olugbenga", "yahoo.com", "orcid", "github.com/tollyboy88",
        "zenodo.22821051", "10.5281/zenodo",
    ]
    found = [item for item in forbidden if item in text]
    assert not found, f"Anonymous identifier(s) in {path.name}: {found}"
    assert not document.core_properties.author
    assert not document.core_properties.last_modified_by


def check_inline_order(path: Path, figures: int, tables: int) -> None:
    document = Document(path)
    sequence: list[str] = []
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            sequence.append("".join(child.itertext()))
        elif isinstance(child, CT_Tbl):
            sequence.append("[TABLE]")
    for label, total in (("Figure", figures), ("Table", tables)):
        for number in range(1, total + 1):
            token = f"{label} {number}"
            caption = next(
                index for index, text in enumerate(sequence)
                if re.search(rf"^{label} {number}[.:]", text.strip())
            )
            citation = next(
                index for index, text in enumerate(sequence[:caption])
                if re.search(rf"\b{label}s?\s+{number}\b|\b{label}s?\s+\d+[–-]{number}\b", text)
            )
            assert citation < caption, f"{token} is not cited before placement in {path.name}"


def reference_count(source: Path) -> int:
    text = source.read_text(encoding="utf-8").split("## References", 1)[1]
    return sum(bool(line.strip()) for line in text.splitlines())


def check_reference_citations(source: Path, style: str) -> None:
    body, references = source.read_text(encoding="utf-8").split("## References", 1)
    missing: list[str] = []
    for reference in (line.strip() for line in references.splitlines() if line.strip()):
        pattern = r"(.+?)\s*\((?:n\.d\.|\d{4})\)" if style == "p1" else r"(.+?)\.\s*\d{4}\."
        match = re.match(pattern, reference)
        assert match, f"Could not parse reference: {reference}"
        first_author = match.group(1).split(",")[0].strip().rstrip(".")
        if first_author not in body:
            missing.append(first_author)
    assert not missing, f"References not cited in manuscript body: {missing}"


def main() -> None:
    expected_p1 = {
        "01_manuscript_with_author_details.docx", "02_anonymous_manuscript.docx",
        "03_cover_letter.docx", "04_anonymous_supplementary_material.docx",
    }
    expected_p2 = {
        "01_main_manuscript_anonymous.docx", "02_manuscript_with_author_details.docx",
        "03_title_page.docx", "04_cover_letter.docx",
        "05_supplement_proofs_diagnostics.docx", "06_replication_readme.docx",
    }
    assert {path.name for path in P1.glob("*.docx") if not path.name.startswith("~$")} == expected_p1
    assert {path.name for path in P2.glob("*.docx") if not path.name.startswith("~$")} == expected_p2
    check_anonymous(P1 / "02_anonymous_manuscript.docx")
    check_anonymous(P1 / "04_anonymous_supplementary_material.docx")
    check_anonymous(P2 / "01_main_manuscript_anonymous.docx")
    check_inline_order(P1 / "01_manuscript_with_author_details.docx", 7, 7)
    check_inline_order(P1 / "02_anonymous_manuscript.docx", 7, 7)
    check_inline_order(P2 / "01_main_manuscript_anonymous.docx", 5, 7)
    check_inline_order(P2 / "02_manuscript_with_author_details.docx", 5, 7)
    p1_references = reference_count(ROOT / "papers/paper1_naaj/manuscript_source.md")
    p2_references = reference_count(PAPER2 / "submission/manuscript_source.md")
    assert p1_references > 25 and p2_references > 25
    check_reference_citations(ROOT / "papers/paper1_naaj/manuscript_source.md", "p1")
    check_reference_citations(PAPER2 / "submission/manuscript_source.md", "p2")
    p1_source = (ROOT / "papers/paper1_naaj/manuscript_source.md").read_text(encoding="utf-8")
    for required in ("94.8%", "74.0%", "observed upper triangle", "772 insurer–line combinations"):
        assert required in p1_source
    for superseded in ("84.5%", "observed lower triangle", "772 insurer–line records"):
        assert superseded not in p1_source
    results = json.loads((PAPER2 / "outputs/RESULTS.json").read_text(encoding="utf-8"))
    p2_source = (PAPER2 / "submission/manuscript_source.md").read_text(encoding="utf-8")
    assert results["selected_placement"] in p2_source
    assert f'{results["hierarchical_log_score"]:.3f}' in p2_source
    assert f'{results["global_log_score"]:.3f}' in p2_source
    assert f'{100 * results["mean_90_coverage"]:.1f}%' in p2_source
    assert f'{100 * results["mean_95_coverage"]:.1f}%' in p2_source
    assert f'{results["max_recursion_difference"]:.6f}' in p2_source
    print(f"Validated 10 DOCX files; references: Paper 1={p1_references}, Paper 2={p2_references}")


if __name__ == "__main__":
    main()
