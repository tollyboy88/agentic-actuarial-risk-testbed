from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from PIL import Image
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
SUB = ROOT / "submission"
FINAL = SUB / "final"
FIG = FINAL / "figures"


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def style_doc(doc: Document):
    sec = doc.sections[0]
    sec.top_margin = Inches(1)
    sec.bottom_margin = Inches(1)
    sec.left_margin = Inches(1)
    sec.right_margin = Inches(1)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 2
    normal.paragraph_format.space_after = Pt(0)
    for name, size in [("Title", 16), ("Heading 1", 14), ("Heading 2", 12)]:
        s = doc.styles[name]
        s.font.name = "Times New Roman"
        s.font.size = Pt(size)
        s.font.bold = True
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_field(footer, "PAGE")


def add_field(paragraph, instr: str):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    text = OxmlElement("w:instrText")
    text.set(qn("xml:space"), "preserve")
    text.text = instr
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, text, end])


def add_inline(paragraph, text: str):
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        else:
            paragraph.add_run(part)


def markdown_to_docx(source: str, out: Path, identified: bool):
    doc = Document()
    style_doc(doc)
    lines = source.splitlines()
    title = lines[0].removeprefix("# ")
    p = doc.add_paragraph(title, style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if identified:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("Adebayo Adetola").bold = True
        p = doc.add_paragraph("Independent Researcher, United Kingdom")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph("Correspondence: adebayoadetola96@yahoo.com")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        p = doc.add_paragraph("Anonymous manuscript")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for line in lines[1:]:
        s = line.strip()
        if not s:
            continue
        if not identified:
            s = s.replace("https://github.com/tollyboy88/agentic-actuarial-risk-testbed", "[repository link omitted for review]")
        if s.startswith("## "):
            doc.add_heading(s[3:], level=1)
        elif s.startswith("### "):
            doc.add_heading(s[4:], level=2)
        elif s.startswith("- "):
            add_inline(doc.add_paragraph(style="List Bullet"), s[2:])
        else:
            p = doc.add_paragraph()
            add_inline(p, s)
    doc.add_heading("Figure captions", level=1)
    captions = [
        "Figure 1. Median absolute paired error across workflow stages and control topologies.",
        "Figure 2. Silent-failure rate by workflow topology.",
        "Figure 3. Detection rate by fault class and topology.",
        "Figure 4. Scenario-conditioned annual VaR at 99.5% by topology (logarithmic scale).",
        "Figure 5. Sector VaR at 99.5% under prescribed cross-firm dependence.",
    ]
    for c in captions:
        doc.add_paragraph(c)
    doc.core_properties.title = title
    doc.core_properties.subject = "Agentic actuarial workflow risk simulation"
    doc.core_properties.keywords = "actuarial AI, operational risk, simulation"
    doc.core_properties.author = "Adebayo Adetola" if identified else ""
    doc.core_properties.last_modified_by = "" if not identified else "Adebayo Adetola"
    doc.save(out)


def add_table(doc, title, columns, rows, add_break=True):
    doc.add_heading(title, level=1)
    table = doc.add_table(rows=1, cols=len(columns))
    table.style = "Table Grid"
    table.autofit = True
    for i, col in enumerate(columns):
        cell = table.rows[0].cells[i]
        cell.text = col
        set_cell_shading(cell, "D9EAF7")
        for run in cell.paragraphs[0].runs:
            run.bold = True
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
    if add_break:
        doc.add_page_break()


def make_tables(out: Path):
    capital = pd.read_csv(ROOT / "outputs/scaled/tables/capital.csv")
    summary = pd.read_csv(ROOT / "outputs/scaled/tables/fault_topology_summary.csv")
    systemic = pd.read_csv(ROOT / "outputs/scaled/tables/systemic_stress.csv")
    topo = summary.groupby("topology", as_index=False).apply(
        lambda g: pd.Series({"runs": int(g.runs.sum()), "detect": (g.detection_rate*g.runs).sum()/g.runs.sum(), "silent": (g.silent_failure_rate*g.runs).sum()/g.runs.sum()}),
        include_groups=False,
    ).reset_index(drop=True)
    doc = Document()
    style_doc(doc)
    doc.add_paragraph("Tables", style="Title").alignment = WD_ALIGN_PARAGRAPH.CENTER
    rows = [[r.topology, int(r.runs), f"{r.detect:.1%}", f"{r.silent:.1%}"] for r in topo.itertuples()]
    add_table(doc, "Table 1. Detection and silent failure by topology", ["Topology", "Fault runs", "Detection", "Silent failure"], rows)
    rows = [[r.topology, f"{r.mean_annual_loss:,.0f}", f"{r.var_995:,.0f}", f"{r.es_995:,.0f}", f"{r.annual_control_cost:,.2f}"] for r in capital.itertuples()]
    add_table(doc, "Table 2. Annual loss and control-cost scenarios (GBP)", ["Topology", "Mean", "VaR 99.5%", "ES 99.5%", "Control cost"], rows)
    med = systemic.groupby("rho").var_995_sector.median().reset_index()
    rows = [[f"{r.rho:.1f}", f"{r.var_995_sector:,.0f}"] for r in med.itertuples()]
    add_table(doc, "Table 3. Median sector VaR 99.5% by prescribed dependence", ["Correlation", "Median sector VaR (GBP)"], rows)
    rows = [
        ["F1", "Data/unit corruption", "Currency or magnitude error; includes ×1,000 stress"],
        ["F2", "Semantic mapping", "Incorrect peril, segment, or field interpretation"],
        ["F3", "Tool arguments", "Correct tool called with an incorrect parameter"],
        ["F4", "Reasoning/judgement", "Unsupported actuarial selection or decision"],
        ["F5", "Hand-off loss", "Required state omitted between agents or stages"],
        ["F6", "Context", "Stale or conflicting context used"],
        ["F7", "Adversarial", "Indirect prompt injection from untrusted content"],
    ]
    add_table(doc, "Table 4. Fault taxonomy", ["Code", "Class", "Operational interpretation"], rows, add_break=False)
    doc.save(out)


def make_title_page(out: Path):
    doc = Document(); style_doc(doc)
    title = "When the model runs itself: quantifying error propagation and operational risk capital for agentic artificial intelligence in actuarial workflows"
    doc.add_paragraph(title, style="Title").alignment = WD_ALIGN_PARAGRAPH.CENTER
    for text in ["Adebayo Adetola", "Independent Researcher, United Kingdom", "Email: adebayoadetola96@yahoo.com", "GitHub: https://github.com/tollyboy88/agentic-actuarial-risk-testbed"]:
        p = doc.add_paragraph(text); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_heading("Author declarations", level=1)
    doc.add_paragraph("Funding: No external funding was used in the development of this independent research prototype.")
    doc.add_paragraph("Competing interests: The author declares no competing interests.")
    doc.add_paragraph("Author contribution (CRediT): Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Visualization, Writing—original draft, Writing—review and editing: Adebayo Adetola.")
    doc.add_paragraph("ORCID: Not supplied. Add before submission if available.")
    doc.add_paragraph("Telephone: Not supplied; enter in the submission portal if requested.")
    doc.save(out)


def make_cover(out: Path):
    doc = Document(); style_doc(doc)
    doc.add_paragraph("Cover letter", style="Title").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Editor-in-Chief\nScandinavian Actuarial Journal")
    doc.add_paragraph("Dear Editor,")
    doc.add_paragraph("Please consider the manuscript “When the model runs itself: quantifying error propagation and operational risk capital for agentic artificial intelligence in actuarial workflows” as an Original Article.")
    doc.add_paragraph("The manuscript introduces a reproducible known-truth testbed that traces controlled faults through a six-stage actuarial reserving workflow and translates residual effects into explicitly scenario-conditioned operational-risk distributions. Its principal innovation is the measurable bridge between agent-trajectory evidence, control architecture, and actuarial tail-risk assessment. The study reports 1,024 runs across seven fault classes and eight control topologies, using same-world counterfactual pairing while carefully separating methodological demonstration from insurer-specific capital calibration.")
    doc.add_paragraph("The work fits the journal’s interest in actuarial methods with practical application. The source code, configurations, and non-restricted derived results are publicly available at https://github.com/tollyboy88/agentic-actuarial-risk-testbed. Restricted third-party raw data are not redistributed. All references in the manuscript are cited in the text.")
    doc.add_paragraph("This manuscript is original, is not under consideration elsewhere, and has not been published previously. The author declares no competing interests and no external funding. OpenAI Codex assisted with software implementation, literature discovery, language editing, and preparation of submission files; the author retains responsibility for the submitted work.")
    doc.add_paragraph("Thank you for your consideration.\n\nSincerely,\nAdebayo Adetola\nIndependent Researcher, United Kingdom\nadebayoadetola96@yahoo.com")
    doc.save(out)


def make_supplement(out: Path):
    doc = Document(); style_doc(doc)
    doc.add_paragraph("Supplementary material: Agentic Actuarial Testbed", style="Title").alignment = WD_ALIGN_PARAGRAPH.CENTER
    sections = {
        "S1. Reproducibility protocol": "Install Python 3.11 or newer, install the package and test dependencies, and execute `aat-sim all --config configs/scaled.yaml`. The seed and all resolved parameters are written to the output directory. The full profile is computationally larger and is intended for expanded replication.",
        "S2. Synthetic-world design": "Worlds contain policy exposure, premium, claim ultimate, incremental paid development, report and payment dates, currency, peril, and ambient duplicates. Ground truth is retained before observation defects. No synthetic record represents a real policyholder.",
        "S3. Pairing and replay": "Every injected-fault trajectory is matched to a same-world, same-seed, same-topology no-fault trajectory. A detected fault restores the last clean state and re-executes downstream deterministic stages. Event and snapshot identifiers preserve this relationship.",
        "S4. Capital parameters": "The screening results use 10,000 annual simulations per topology, configured Poisson event frequencies, a 5% reserve-movement-to-economic-loss conversion, and GBP 5,000 remediation cost. Systemic stress uses 20 firms, 5,000 simulations, and prescribed Gaussian-copula correlations 0, 0.3, 0.6, and 0.9.",
        "S5. Validation gates": "Completed gates include deterministic world reproduction, six complete finite stage snapshots, visible fault and repair events, Parquet and SQLite persistence, successful aggregation, and 1,024 completed screening runs without hard execution failure.",
        "S6. Interpretation limits": "The simulator does not estimate production fault frequency, actual human-review effectiveness, firm-specific economic conversion, or cross-firm correlation. The output is suitable for methodological testing and scenario discussion, not a stand-alone regulatory capital estimate.",
        "S7. Recommended extension": "A publication-scale study should expand seeded worlds, bootstrap by world, vary fault magnitudes and conversion factors, compare Poisson and negative-binomial frequencies, stress tail thresholds and copulas, and validate a subset against an independent reserving implementation and de-identified production exceptions.",
    }
    for h, text in sections.items():
        doc.add_heading(h, level=1); doc.add_paragraph(text)
    doc.add_heading("S8. File map", level=1)
    for item in ["configs/: experiment assumptions and seeds", "src/aat/: simulation and capital engine", "outputs/scaled/: screening results", "dashboard/: interactive result viewer", "tests/: deterministic and end-to-end tests"]:
        doc.add_paragraph(item, style="List Bullet")
    doc.save(out)


def prepare_figures():
    FIG.mkdir(parents=True, exist_ok=True)
    sources = sorted((ROOT / "outputs/scaled/figures").glob("fig*.png"))
    for i, src in enumerate(sources, 1):
        with Image.open(src) as im:
            im = im.convert("RGB")
            if im.width < 3000:
                scale = 3000 / im.width
                im = im.resize((3000, int(im.height * scale)), Image.Resampling.LANCZOS)
            im.save(FIG / f"Figure_{i}.png", dpi=(600, 600), optimize=True)


def main():
    FINAL.mkdir(parents=True, exist_ok=True)
    source = (SUB / "manuscript_source.md").read_text(encoding="utf-8")
    markdown_to_docx(source, FINAL / "01_manuscript_with_author_details.docx", identified=True)
    markdown_to_docx(source, FINAL / "02_anonymous_manuscript.docx", identified=False)
    make_title_page(FINAL / "03_author_details_title_page.docx")
    make_cover(FINAL / "04_cover_letter.docx")
    make_supplement(FINAL / "05_supplementary_material.docx")
    make_tables(FINAL / "06_tables.docx")
    prepare_figures()


if __name__ == "__main__":
    main()
