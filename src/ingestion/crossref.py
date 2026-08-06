import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

from core.config import Settings
from core.utils import ensure_parent, normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_abstract(text: str) -> str:
    """Remove HTML/XML tags from abstract text."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def _extract_date(date_dict: dict) -> str:
    """Extract YYYY-MM-DD string from Crossref date-parts structure."""
    if not date_dict or "date-parts" not in date_dict:
        return ""
    parts = date_dict.get("date-parts", [[]])[0]
    if not parts:
        return ""
    year = parts[0]
    month = parts[1] if len(parts) > 1 else 1
    day = parts[2] if len(parts) > 2 else 1
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref API JSON payload into a list of PaperRecord objects."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        doi = item.get("DOI", "").strip()
        paper_id = doi if doi else f"crossref_{len(records)}"

        titles = item.get("title", [])
        title = titles[0] if isinstance(titles, list) and titles else str(titles)

        summary = _clean_abstract(item.get("abstract", ""))
        authors = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in item.get("author", [])
            if isinstance(a, dict)
        ]
        categories = item.get("subject", [])
        primary_cat = categories[0] if categories else ""

        pub_dict = (
            item.get("published")
            or item.get("published-print")
            or item.get("published-online")
            or {}
        )
        published = _extract_date(pub_dict)
        updated = _extract_date(item.get("issued") or item.get("created") or {})

        abs_url = item.get("URL", f"https://doi.org/{doi}" if doi else "")
        pdf_url = abs_url
        for link in item.get("link", []):
            if isinstance(link, dict) and link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", abs_url)
                break

        containers = item.get("container-title", [])
        comment = (
            containers[0]
            if isinstance(containers, list) and containers
            else str(containers)
        )

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_cat,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch records from Crossref API, save raw response, parse and save raw records."""
    api_url = (
        settings.source_api
        if settings.source_api.startswith("http")
        else "https://api.crossref.org/works"
    )
    params: dict[str, str | int] = {}
    if settings.source_query:
        params["query"] = settings.source_query
    if settings.source_filter:
        params["filter"] = settings.source_filter
    if settings.max_results:
        params["rows"] = settings.max_results

    headers = {"User-Agent": "DataObservabilityLab/1.0 (mailto:student@example.com)"}
    response = None

    for attempt in range(3):
        res = requests.get(api_url, params=params, headers=headers, timeout=30)
        if res.status_code == 200:
            response = res
            break
        if res.status_code in (429, 503, 504):
            time.sleep(2**attempt)
        else:
            res.raise_for_status()

    if response is None:
        raise RuntimeError("Failed to fetch data from Crossref API after 3 retries.")

    payload = response.json()
    settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.raw_api_response.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    records = parse_crossref_payload(payload)
    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    records_data = [asdict(r) for r in records]
    settings.paths.raw_records_json.write_text(
        json.dumps(records_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load raw records from JSON snapshot and map to a list of PaperRecord."""
    if not path.exists():
        raise FileNotFoundError(f"Raw records file not found at {path}")
    raw_data = json.loads(path.read_text(encoding="utf-8"))
    return [PaperRecord(**item) for item in raw_data]
