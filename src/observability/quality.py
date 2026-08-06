from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json

def _non_empty(series: pd.Series) -> pd.Series:
    """Return a mask for values that remain meaningful after string cleanup."""
    return series.notna() & series.astype(str).str.strip().ne("")


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run lightweight, reproducible data-quality checks and persist the result.

    The checks deliberately use the cleaned-data contract rather than a separate
    validation framework, so the same report is available for baseline,
    corrupted, and repaired datasets.
    """
    required_columns = {"paper_id", "title", "summary", "age_days"}
    missing_columns = sorted(required_columns.difference(df.columns))
    row_count = len(df)

    def check(name: str, passed: bool, observed: Any, expected: str) -> dict[str, Any]:
        return {
            "name": name,
            "passed": bool(passed),
            "observed": observed,
            "expected": expected,
        }

    checks: list[dict[str, Any]] = [
        check("required_columns", not missing_columns, missing_columns, "all required columns are present"),
        check("row_count", row_count > 0, row_count, "at least one row"),
    ]

    if missing_columns:
        checks.extend(
            [
                check("paper_id_not_null", False, None, "no blank paper_id values"),
                check("paper_id_unique", False, None, "paper_id values are unique"),
                check("title_not_null", False, None, "no blank title values"),
                check("summary_not_blank", False, None, "no blank summary values"),
                check("summary_min_length", False, None, "each summary has at least 40 characters"),
                check("freshness", False, None, f"age_days <= {settings.freshness_threshold_days}"),
            ]
        )
    else:
        paper_ids = _non_empty(df["paper_id"])
        titles = _non_empty(df["title"])
        summaries = _non_empty(df["summary"])
        summary_lengths = df["summary"].fillna("").astype(str).str.strip().str.len()
        ages = pd.to_numeric(df["age_days"], errors="coerce")
        stale_rows = int((ages > settings.freshness_threshold_days).sum())
        invalid_age_rows = int(ages.isna().sum())

        checks.extend(
            [
                check("paper_id_not_null", bool(paper_ids.all()), int((~paper_ids).sum()), "no blank paper_id values"),
                check(
                    "paper_id_unique",
                    bool(df.loc[paper_ids, "paper_id"].astype(str).str.strip().is_unique),
                    int(df.loc[paper_ids, "paper_id"].astype(str).str.strip().duplicated().sum()),
                    "paper_id values are unique",
                ),
                check("title_not_null", bool(titles.all()), int((~titles).sum()), "no blank title values"),
                check("summary_not_blank", bool(summaries.all()), int((~summaries).sum()), "no blank summary values"),
                check(
                    "summary_min_length",
                    bool((summary_lengths >= 40).all()),
                    int((summary_lengths < 40).sum()),
                    "each summary has at least 40 characters",
                ),
                check(
                    "freshness",
                    stale_rows == 0 and invalid_age_rows == 0,
                    {"stale_rows": stale_rows, "invalid_age_rows": invalid_age_rows},
                    f"age_days <= {settings.freshness_threshold_days}",
                ),
            ]
        )

    report = {
        "report_name": report_name,
        "total_rows": row_count,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "overall_passed": all(item["passed"] for item in checks),
        "checks": checks,
    }
    write_json(settings.paths.quality_dir / f"{report_name}.json", report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Summarise publication recency for a cleaned dataset."""
    total_rows = len(df)
    published_source = df["published"] if "published" in df else pd.Series(pd.NA, index=df.index)
    age_source = df["age_days"] if "age_days" in df else pd.Series(pd.NA, index=df.index)
    published = pd.to_datetime(published_source, errors="coerce", utc=True)
    ages = pd.to_numeric(age_source, errors="coerce")
    invalid_published_rows = int(published.isna().sum()) if total_rows else 0
    invalid_age_rows = int(ages.isna().sum()) if total_rows else 0
    stale_rows = int((ages > settings.freshness_threshold_days).sum())

    latest = published.max() if not published.empty else pd.NaT
    oldest = published.min() if not published.empty else pd.NaT
    report = {
        "total_rows": total_rows,
        "latest_published": latest.date().isoformat() if pd.notna(latest) else None,
        "oldest_published": oldest.date().isoformat() if pd.notna(oldest) else None,
        "stale_rows": stale_rows,
        "invalid_published_rows": invalid_published_rows,
        "invalid_age_rows": invalid_age_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": bool(total_rows > 0 and stale_rows == 0 and invalid_published_rows == 0 and invalid_age_rows == 0),
    }
    write_json(report_path, report)
    return report
