# Individual Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyen Thien Loc |
| MSSV | 2A202601479 |
| Khóa/Lớp | K3 |
| Tên nhóm | bo pc |
| Vai trò chính | Team lead; Data Observability Owner |
| Repository | [K3_Day10_Data-Pipeline-Data-Observability](https://github.com/nguyen1oc/K3_Day10_Data-Pipeline-Data-Observability) |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Data quality | `src/observability/quality.py`: `run_data_quality_checks` | Cleaned/corrupted/repaired DataFrame và `Settings` | JSON quality report trong `data/quality/` | Hoàn thành |
| Freshness monitoring | `src/observability/quality.py`: `build_freshness_report` | DataFrame đã clean và ngưỡng freshness | JSON freshness report | Hoàn thành |
| Baseline reporting | `src/observability/reporting.py`: `generate_phase1_report` | Source summary, metrics, quality, freshness | `data/reports/phase1_report.md` | Hoàn thành |
| Comparison reporting | `src/observability/reporting.py`: `generate_corruption_report` | Metrics/quality/freshness của các trạng thái | `data/reports/corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Điều phối tích hợp | Pipeline baseline và corruption flow | Kiểm tra artifact của ba trạng thái, đường dẫn output và tính nhất quán giữa metric/report |
| Phân tích kết quả | Evaluation và retrieval | Xác định baseline retrieval/answering yếu khiến metric không thể hiện tác động của corruption |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Kiểm tra quality | `data/quality/baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json` | Baseline và repaired pass 8/8 checks; corrupted fail 4/8 checks | Đọc JSON reports sau hai pipeline runs |
| Theo dõi freshness | `freshness_report.json`, `corrupted_freshness_report.json`, `repaired_freshness_report.json` | Baseline/repaired fresh; corrupted có 1 stale row | Đối chiếu `stale_rows`, `is_fresh` và ngưỡng 180 ngày |
| Báo cáo baseline | `data/reports/phase1_report.md` | Tổng hợp nguồn, metrics, quality và freshness | Mở Markdown report và đối chiếu JSON artifact |
| Báo cáo so sánh | `data/reports/corruption_report.md` | So sánh baseline/corrupted/repaired | Đối chiếu report với `data/results/*_metrics.json` |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline cần phát hiện dữ liệu có vấn đề trước khi người dùng nhận câu trả lời sai. Vì vậy, quality checks không chỉ kiểm tra pipeline có chạy hay không mà kiểm tra completeness, uniqueness, validity và freshness của corpus ở cả ba trạng thái.

### Cách triển khai

`run_data_quality_checks` kiểm tra: schema cột bắt buộc, row count, `paper_id` rỗng, `paper_id` trùng, title rỗng, summary rỗng, summary ngắn hơn 40 ký tự và `age_days` vượt ngưỡng 180 ngày. Hàm ghi danh sách check có `passed`, `observed` và `expected` để report có thể giải thích nguyên nhân fail.

`build_freshness_report` tổng hợp ngày xuất bản mới nhất/cũ nhất, số dòng stale, số ngày không hợp lệ và cờ `is_fresh`. Reporting module chỉ nhận các payload đã có và ghi Markdown; nhờ đó report không tự tính lại metric hoặc quality, tránh lệch với artifact.

### Input, output và contract

| Thành phần | Contract |
| --- | --- |
| Input DataFrame | Có các cột `paper_id`, `title`, `summary`, `published`, `age_days` sau cleaning |
| Quality output | `overall_passed`, `total_rows`, threshold và danh sách `checks` |
| Freshness output | latest/oldest publication date, stale/invalid row counts, `is_fresh` |
| Reporting input | Metrics JSON, quality payload, freshness payload do pipeline tạo |
| Reporting output | Markdown trong `data/reports/` phản ánh đúng các payload input |

### Cách xác minh

- Baseline: 24 rows, pass 8/8 checks; newest publication `2026-08-01`, oldest `2026-02-12`, `stale_rows = 0`.
- Corrupted: 23 rows, fail uniqueness, blank/short summary và freshness; `stale_rows = 1`.
- Repaired: 24 rows, pass lại 8/8 checks, `stale_rows = 0`.

## 5. Một quyết định kỹ thuật quan trọng

Repair được đánh giá bằng cách build lại dataset từ `data/raw/crossref_records.json` qua cleaning logic chuẩn, thay vì vá trực tiếp `papers_clean_corrupted.csv`. Cách này giữ raw snapshot là nguồn đáng tin cậy, tái lập được thí nghiệm và cho phép chứng minh repair đã khôi phục quality/freshness.

## 6. Một lỗi hoặc blocker đã xử lý

Lần evaluation đầu dùng câu hỏi tiếng Việt trong khi corpus và embedding baseline thiên về tiếng Anh, làm retrieval yếu. Frozen test set đã được chuẩn hóa sang câu hỏi/ground truth tiếng Anh trước khi chạy lại toàn bộ baseline, corrupted và repaired. Kết quả retrieval hit rate baseline đạt 0.9; corruption làm giảm còn 0.8; repair trở lại 0.9, nên thí nghiệm hiện đã đo được tác động và sự phục hồi.

Blocker còn lại là answer extraction. Trong `qa.py`, đa số câu hỏi factual vẫn đi vào fallback lấy câu đầu tiên của summary. `baseline_answers.json` cho thấy các answer là phần mở đầu abstract thay vì số liệu/tên mô hình được hỏi; vì vậy `judge_accuracy` vẫn 0.0 và `mean_judge_score` vẫn 1.0, dù retrieval đã tốt hơn.

## 7. Hiểu biết về luồng end-to-end

```text
Crossref API → raw records → cleaning → embedding/ChromaDB → frozen test set
→ evaluation baseline → quality/freshness report
→ corruption → re-index/evaluate → quality/freshness report
→ repair từ raw records → re-index/evaluate → comparison report
```

Các quality/freshness checks chạy sau khi dataset cho từng trạng thái được tạo; reporting chạy cuối mỗi flow để tổng hợp artifact. Baseline, corrupted và repaired dùng chung frozen test set để comparison có ý nghĩa.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 0.9000 | 0.8000 | 0.9000 | Corruption giảm 0.1; repair khôi phục đúng baseline |
| `mean_token_f1` | 0.0805 | 0.0410 | 0.0805 | Corruption làm giảm gần một nửa; repair khôi phục đúng baseline |
| `judge_accuracy` | 0.0000 | 0.0000 | 0.0000 | Không có câu trả lời nào được judge là materially correct |
| `mean_judge_score` | 1.0 | 1.0 | 1.0 | Baseline QA chưa đáp ứng câu hỏi factual |
| Quality | Pass 8/8 | Fail 4/8 | Pass 8/8 | Observability phát hiện và xác nhận repair |
| Freshness | Fresh | Stale | Fresh | Corruption tạo một record 5,000 ngày tuổi; repair khôi phục |

### Kết luận từ số liệu

1. Corruption tạo duplicate, blank/short summary và stale date; các signal này làm corrupted quality fail 4/8 checks và freshness thành stale.
2. Trên cùng frozen test set, corruption làm retrieval hit rate giảm từ 0.9 xuống 0.8 và mean token F1 giảm từ 0.0805 xuống 0.0410.
3. Repair từ raw records phục hồi 24 rows, pass 8/8 quality checks, freshness fresh, retrieval hit rate 0.9 và mean token F1 0.0805; các giá trị này bằng baseline của lần chạy hiện tại.
4. Judge metrics vẫn không đổi ở mức thấp vì answer extraction chưa trích xuất đúng fact được hỏi. Đây là giới hạn của bước answer generation, không phủ định kết quả recovery của retrieval/data quality.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Data observability giúp phát hiện dataset lỗi ngay cả khi metric agent chưa phản ánh sự thay đổi.
2. Raw artifact là điều kiện quan trọng để repair tái lập được và không phụ thuộc vào dữ liệu nguồn sống.
3. Quality tốt không tự động đảm bảo RAG tốt; retrieval, ngôn ngữ câu hỏi/corpus và answer extraction cần được đánh giá riêng.

### Nếu có thêm thời gian

Kế hoạch cải thiện được ưu tiên theo thứ tự sau:

1. Thay fallback `first_sentence(summary)` trong QA bằng answer generation dựa trên top-k contexts, với ràng buộc chỉ trả lời thông tin có trong context. Cách này phù hợp hơn với câu hỏi factual yêu cầu số liệu, tên mô hình hoặc kết quả thực nghiệm.
2. Bổ sung extraction rule phù hợp với các dạng factual question hoặc dùng LLM để tổng hợp answer từ context; mục tiêu là cải thiện `judge_accuracy` và `mean_judge_score`, không chỉ retrieval hit rate.
3. Giữ thống nhất ngôn ngữ giữa query và corpus/embedding. Nếu cần quay lại câu hỏi tiếng Việt, dùng multilingual embedding và rebuild toàn bộ Chroma index.
4. Trước mỗi thí nghiệm, chạy baseline trước; sau khi freeze test set thì giữ nguyên test set cho đầy đủ baseline/corrupted/repaired của cùng một lần chạy.

Sau các thay đổi trên, frozen test set phải được giữ không đổi trong ba trạng thái baseline/corrupted/repaired của cùng một thí nghiệm.

## 10. Cam kết của thành viên

- [x] Nội dung phản ánh đúng phần việc và artifact đã kiểm tra.
- [x] Có thể giải thích luồng end-to-end và vai trò observability.
- [x] Kết luận về quality/freshness có artifact để đối chiếu.
- [x] Không ghi pipeline agent đã cải thiện khi metric không chứng minh điều đó.
- [x] Báo cáo không chứa API key, token hoặc secret.

**Họ và tên:** Nguyen Thien Loc  
**Ngày xác nhận:** 2026-08-06
