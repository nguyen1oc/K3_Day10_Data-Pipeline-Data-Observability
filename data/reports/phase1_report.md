# Phase 1 Baseline Report

## Source summary

| Field | Value |
| --- | --- |
| source_api | Crossref REST API |
| source_query | agentic retrieval augmented generation large language model |
| max_results | 24 |
| raw_records_count | 24 |
| clean_records_count | 24 |

## Evaluation metrics

| Metric | Baseline |
| --- | ---: |
| samples | 10 |
| retrieval_hit_rate | 0.9000 |
| mean_token_f1 | 0.0805 |
| judge_accuracy | 0.0000 |
| mean_judge_score | 1 |

Ragas: `{'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'}`

## Data quality

Overall status: **PASS (8/8 checks passed)**

| Check | Status | Observed | Expected |
| --- | --- | --- | --- |
| required_columns | PASS | [] | all required columns are present |
| row_count | PASS | 24 | at least one row |
| paper_id_not_null | PASS | 0 | no blank paper_id values |
| paper_id_unique | PASS | 0 | paper_id values are unique |
| title_not_null | PASS | 0 | no blank title values |
| summary_not_blank | PASS | 0 | no blank summary values |
| summary_min_length | PASS | 0 | each summary has at least 40 characters |
| freshness | PASS | {'stale_rows': 0, 'invalid_age_rows': 0} | age_days <= 180 |

## Freshness

| Field | Value |
| --- | --- |
| total_rows | 24 |
| latest_published | 2026-08-01 |
| oldest_published | 2026-02-12 |
| stale_rows | 0 |
| invalid_published_rows | 0 |
| invalid_age_rows | 0 |
| freshness_threshold_days | 180 |
| is_fresh | True |
