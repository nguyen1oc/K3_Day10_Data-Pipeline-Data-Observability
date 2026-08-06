from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import ensure_parent, normalize_whitespace, write_csv, write_json
from ingestion.crossref import PaperRecord


# Minimum length for valid summary (after cleaning)
MIN_SUMMARY_CHARS = 100


def _strip_html_tags(text: str) -> str:
    """Remove XML/HTML tags from text content."""
    if not text:
        return ""
    # Remove common XML/HTML tags like <jats:p>, <b>, <i>, etc.
    cleaned = re.sub(r"<[^>]+>", "", text)
    return normalize_whitespace(cleaned)


def _parse_date(date_str: str) -> datetime | None:
    """Parse date string in YYYY-MM-DD format, returning timezone-aware datetime."""
    if not date_str:
        return None
    try:
        # Return timezone-aware datetime for consistency
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def _calculate_age_days(published_str: str, run_date: datetime) -> int | None:
    """Calculate paper age in days from publication date to run date."""
    published = _parse_date(published_str)
    if published is None:
        return None
    return (run_date - published).days


def _is_valid_record(row: dict[str, Any]) -> bool:
    """Check if record meets minimum quality requirements."""
    # Must have title
    title = row.get("title", "")
    if not title or not title.strip():
        return False

    # Must have summary with at least MIN_SUMMARY_CHARS after cleaning
    summary = _strip_html_tags(row.get("summary", ""))
    if len(summary) < MIN_SUMMARY_CHARS:
        return False

    return True


def _build_text_for_embedding(title: str, authors_joined: str, summary: str) -> str:
    """Build combined text for embedding."""
    parts = [
        f"Title: {title}",
        f"Authors: {authors_joined}" if authors_joined else "Authors: Unknown",
        f"Summary: {summary}",
    ]
    return " | ".join(parts)


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed.

    Args:
        records: List of raw PaperRecord objects.
        run_date: Current date for age calculation.

    Returns:
        Cleaned pandas DataFrame ready for embedding.

    Cleaning rules:
        - Drop rows without title or summary < 100 chars.
        - Remove XML/HTML tags from title and summary.
        - Join authors with commas (authors_joined).
        - Join categories with commas (categories_joined).
        - Calculate age_days from published date.
        - Create text_for_embedding column.
    """
    if not records:
        return pd.DataFrame()

    rows = []
    for record in records:
        # Build raw row dict for validation
        raw_row = {
            "title": record.title,
            "summary": record.summary,
        }

        # Validate: skip if no title or summary too short
        if not _is_valid_record(raw_row):
            continue

        # Clean title and summary - remove HTML/XML tags
        title = _strip_html_tags(record.title)
        summary = _strip_html_tags(record.summary)

        # Re-validate after stripping tags
        if not title or len(summary) < MIN_SUMMARY_CHARS:
            continue

        # Normalize authors list and join with commas
        authors = [a.strip() for a in record.authors if a and a.strip()]
        authors_joined = ", ".join(authors) if authors else ""

        # Normalize categories list and join with commas
        categories = [c.strip() for c in record.categories if c and c.strip()]
        categories_joined = ", ".join(categories) if categories else ""

        # Parse dates
        published_date = _parse_date(record.published)
        updated_date = _parse_date(record.updated) or published_date

        # Calculate age in days
        age_days = _calculate_age_days(record.published, run_date) if record.published else None

        # Calculate summary character count (after cleaning)
        summary_chars = len(summary)

        # Build text_for_embedding
        text_for_embedding = _build_text_for_embedding(title, authors_joined, summary)

        row = {
            "paper_id": record.paper_id,
            "title": title,
            "summary": summary,
            "authors_joined": authors_joined,
            "categories_joined": categories_joined,
            "primary_category": record.primary_category,
            "published": record.published,
            "published_date": published_date,
            "updated": record.updated,
            "updated_date": updated_date,
            "age_days": age_days,
            "summary_chars": summary_chars,
            "abs_url": record.abs_url,
            "pdf_url": record.pdf_url,
            "comment": record.comment,
            "text_for_embedding": text_for_embedding,
        }
        rows.append(row)

    # Create DataFrame
    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # Drop exact duplicates based on paper_id
    df = df.drop_duplicates(subset=["paper_id"], keep="first")

    # Sort by published date (newest first), then by paper_id for stability
    df = df.sort_values(
        by=["published", "paper_id"],
        ascending=[False, True],
        na_position="last",
    )

    # Reset index after sorting
    df = df.reset_index(drop=True)

    return df


def save_clean_data(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    """Save cleaned DataFrame to CSV and JSON formats.

    Args:
        df: Cleaned DataFrame.
        csv_path: Path for CSV output.
        json_path: Path for JSON output.
    """
    ensure_parent(csv_path)
    ensure_parent(json_path)

    # Save to CSV (pandas handles datetime fine)
    write_csv(df, csv_path)

    # For JSON: convert datetime columns to ISO strings
    df_json = df.copy()
    for col in ["published_date", "updated_date"]:
        if col in df_json.columns:
            df_json[col] = df_json[col].apply(
                lambda x: x.isoformat() if pd.notna(x) else None
            )
    json_data = df_json.to_dict(orient="records")
    write_json(json_path, json_data)


# ---------------------------------------------------------------------------
# CLI entry point for testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from datetime import UTC
    from ingestion.crossref import load_raw_records

    # Resolve project root (two levels up from this file)
    project_root = Path(__file__).resolve().parents[2]
    raw_records_path = project_root / "data" / "raw" / "crossref_records.json"
    clean_csv_path = project_root / "data" / "clean" / "papers_clean.csv"
    clean_json_path = project_root / "data" / "clean" / "papers_clean.json"

    print(f"[cleaning] Loading raw records from: {raw_records_path}")
    records = load_raw_records(raw_records_path)
    print(f"[cleaning] Loaded {len(records)} raw records")

    run_date = datetime.now(UTC)
    print(f"[cleaning] Cleaning records (run_date={run_date.date()})...")

    df = build_clean_dataframe(records, run_date)
    print(f"[cleaning] Cleaned DataFrame has {len(df)} rows")

    if len(df) > 0:
        print(f"[cleaning] Sample row:\n{df.iloc[0][['paper_id', 'title', 'authors_joined', 'age_days']].to_string()}")

    print(f"[cleaning] Saving to CSV: {clean_csv_path}")
    print(f"[cleaning] Saving to JSON: {clean_json_path}")
    save_clean_data(df, clean_csv_path, clean_json_path)

    print("[cleaning] Done!")
