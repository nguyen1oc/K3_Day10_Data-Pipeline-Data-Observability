from __future__ import annotations

from datetime import UTC, datetime

from core.config import load_settings, require_llm_credentials
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe, save_clean_data
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run baseline phase end-to-end:
    1. Load settings and verify LLM credentials.
    2. Load or fetch raw records.
    3. Clean data and save clean CSV/JSON.
    4. Build Chroma embedding index.
    5. Build or load test set.
    6. Evaluate baseline pipeline.
    7. Run quality checks & freshness report.
    8. Generate phase 1 markdown report.
    """
    settings = load_settings()
    require_llm_credentials(settings)

    # 1. Load or fetch raw records
    if settings.paths.raw_records_json.exists() and not settings.refresh_source:
        records = load_raw_records(settings.paths.raw_records_json)
    else:
        records = fetch_source_records(settings)

    # 2. Clean data
    run_date = datetime.now(UTC)
    df_clean = build_clean_dataframe(records, run_date=run_date)
    save_clean_data(df_clean, settings.paths.clean_csv, settings.paths.clean_json)

    # 3. Build Chroma embedding index
    index = LocalEmbeddingIndex.build(
        df=df_clean,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )

    # 4. Evaluation test set
    if not settings.paths.eval_testset.exists() or settings.refresh_test_set:
        build_test_set(df_clean, settings.paths.eval_testset)

    # 5. Evaluate pipeline
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    # 6. Quality & Freshness reports
    quality_report = run_data_quality_checks(df_clean, settings, "baseline_quality")
    freshness_report = build_freshness_report(df_clean, settings, settings.paths.freshness_report)

    # 7. Generate Phase 1 markdown report
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "max_results": settings.max_results,
        "raw_records_count": len(records),
        "clean_records_count": len(df_clean),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality_report,
        freshness=freshness_report,
    )
    print(f"Phase 1 baseline complete! Report generated at: {settings.paths.baseline_report}")

