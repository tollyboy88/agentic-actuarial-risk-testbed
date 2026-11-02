from __future__ import annotations

import csv
import difflib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER2 = ROOT.parent / "bayesian-multistate-actuarial-workflows"


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "actuarial-reference-verifier/1.0 (mailto:adebayoadetola96@yahoo.com)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def title_from_reference(reference: str) -> str:
    body = re.sub(r"https?://\S+", "", reference)
    match = re.search(r"\b(?:19|20)\d{2}[a-z]?\.\s*(.+)", body)
    body = match.group(1) if match else body
    return body.split(". ", 1)[0].strip().rstrip(".")


def verify(reference: str) -> dict[str, object]:
    title = title_from_reference(reference)
    doi_match = re.search(r"https?://doi\.org/([^\s.]+(?:\.[^\s.]+)*)", reference, re.I)
    try:
        if doi_match:
            doi = doi_match.group(1).rstrip(".")
            try:
                item = get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe=""))["message"]
                found = (item.get("title") or [""])[0]; url = item.get("URL", "")
            except Exception:
                item = get_json("https://api.datacite.org/dois/" + urllib.parse.quote(doi, safe=""))["data"]["attributes"]
                titles = item.get("titles") or []; found = titles[0].get("title", "") if titles else ""; url = item.get("url", "")
            score = difflib.SequenceMatcher(None, normalize(title), normalize(found)).ratio()
            return {"status": "verified_doi", "doi": doi, "matched_title": found, "similarity": round(score, 3), "url": url}
        url_match = re.search(r"https?://\S+", reference)
        if url_match:
            url = url_match.group(0).rstrip(".")
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.status
            return {"status": "verified_url" if status < 400 else "manual_primary_source", "doi": "", "matched_title": title, "similarity": 1.0, "url": url}
        query = urllib.parse.urlencode({"query.bibliographic": reference, "rows": 1})
        items = get_json("https://api.crossref.org/works?" + query)["message"]["items"]
        if not items: return {"status": "manual_review", "doi": "", "matched_title": "", "similarity": 0, "url": ""}
        item = items[0]; found = (item.get("title") or [""])[0]
        score = difflib.SequenceMatcher(None, normalize(title), normalize(found)).ratio()
        status = "verified_crossref" if score >= 0.72 else "manual_primary_source"
        return {"status": status, "doi": item.get("DOI", ""), "matched_title": found, "similarity": round(score, 3), "url": item.get("URL", "")}
    except Exception as error:
        return {"status": "manual_primary_source", "doi": "", "matched_title": str(error), "similarity": 0, "url": ""}


def references(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").split("## References", 1)[1]
    return [line.strip() for line in text.splitlines() if line.strip()]


def main() -> None:
    jobs = [
        (ROOT / "papers/paper1_naaj/manuscript_source.md", ROOT / "outputs/reference_verification_paper1.csv"),
        (PAPER2 / "submission/manuscript_source.md", PAPER2 / "outputs/reference_verification_paper2.csv"),
    ]
    for source, target in jobs:
        rows = []
        for index, reference in enumerate(references(source), 1):
            result = verify(reference); rows.append({"reference_number": index, "reference": reference, **result}); time.sleep(0.05)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
        print(target, len(rows))


if __name__ == "__main__": main()
