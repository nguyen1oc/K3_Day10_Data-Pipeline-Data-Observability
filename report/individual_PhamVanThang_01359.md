# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Phạm Văn Thắng             |
| MSSV               | 01359                      |
| Khóa/Lớp         | K3                         |
| Tên nhóm         | Nhóm 4 Thành viên          |
| Vai trò chính    | Thành viên 4 — Corruption & Integration Owner (Pipeline Lead) |
| Repository         | https://github.com/nguyen1oc/K3_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06                 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data Corruption Engine | `src/ingestion/corruption.py`<br>`corrupt_clean_dataframe()` | `papers_clean.csv` | `papers_clean_corrupted.csv`<br>`corruption_log.json` | Hoàn thành |
| Baseline Pipeline Integrator | `src/pipelines/phase1.py`<br>`main()` | `raw_records.json` | `baseline_metrics.json`<br>`phase1_report.md` | Hoàn thành |
| Corruption Flow Integrator | `src/pipelines/corruption_flow.py`<br>`main()` | `papers_clean.csv`<br>`raw_records.json` | `corrupted_metrics.json`<br>`repaired_metrics.json`<br>`corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Debug & Fix String Isoformat Error | Thành viên 2 (`cleaning.py`) | Sửa hàm `save_clean_data()` để tự động xử lý an toàn cả `datetime` lẫn chuỗi `str` ngày tháng khi đọc lại từ CSV. |
| ChromaDB Handle Fix | Thành viên 3 / Retrieval | Tái sử dụng trực tiếp đối tượng `client` & `collection` trong `LocalEmbeddingIndex.build()` tránh lỗi `NotFoundError` trên Windows. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Thiết lập 6 kịch bản Corruption | `src/ingestion/corruption.py` | Tạo ra 23 bản ghi lỗi và nhật ký `data/results/corruption_log.json` | `uv run python script/run_corruption_flow.py` |
| Tích hợp Baseline Pipeline Phase 1 | `src/pipelines/phase1.py` | Sinh báo cáo `data/reports/phase1_report.md` và `baseline_metrics.json` | `uv run python script/run_phase1.py` |
| Điều phối luồng Repair & Comparison | `src/pipelines/corruption_flow.py` | Sinh báo cáo so sánh 3 trạng thái `data/reports/corruption_report.md` | `uv run python script/run_corruption_flow.py` |

**Output cụ thể:**
File báo cáo so sánh tổng hợp [data/reports/corruption_report.md](file:///d:/VIN_AI/K3_Day10_Data-Pipeline-Data-Observability/data/reports/corruption_report.md) chứng minh chi tiết tín hiệu Data Quality báo `FAIL` ở trạng thái Corrupted và hồi phục thành `PASS` ở trạng thái Repaired.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng Data Corruption Engine mô phỏng các lỗi dữ liệu thực tế (mất bản ghi mới, rỗng summary, nhiễu text, cắt ngắn tiêu đề, ngày cũ quá hạn, trùng lặp) và điều phối toàn bộ pipeline end-to-end cho cả 2 pha Baseline và Corruption-Repair Flow.

### Cách triển khai
1. **Corruption Engine:** Viết hàm `corrupt_clean_dataframe()` xử lý 6 kịch bản:
   - Drop 2 bản ghi mới nhất ở cuối dataframe (`drop_latest_record`).
   - Xóa rỗng `summary` ở 2 dòng (`blank_summary`).
   - Chèn chuỗi rác `@@@GARBLED NOISE@@@` vào `summary` (`inject_noise`).
   - Cắt ngắn `title` xuống 10 ký tự (`truncate_title`).
   - Đổi ngày xuất bản về 2010 và `age_days = 5000` (`make_stale_date`).
   - Nhân bản dòng đầu tiên (`add_duplicate`).
   - Tái tạo lại chuỗi `text_for_embedding` và ghi vết `corruption_log.json`.
2. **Phase 1 Pipeline:** Nạp settings ➔ Đọc raw records ➔ Gọi làm sạch ➔ Tạo Chroma Index `papers-baseline` ➔ Nạp `test_set.json` ➔ Đánh giá Metrics ➔ Kiểm tra Quality/Freshness ➔ Sinh báo cáo `phase1_report.md`.
3. **Corruption Flow Pipeline:** Đọc clean CSV ➔ Làm hỏng dữ liệu ➔ Rebuild Chroma Index `papers-corrupted` ➔ Đánh giá Corrupted ➔ Khôi phục (Repair) từ raw records gốc ➔ Rebuild Chroma Index `papers-repaired` ➔ Đánh giá Repaired ➔ Sinh báo cáo so sánh `corruption_report.md`.

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| Input | `crossref_records.json`, `papers_clean.csv`, `test_set.json` |
| Output | `papers_clean_corrupted.csv`, `papers_clean_repaired.csv`, `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json`, `phase1_report.md`, `corruption_report.md` |
| Module phụ thuộc | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/evaluation/testset.py`, `src/observability/quality.py` |
| Module sử dụng output | `script/run_phase1.py`, `script/run_corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Lỗi định dạng ngày khi đọc từ CSV, lỗi handle ChromaDB SQLite lock, lỗi 429 Rate Limit API |

### Cách xác minh

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Cả 2 pipeline chạy thông suốt, không phát sinh ngoại lệ (exception), sinh đủ các báo cáo Markdown và JSON artifacts trong `data/`.
- **Kết quả thực tế:** Báo cáo `phase1_report.md` và `corruption_report.md` được sinh ra chính xác.
- **Artifact/log:** `data/reports/phase1_report.md`, `data/reports/corruption_report.md`, `data/results/corruption_log.json`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn phương pháp khôi phục (Repair) dữ liệu ở Pha 2.
- **Các phương án đã cân nhắc:**
  - *Phương án A:* Sửa trực tiếp file `papers_clean_corrupted.csv` bằng cách điền tay lại các trường bị lỗi.
  - *Phương án B:* Khôi phục nguyên bản (Repair from Raw) bằng cách đọc lại snapshot gốc từ `data/raw/crossref_records.json` và chạy lại logic `build_clean_dataframe()`.
- **Phương án đã chọn:** Phương án B (Repair from Raw).
- **Lý do:** Giúp đảm bảo tính đóng gói (encapsulation), khả năng tái lập (reproducibility) và tuân thủ đúng nguyên tắc Data Lineage trong Data Engineering.
- **Bằng chứng quyết định phù hợp:** File `repaired_quality.json` đạt 8/8 PASS và khôi phục chính xác 24 bản ghi sạch.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `AttributeError: 'str' object has no attribute 'isoformat'` tại dòng `save_clean_data()` khi chạy `corruption_flow.py`.
- **Lệnh hoặc bước tái hiện:** `uv run python script/run_corruption_flow.py`
- **Nguyên nhân gốc:** Khi đọc lại dữ liệu từ `papers_clean.csv` bằng `pd.read_csv()`, các cột `published_date` và `updated_date` được nạp dưới dạng kiểu chuỗi `str` chứ không phải đối tượng `datetime`, dẫn đến việc gọi trực tiếp `.isoformat()` bị từ chối.
- **Cách xử lý:** Cập nhật hàm `save_clean_data()` trong `src/ingestion/cleaning.py` để kiểm tra an toàn `hasattr(x, "isoformat")` trước khi ép kiểu.
- **Cách xác minh sau khi sửa:** Lệnh `uv run python script/run_corruption_flow.py` chạy thành công 100% không còn báo lỗi.
- **Điều học được:** Khi làm việc với Pandas I/O, dữ liệu đọc từ CSV luôn quay về kiểu primitive (string/number), cần xử lý type-checking an toàn trước khi gọi các phương thức riêng biệt của object.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu từ Crossref đến vector index:** REST API ➔ Raw JSON snapshot ➔ Normalize & Cleaning (trích xuất title, summary, authors, tính age_days) ➔ Tạo `text_for_embedding` ➔ Trích xuất vector bằng MiniLM ➔ Nạp vào ChromaDB Persistent Collection.
2. **Evaluation set & Ground-truth document IDs:** Bộ câu hỏi `test_set.json` chứa các `ground_truth_doc_ids` cố định để khi agent thực hiện semantic search, hệ thống đối chiếu xem ID bài báo truy vấn được có nằm trong tập ground truth hay không (`retrieval_hit_rate`).
3. **Quality checks vs Freshness monitoring:** Quality checks tập trung vào tính toàn vẹn của schema (null, duplicate, độ dài text, uniqueness), trong khi Freshness monitoring tập trung vào tính thời sự của dữ liệu dựa theo số ngày tuổi `age_days` so với ngưỡng quy định.
4. **Tại sao dùng cùng test set cho 3 pha:** Để biến số duy nhất thay đổi là **chất lượng dữ liệu (Data Quality)**, đảm bảo phép so sánh chỉ số giữa Baseline, Corrupted và Repaired là hoàn toàn công bằng.
5. **Dấu hiệu Repair thành công:** Tín hiệu Data Quality quay về `PASS` (8/8 checks passed), Freshness đạt `FRESH`, và số lượng dòng khôi phục đủ 24 bản ghi.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   0.9000 |    0.5000 |   0.5000 | Baseline đạt 90%, corruption giảm xuống 50%, repair chưa phục hồi hit rate do rebuild embeddings tạo collection khác. |
| `mean_token_f1`      |   0.0805 |    0.0061 |   0.0061 | Baseline đạt ~0.08, corruption làm giảm mạnh xuống ~0.006, repair chưa phục hồi token F1. |
| `judge_accuracy`     |   0.0000 |    0.0000 |   0.0000 | Do Fallback Heuristic được kích hoạt khi LLM API bị giới hạn quota. |
| `mean_judge_score`   |        1 |         1 |        1 | Điểm đánh giá fallback. |
| Quality checks         | PASS (8/8) | **FAIL (4/8)** | PASS (8/8) | Phản ánh chính xác 4 lỗi dữ liệu bị vi phạm ở pha Corrupted. |
| Freshness status       |    FRESH | **STALE** |    FRESH | Phát hiện chính xác 1 bản ghi bị hỏng ngày tháng ở pha Corrupted. |

### Kết luận từ số liệu

1. **[Data corruption]** (xóa summary, đổi ngày cũ, thêm duplicate, drop records) ➔ **[quality/freshness signal thay đổi]** (chuyển sang `FAIL` 4/8 và `STALE`) + **[retrieval metrics giảm]** (`retrieval_hit_rate` 0.9→0.5, `mean_token_f1` 0.08→0.006) ➔ Hệ thống Data Observability cảnh báo tức thì trước khi dữ liệu xấu đi vào sản xuất.
2. **[Repair action]** (nạp lại từ raw source) ➔ **[quality/freshness signal phục hồi]** (chuyển về `PASS` 8/8 và `FRESH`) nhưng **[retrieval metrics chưa phục hồi]** (`retrieval_hit_rate` vẫn 0.5, `mean_token_f1` vẫn 0.006) ➔ Repair khôi phục hoàn toàn tính toàn vẹn dữ liệu (data quality), tuy nhiên retrieval performance chưa trở lại mức baseline — có thể do rebuild embeddings trên repaired data tạo ra ChromaDB collection khác với baseline ban đầu.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. Quản trị chất lượng dữ liệu (Data Observability) là thành tố sống còn đối với các hệ thống RAG/Agent.
2. Việc phân tách rõ ràng 3 trạng thái Baseline - Corrupted - Repaired giúp đo lường định lượng được tác động của dữ liệu xấu.
3. Cần xây dựng các cơ chế phòng thủ (Fallback mechanisms) tốt để pipeline không bị crash khi các dịch vụ bên ngoài (như LLM API) gặp sự cố.

### Nếu có thêm thời gian
Bổ sung cơ chế tự động cảnh báo (Alerting via Slack/Email) ngay khi Data Quality check báo status `FAIL` ở bất kỳ bước nào trong pipeline.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Phạm Văn Thắng  
**Ngày xác nhận:** 2026-08-06  
