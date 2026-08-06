from __future__ import annotations

from typing import Any

from core.utils import write_text


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    if value is None:
        return "N/A"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _metric_rows(*named_metrics: tuple[str, dict[str, Any]]) -> list[str]:
    keys = ("samples", "retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score")
    header = "| Metric | " + " | ".join(name for name, _ in named_metrics) + " |"
    divider = "| --- | " + " | ".join("---:" for _ in named_metrics) + " |"
    rows = [header, divider]
    for key in keys:
        rows.append("| " + key + " | " + " | ".join(_format_value(metrics.get(key)) for _, metrics in named_metrics) + " |")
    return rows


def _quality_summary(quality: dict[str, Any]) -> str:
    passed = sum(1 for item in quality.get("checks", []) if item.get("passed"))
    total = len(quality.get("checks", []))
    status = "PASS" if quality.get("overall_passed") else "FAIL"
    return f"{status} ({passed}/{total} checks passed)"

def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a Markdown summary for the clean baseline run."""
    source_rows = ["| Field | Value |", "| --- | --- |"]
    source_rows.extend(f"| {key} | {_format_value(value)} |" for key, value in source_summary.items())
    quality_rows = ["| Check | Status | Observed | Expected |", "| --- | --- | --- | --- |"]
    for item in quality.get("checks", []):
        quality_rows.append(
            f"| {item.get('name', 'unknown')} | {'PASS' if item.get('passed') else 'FAIL'} | "
            f"{_format_value(item.get('observed'))} | {_format_value(item.get('expected'))} |"
        )

    ragas = metrics.get("ragas", {})
    lines = [
        "# Phase 1 Baseline Report",
        "",
        "## Source summary",
        "",
        *source_rows,
        "",
        "## Evaluation metrics",
        "",
        *_metric_rows(("Baseline", metrics)),
        "",
        f"Ragas: `{_format_value(ragas)}`",
        "",
        "## Data quality",
        "",
        f"Overall status: **{_quality_summary(quality)}**",
        "",
        *quality_rows,
        "",
        "## Freshness",
        "",
        "| Field | Value |",
        "| --- | --- |",
        *(f"| {key} | {_format_value(value)} |" for key, value in freshness.items()),
        "",
    ]
    write_text(report_path, "\n".join(lines))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write a comparison report for baseline, corrupted, and repaired runs."""
    quality_rows = [
        "| Signal | Corrupted | Repaired |",
        "| --- | --- | --- |",
        f"| Quality checks | {_quality_summary(corrupted_quality)} | {_quality_summary(repaired_quality)} |",
        f"| Freshness | {'FRESH' if corrupted_freshness.get('is_fresh') else 'STALE'} | {'FRESH' if repaired_freshness.get('is_fresh') else 'STALE'} |",
        f"| Stale rows | {_format_value(corrupted_freshness.get('stale_rows'))} | {_format_value(repaired_freshness.get('stale_rows'))} |",
        f"| Total rows | {_format_value(corrupted_freshness.get('total_rows'))} | {_format_value(repaired_freshness.get('total_rows'))} |",
    ]
    lines = [
        "# Corruption and Repair Comparison",
        "",
        "All three evaluations use the same test set; therefore metric changes can be compared directly.",
        "",
        "## Evaluation metrics",
        "",
        *_metric_rows(
            ("Baseline", baseline_metrics),
            ("Corrupted", corrupted_metrics),
            ("Repaired", repaired_metrics),
        ),
        "",
        "## Data quality and freshness",
        "",
        *quality_rows,
        "",
        "## Interpretation",
        "",
        "Compare the corrupted values against baseline to identify the impact of data corruption, then compare repaired values against baseline to verify recovery.",
        "",
    ]
    write_text(report_path, "\n".join(lines))
