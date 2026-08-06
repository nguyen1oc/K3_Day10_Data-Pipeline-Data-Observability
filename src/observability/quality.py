from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Thực thiện bộ kiểm tra Data Quality trên Clean Dataframe và ghi báo cáo JSON.

    1. Row count check (phải có dữ liệu > 0).
    2. paper_id check (không được null và phải duy nhất).
    3. title check (không được null hoặc rỗng).
    4. summary check (độ dài summary tối thiểu 20 ký tự).
    5. freshness check (age_days <= freshness_threshold_days).
    """
    total_rows = len(df)
    row_count_passed = total_rows > 0

    if "paper_id" in df.columns:
        null_paper_ids = int(df["paper_id"].isnull().sum())
        duplicate_paper_ids = int(df["paper_id"].duplicated().sum())
        unique_paper_ids = int(df["paper_id"].nunique())
        paper_id_passed = (null_paper_ids == 0) and (duplicate_paper_ids == 0)
    else:
        null_paper_ids = total_rows
        duplicate_paper_ids = 0
        unique_paper_ids = 0
        paper_id_passed = False

    if "title" in df.columns:
        null_titles = int(df["title"].isnull().sum())
        empty_titles = int((df["title"].astype(str).str.strip() == "").sum())
        title_passed = (null_titles == 0) and (empty_titles == 0)
    else:
        null_titles = total_rows
        empty_titles = 0
        title_passed = False

    if "summary" in df.columns:
        null_summaries = int(df["summary"].isnull().sum())
        short_summaries = int((df["summary"].astype(str).str.strip().str.len() < 20).sum())
        summary_passed = (null_summaries == 0) and (short_summaries == 0)
    else:
        null_summaries = total_rows
        short_summaries = 0
        summary_passed = False

    if "age_days" in df.columns:
        stale_records = int((df["age_days"] > settings.freshness_threshold_days).sum())
        freshness_passed = stale_records == 0
    else:
        stale_records = 0
        freshness_passed = True

    passed = all([
        row_count_passed,
        paper_id_passed,
        title_passed,
        summary_passed,
        freshness_passed,
    ])

    report = {
        "report_name": report_name,
        "passed": passed,
        "total_rows": total_rows,
        "checks": {
            "row_count": {
                "passed": row_count_passed,
                "total_rows": total_rows,
            },
            "paper_id_unique": {
                "passed": paper_id_passed,
                "null_count": null_paper_ids,
                "duplicate_count": duplicate_paper_ids,
                "unique_count": unique_paper_ids,
            },
            "title_not_null": {
                "passed": title_passed,
                "null_count": null_titles,
                "empty_count": empty_titles,
            },
            "summary_quality": {
                "passed": summary_passed,
                "null_count": null_summaries,
                "short_count": short_summaries,
            },
            "freshness": {
                "passed": freshness_passed,
                "stale_records": stale_records,
                "threshold_days": settings.freshness_threshold_days,
            },
        },
    }

    report_path = settings.paths.quality_dir / f"{report_name}.json"
    write_json(report_path, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path | str) -> dict[str, Any]:
    """Tổng hợp freshness report cho dataset và ghi thành file JSON."""
    total_rows = len(df)

    if "published" in df.columns and total_rows > 0:
        published_series = pd.to_datetime(df["published"], errors="coerce")
        valid_dates = published_series.dropna()
        latest_published = valid_dates.max().isoformat() if not valid_dates.empty else None
        oldest_published = valid_dates.min().isoformat() if not valid_dates.empty else None
    else:
        latest_published = None
        oldest_published = None

    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = 0

    is_fresh = (stale_rows == 0) and (total_rows > 0)

    report = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": is_fresh,
    }

    report_file = Path(report_path)
    write_json(report_file, report)
    return report

