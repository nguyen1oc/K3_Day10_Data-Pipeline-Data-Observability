# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K3 |
| Tên nhóm | bo pc |
| Repository | [K3_Day10_Data-Pipeline-Data-Observability_bopc](https://github.com/nguyen1oc/K3_Day10_Data-Pipeline-Data-Observability_bopc) |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Anh Quân | 2A202601251 | Data ingestion owner | `crossref.py`; raw response và raw records |
| 2 | Lê Bình Nguyễn | 2A202601659 | Cleaning & evaluation-set owner | `cleaning.py`, `testset.py`; clean data và frozen test set |
| 3 | Nguyen Thien Loc | 2A202601479 | Team lead & Data Observability owner | `quality.py`, `reporting.py`; quality/freshness và reports |
| 4 | Phạm Văn Thắng | 2A202601359 | Corruption & integration owner | `corruption.py`, `phase1.py`, `corruption_flow.py` |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành pipeline RAG lấy metadata bài báo từ Crossref, làm sạch dữ liệu, xây dựng embedding/index ChromaDB, đánh giá bằng frozen test set, theo dõi data quality/freshness và chạy thí nghiệm corruption–repair. Baseline tạo raw response/records, cleaned CSV/JSON, embedding manifests, Chroma persistent store, test set 10 câu hỏi, metrics/answers, quality/freshness JSON và Markdown report. Dữ liệu baseline có 24 records, pass 8/8 quality checks và ở trạng thái fresh.

Corruption tạo các lỗi có chủ đích: xóa 2 record mới, blank summary, chèn noise, truncate title, làm stale publication date và duplicate record. Dataset corrupted còn 23 rows, fail 4/8 quality checks và có 1 stale row. Trên cùng frozen test set, retrieval hit rate giảm từ 0.9 xuống 0.8, mean token F1 giảm từ 0.0805 xuống 0.0410. Repair được thực hiện bằng cách dựng lại clean dataset từ raw snapshot, không vá trực tiếp dataset lỗi. Sau repair, dataset trở lại 24 rows, pass 8/8 checks, fresh, và retrieval/token-F1 khôi phục về đúng baseline. Giới hạn chính còn lại là answer extraction: judge accuracy và mean judge score vẫn thấp vì nhiều câu trả lời chỉ lấy câu đầu abstract thay vì trích đúng fact được hỏi.

## 3. Kiến trúc và luồng dữ liệu

```text
Crossref REST API
  → raw response + raw records
  → cleaning + data modeling
  → MiniLM embeddings + ChromaDB
  → frozen evaluation test set + baseline evaluation
  → quality/freshness reports
  → corruption + re-index + re-evaluation
  → repair from raw snapshot + re-index + re-evaluation
  → comparison report
```

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref API | Fetch, retry, parse DOI/title/abstract/authors/date | `data/raw/crossref_response.json`, `crossref_records.json` | Nguyễn Anh Quân |
| Cleaning | Raw records | Validate, normalize text, remove HTML, deduplicate, build embedding text | `data/clean/papers_clean.csv/json` | Lê Bình Nguyễn |
| Index & evaluation | Clean data + test set | MiniLM embedding, Chroma query, metrics | `data/embeddings/`, `data/results/` | Nhóm tích hợp |
| Observability | DataFrame ba trạng thái | Quality checks, freshness, Markdown reporting | `data/quality/`, `data/reports/` | Nguyen Thien Loc |
| Corruption/repair | Clean data + raw snapshot | Corrupt, re-index, repair from raw, compare | corrupted/repaired artifacts và log | Phạm Văn Thắng |

## 4. Cách tái hiện kết quả

| Cấu hình | Giá trị |
| --- | --- |
| Source | Crossref REST API |
| Query | `agentic retrieval augmented generation large language model` |
| Số record tối đa | 24 |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store | ChromaDB persistent tại `data/chroma/` |
| Retrieval top-k | 4 |
| Freshness threshold | 180 ngày |
| Test set | `data/eval/test_set.json`, 10 factual questions |
| LLM provider/model | Đọc từ `.env`; không đưa API key vào report |

```bash
uv sync
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

Baseline cần chạy trước corruption flow. Baseline, corrupted và repaired sử dụng cùng một frozen test set trong cùng một lần thí nghiệm để các metric có thể so sánh trực tiếp.

## 5. Ingestion, cleaning và data contract

| Thành phần | Contract |
| --- | --- |
| Raw record | `paper_id`, title, summary, authors, categories, published/updated dates, URLs |
| Clean record | Raw fields đã chuẩn hóa, `authors_joined`, `categories_joined`, `summary_chars`, `age_days`, `text_for_embedding` |
| Document identity | DOI được dùng làm `paper_id`, ổn định qua index/evaluation/repair |
| Cleaning rules | Bỏ title rỗng hoặc summary ngắn; loại HTML/XML; deduplicate theo `paper_id`; sort ổn định |
| Embedding text | Kết hợp title, authors và summary để semantic retrieval |

Baseline nhận 24 raw records và tạo 24 clean records. `age_days` được tính từ `published` để cung cấp freshness signal. Test set xác minh schema và rằng mọi `ground_truth_doc_ids` đều tồn tại trong clean dataset.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 10 |
| Question type | `factual` |
| Ground truth | Answer tham chiếu cùng `ground_truth_doc_ids` |
| Retrieval metric | Document ID đúng xuất hiện trong top-k |
| Answer metrics | Token F1, LLM judge accuracy và judge score |
| Optional metric | Ragas bị skip khi `RUN_RAGAS` không bật |
| Frozen test set | `data/eval/test_set.json` dùng chung cho cả ba trạng thái |

Frozen test set đã được chuẩn hóa sang tiếng Anh để đồng nhất tốt hơn với corpus/embedding hiện tại. Đây là thay đổi được thực hiện trước lần chạy cuối; sau đó file được giữ nguyên cho baseline, corrupted và repaired.

## 7. Kết quả baseline

| Artifact | Đường dẫn | Trạng thái |
| --- | --- | --- |
| Raw response/records | `data/raw/` | Có |
| Cleaned dataset | `data/clean/papers_clean.csv/json` | Có, 24 rows |
| Embedding manifest/index | `data/embeddings/papers_embeddings.json`, `data/chroma/` | Có |
| Evaluation set | `data/eval/test_set.json` | Có, 10 samples |
| Metrics/answers | `data/results/baseline_metrics.json`, `baseline_answers.json` | Có |
| Quality/freshness | `data/quality/baseline_quality.json`, `freshness_report.json` | Có |
| Baseline report | `data/reports/phase1_report.md` | Có |

| Metric | Baseline | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | 0.9000 | 9/10 câu có document ground truth trong top-k |
| `mean_token_f1` | 0.0805 | Answer extraction còn hạn chế với factual detail |
| `judge_accuracy` | 0.0000 | Judge chưa chấp nhận answer factual hiện tại |
| `mean_judge_score` | 1.0 | Cần cải thiện answer generation |

## 8. Data quality và freshness

| Check | Quality dimension | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- | --- |
| Required columns/row count | Completeness | Pass | Pass | Pass |
| `paper_id` not null/unique | Validity & uniqueness | Pass | Fail: 1 duplicate | Pass |
| Title not null | Completeness | Pass | Pass | Pass |
| Summary not blank/min length | Completeness | Pass | Fail: 3 affected rows | Pass |
| `age_days` freshness | Timeliness | Fresh | Fail: 1 stale row | Fresh |
| Overall | — | Pass 8/8 | Fail 4/8 | Pass 8/8 |

Baseline/repaired có ngày mới nhất `2026-08-01`, ngày cũ nhất `2026-02-12`, không có stale row. Corrupted có ngày cũ nhất bị sửa thành `2010-01-01`, nên `stale_rows = 1` với threshold 180 ngày.

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Tác động thực tế | Cách repair |
| --- | --- | --- | --- |
| Drop latest records | Xóa 2 records mới nhất | Dataset 24 → 22 trước khi duplicate | Dựng lại từ raw snapshot |
| Blank summary | Xóa summary của 2 rows | Summary completeness fail | Re-run cleaning chuẩn |
| Noise injection | Chèn chuỗi garbled vào 2 summaries | Chất lượng context giảm | Re-run cleaning chuẩn |
| Truncate title | Cắt title của 2 rows | Metadata/retrieval signal giảm | Re-run cleaning chuẩn |
| Stale date | Đặt một row thành 2010, age 5,000 | Freshness fail | Re-run cleaning chuẩn |
| Duplicate row | Sao chép một record | `paper_id_unique` fail | Re-run cleaning chuẩn |

`data/results/corruption_log.json` lưu loại lỗi, paper ID bị tác động và chi tiết từng bước. Repair chỉ dùng `data/raw/crossref_records.json`, do đó không phụ thuộc biến động dữ liệu Crossref ở thời điểm chạy lại.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Ảnh hưởng corruption | Mức phục hồi |
| --- | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 0.9000 | 0.8000 | 0.9000 | -0.1000 | Khôi phục hoàn toàn |
| `mean_token_f1` | 0.0805 | 0.0410 | 0.0805 | -0.0395 | Khôi phục hoàn toàn |
| `judge_accuracy` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | Không thay đổi |
| `mean_judge_score` | 1.0 | 1.0 | 1.0 | 0.0 | Không thay đổi |
| Quality checks | Pass 8/8 | Fail 4/8 | Pass 8/8 | Degrade | Khôi phục hoàn toàn |
| Freshness | Fresh | Stale | Fresh | Degrade | Khôi phục hoàn toàn |

Hai quan hệ nhân quả được artifact hỗ trợ là:

1. Duplicate/blank/noisy summary/stale date → quality/freshness fail → retrieval hit rate và token F1 giảm.
2. Repair từ raw snapshot → quality/freshness trở lại pass/fresh → retrieval hit rate và token F1 trở về baseline.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Lần evaluation đầu retrieval yếu và không thể hiện rõ tác động corruption.
- **Nguyên nhân:** Câu hỏi tiếng Việt không đồng nhất với phần lớn corpus/embedding tiếng Anh.
- **Cách xử lý:** Chuẩn hóa frozen test set sang tiếng Anh trước khi chạy lại toàn bộ ba trạng thái.
- **Xác minh:** Baseline retrieval hit rate đạt 0.9; corrupted giảm 0.8; repaired trở về 0.9 trên cùng test set.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| QA fallback lấy câu đầu summary | Judge accuracy/score vẫn thấp | Dùng answer generation dựa trên top-k contexts hoặc extractor factual |
| Embedding/corpus thiên về tiếng Anh | Câu hỏi Việt làm retrieval yếu | Dùng multilingual embedding nếu cần hỗ trợ truy vấn tiếng Việt |
| Ragas chưa chạy | Thiếu các Ragas metrics | Bật `RUN_RAGAS=1` khi có LLM/embedding environment phù hợp |
| Chưa có alert tự động | Chỉ phát hiện sau khi chạy report | Gửi cảnh báo khi quality status là fail |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và phân công khớp với các báo cáo cá nhân.
- [x] Baseline, corrupted và repaired đã chạy trên cùng frozen test set.
- [x] Metrics khớp artifact trong `data/results/`.
- [x] Quality/freshness conclusions khớp JSON trong `data/quality/`.
- [x] Raw, clean, embedding, eval, results và reports artifacts đều có.
- [x] Bốn thành viên có báo cáo riêng trong `report/`.
- [x] Không đưa API key, token hoặc `.env` vào report.
