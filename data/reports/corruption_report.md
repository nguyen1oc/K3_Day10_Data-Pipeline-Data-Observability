# Corruption and Repair Comparison

All three evaluations use the same test set; therefore metric changes can be compared directly.

## Evaluation metrics

| Metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| samples | 10 | 10 | 10 |
| retrieval_hit_rate | 0.9000 | 0.8000 | 0.9000 |
| mean_token_f1 | 0.0805 | 0.0410 | 0.0805 |
| judge_accuracy | 0.0000 | 0.0000 | 0.0000 |
| mean_judge_score | 1 | 1 | 1 |

## Data quality and freshness

| Signal | Corrupted | Repaired |
| --- | --- | --- |
| Quality checks | FAIL (4/8 checks passed) | PASS (8/8 checks passed) |
| Freshness | STALE | FRESH |
| Stale rows | 1 | 0 |
| Total rows | 23 | 24 |

## Interpretation

Compare the corrupted values against baseline to identify the impact of data corruption, then compare repaired values against baseline to verify recovery.
