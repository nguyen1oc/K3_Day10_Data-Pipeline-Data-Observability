from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from core.config import load_settings, require_llm_credentials
from core.utils import read_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe, save_clean_data
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run corruption, evaluation, repair, and comparison flow end-to-end:
    1. Load settings and verify credentials.
    2. Read clean dataset and baseline metrics.
    3. Corrupt clean dataset and persist corrupted clean artifacts.
    4. Build corrupted embedding index & evaluate corrupted dataset.
    5. Run data quality & freshness checks on corrupted dataset.
    6. Repair dataset from raw records & build repaired embedding index.
    7. Evaluate repaired dataset.
    8. Run quality & freshness checks on repaired dataset.
    9. Generate comparison report.
    """
    settings = load_settings()
    require_llm_credentials(settings)

    # 1. Read baseline dataset & metrics
    df_clean = pd.read_csv(settings.paths.clean_csv)
    baseline_metrics = read_json(settings.paths.baseline_metrics)

    # 2. Corrupt clean dataset
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)
    save_clean_data(df_corrupted, settings.paths.corrupted_clean_csv, settings.paths.corrupted_clean_json)

    # 3. Build corrupted Chroma index & evaluate
    index_corrupted = LocalEmbeddingIndex.build(
        df=df_corrupted,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    corrupted_eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index_corrupted,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )

    # 4. Quality & Freshness checks for corrupted data
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, "corrupted_quality")
    corrupted_freshness = build_freshness_report(
        df_corrupted, settings, settings.paths.quality_dir / "corrupted_freshness_report.json"
    )

    # 5. Repair dataset from raw records
    records = load_raw_records(settings.paths.raw_records_json)
    run_date = datetime.now(UTC)
    df_repaired = build_clean_dataframe(records, run_date=run_date)
    save_clean_data(df_repaired, settings.paths.repaired_clean_csv, settings.paths.repaired_clean_json)

    # 6. Build repaired Chroma index & evaluate
    index_repaired = LocalEmbeddingIndex.build(
        df=df_repaired,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    repaired_eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index_repaired,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )

    # 7. Quality & Freshness checks for repaired data
    repaired_quality = run_data_quality_checks(df_repaired, settings, "repaired_quality")
    repaired_freshness = build_freshness_report(
        df_repaired, settings, settings.paths.quality_dir / "repaired_freshness_report.json"
    )

    # 8. Generate comparison report
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_eval_bundle.summary,
        repaired_metrics=repaired_eval_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"Corruption flow completed! Comparison report generated at: {settings.paths.comparison_report}")

