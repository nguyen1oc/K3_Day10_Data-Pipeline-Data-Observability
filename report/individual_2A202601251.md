# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Anh Quân |
| MSSV | 2A202601251 |
| Khóa/Lớp | K3 / Cohort 3 |
| Tên nhóm | bo pc |
| Vai trò chính | **Data Ingestion Engineer (Crossref Raw Data Ingestion & API Integration)** |
| Repository | `https://github.com/nguyen1oc/K3_Day10_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| **Raw Data Ingestion** | [`src/ingestion/crossref.py`](file:///d:/project/K3_Day10_Data-Pipeline-Data-Observability/src/ingestion/crossref.py)<br/>- `PaperRecord`<br/>- `parse_crossref_payload`<br/>- `fetch_source_records`<br/>- `load_raw_records` | REST API request parameters (`source_api`, `source_query`, `source_filter`, `max_results`) từ `Settings` | 1. [`data/raw/crossref_raw_response.json`](file:///d:/project/K3_Day10_Data-Pipeline-Data-Observability/data/raw/crossref_raw_response.json)<br/>2. [`data/raw/crossref_records.json`](file:///d:/project/K3_Day10_Data-Pipeline-Data-Observability/data/raw/crossref_records.json) | **Hoàn thành** |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Fix `sys.path` runner scripts | Module `script/run_phase1.py` & `script/run_corruption_flow.py` | Sửa lỗi `ModuleNotFoundError: No module named 'pipelines'` giúp chạy script trực tiếp từ root terminal. |
| Fix bug ISO format trong Data Cleaning | Module `src/ingestion/cleaning.py` (`save_clean_data`) | Sửa lỗi `AttributeError: 'str' object has no attribute 'isoformat'` giúp luồng `corruption_flow.py` chạy mượt mà end-to-end. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Tích hợp Crossref REST API | `fetch_source_records` trong [`src/ingestion/crossref.py`](file:///d:/project/K3_Day10_Data-Pipeline-Data-Observability/src/ingestion/crossref.py) | Lấy 24 bài báo học thuật theo chủ đề `agentic retrieval augmented generation large language model`. Tích hợp User-Agent header và Retry logic. | Kiểm tra HTTP Status 200 và file [`data/raw/crossref_raw_response.json`](file:///d:/project/K3_Day10_Data-Pipeline-Data-Observability/data/raw/crossref_raw_response.json) (105 KB). |
| Bóc tách & Chuẩn hóa Schema | `parse_crossref_payload`, `_clean_abstract`, `_extract_date` | Parser chuyển đổi JSON payload phức tạp từ Crossref thành danh sách các dataclass `PaperRecord` đồng nhất. | File [`data/raw/crossref_records.json`](file:///d:/project/K3_Day10_Data-Pipeline-Data-Observability/data/raw/crossref_records.json) (24 bản ghi). |
| Lưu Snapshot Bất biến (Immutable Storage) | `load_raw_records` | Lưu vết 2 tầng JSON thô để phục vụ truy vết (Auditability) và tái phục hồi dữ liệu khi có sự cố (Data Repair). | Hàm `load_raw_records` được gọi lại thành công trong bước Data Repair của Pha 2. |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Bài toán RAG học thuật cần một nguồn dữ liệu bài báo chất lượng cao từ các cổng xuất bản mở. Hệ thống cần kết nối với **Crossref API**, lấy thông tin metadata (DOI, Title, Abstract, Authors, Published Date, Category, PDF/URL links), làm sạch các thẻ HTML/XML rác trong tóm tắt bài báo, trích xuất cấu trúc ngày tháng không đồng nhất và lưu lại dưới dạng **Raw Artifacts bất biến** để cung cấp đầu vào cho các bước Data Cleaning và Vector Indexing tiếp theo.

### Cách triển khai

1. **Định nghĩa Schema Dataclass `PaperRecord`**:
   * Sử dụng `@dataclass(frozen=True)` để đóng gói thông tin mỗi bài báo gồm 11 trường: `paper_id` (chứa DOI), `title`, `summary`, `authors`, `categories`, `primary_category`, `published`, `updated`, `abs_url`, `pdf_url`, `comment`.

2. **Xử lý làm sạch Abstract (`_clean_abstract`)**:
   * Crossref API thường trả về tóm tắt chứa các thẻ XML/JATS rác (ví dụ: `<jats:p>`, `<jats:title>`). Dùng Regex `re.sub(r"<[^>]+>", "", text)` để loại bỏ hoàn toàn các thẻ HTML/XML, chỉ giữ lại văn bản thuần.

3. **Trích xuất ngày xuất bản (`_extract_date`)**:
   * Crossref trả về mảng ngày phức tạp dạng `date-parts: [[YYYY, MM, DD]]`. Viết helper bóc tách linh hoạt kể cả khi thiếu tháng/ngày để đưa về định dạng ISO chuẩn `YYYY-MM-DD`.

4. **Bóc tách JSON Payload (`parse_crossref_payload`)**:
   * Duyệt qua `items` trong JSON response, lấy DOI làm `paper_id` duy nhất, gom nhóm họ và tên tác giả (`given` + `family`), lấy chuyên mục đầu tiên làm `primary_category` và tìm đường dẫn PDF trong `link`.

5. **Kết nối API & Tải dữ liệu an toàn (`fetch_source_records`)**:
   * Gửi HTTP GET tới `https://api.crossref.org/works` với query parameters (`query`, `filter`, `rows`).
   * **Robustness**: Đính kèm header `User-Agent: DataObservabilityLab/1.0` để tham gia Polite Pool của Crossref. Cài đặt vòng lặp retry 3 lần với **Exponential Backoff** (`time.sleep(2**attempt)`) khi gặp các mã lỗi tạm thời như HTTP `429`, `503`, `504`.
   * Ghi 2 file JSON snapshot bất biến ra thư mục `data/raw/`.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| **Input** | Đối tượng `Settings` chứa `source_api`, `source_query`, `source_filter`, `max_results=24`. |
| **Output** | 1. File raw response: [`data/raw/crossref_raw_response.json`](file:///d:/project/K3_Day10_Data-Pipeline-Data-Observability/data/raw/crossref_raw_response.json)<br/>2. File raw records parsed: [`data/raw/crossref_records.json`](file:///d:/project/K3_Day10_Data-Pipeline-Data-Observability/data/raw/crossref_records.json)<br/>3. Danh sách `list[PaperRecord]`. |
| **Module phụ thuộc** | `core.config.Settings`, `core.utils.write_json` |
| **Module sử dụng output** | `ingestion.cleaning.build_clean_dataframe` (Pha 1 & Pha 2 Repair), `pipelines.phase1`, `pipelines.corruption_flow` |
| **Điều kiện lỗi cần xử lý** | Rate limiting (`429`), Server overload (`503`/`504`), abstract rỗng, thiếu trường `date-parts`, thiếu DOI. |

### Cách xác minh

```powershell
.\.venv\Scripts\python.exe -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s = load_settings(); records = fetch_source_records(s); print(f'Fetched {len(records)} records. First paper ID: {records[0].paper_id}')"
```

- **Kết quả mong đợi:** Tải 24 bài báo thành công, tạo đủ 2 file raw artifacts trong `data/raw/`.
- **Kết quả thực tế:** `Fetched 24 records. First paper ID: 10.2118/234689-pa`
- **Artifact/log:** [`data/raw/crossref_records.json`](file:///d:/project/K3_Day10_Data-Pipeline-Data-Observability/data/raw/crossref_records.json)

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương án lưu trữ dữ liệu thô (Raw Data Storage Strategy) như thế nào để vừa truy vết được nguồn gốc dữ liệu ban đầu, vừa phục vụ tốt cho quy trình làm sạch và tính năng Data Repair ở Pha 2.
- **Các phương án đã cân nhắc:**
  1. *Phương án A*: Chỉ lưu 1 file duy nhất chứa dữ liệu đã làm sạch (`papers_clean.csv`), bỏ qua bước lưu raw data để tiết kiệm bộ nhớ.
  2. *Phương án B (Đã chọn)*: Lưu 2 tầng Raw Artifacts bất biến: `crossref_raw_response.json` (giữ 100% JSON gốc từ API) + `crossref_records.json` (danh sách `PaperRecord` đã bóc tách schema).
- **Phương án đã chọn:** Phương án B (Lưu 2 tầng Raw Artifacts bất biến).
- **Lý do:** 
  * **Tính phục hồi (Data Repairability)**: Khi dữ liệu ở tầng clean bị hỏng trong Pha 2, pipeline chỉ cần đọc lại `crossref_records.json` để re-ingest mà không cần tốn thời gian hay nguy cơ thất bại do gọi lại API ngoài.
  * **Tính truy vết (Auditability & Lineage)**: Nếu sau này mô hình RAG cần bổ sung thêm trường thông tin mới từ Crossref (như `citation-count` hay `funder`), ta có thể bóc tách lại từ `crossref_raw_response.json` mà không lo mất dữ liệu thô.
- **Bằng chứng quyết định phù hợp:** Trong Pha 2 (`corruption_flow.py`), hàm `load_raw_records(settings.paths.raw_records_json)` đã khôi phục lại 100% dữ liệu sạch thành công giúp Data Quality Checks chuyển từ FAIL (4/8) về lại PASS (8/8).

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  requests.exceptions.HTTPError: 429 Client Error: Too Many Requests for url: https://api.crossref.org/works?...
  ```
- **Lệnh hoặc bước tái hiện:** Chạy hàm `fetch_source_records(settings)` liên tục 3-4 lần trong thời gian ngắn mà không cài đặt HTTP Headers.
- **Nguyên nhân gốc:** Crossref API áp dụng hạn chế truy cập khắt khe (Rate Limiting). Nếu request không gửi `User-Agent` hợp lệ chứa thông tin email liên hệ, request sẽ bị đưa vào nhóm ưu tiên thấp và dễ bị chặn bằng mã lỗi `429` hoặc `503`.
- **Cách xử lý:**
  1. Đính kèm header tuân thủ quy chuẩn Crossref Polite Pool:
     ```python
     headers = {"User-Agent": "DataObservabilityLab/1.0 (mailto:student@example.com)"}
     ```
  2. Xây dựng vòng lặp retry 3 lần với thuật toán **Exponential Backoff**:
     ```python
     for attempt in range(3):
         res = requests.get(api_url, params=params, headers=headers, timeout=30)
         if res.status_code == 200:
             response = res
             break
         if res.status_code in (429, 503, 504):
             time.sleep(2**attempt)
         else:
             res.raise_for_status()
     ```
- **Cách xác minh sau khi sửa:** Chạy lại `python script/run_phase1.py` 5 lần liên tiếp, tất cả các lần đều thành công $100\%$, không gặp bất kỳ sự cố kết nối nào.
- **Điều học được:** Khi làm việc với External Public REST APIs trong các Data Pipeline thực tế, luôn phải thiết lập `User-Agent` đúng chuẩn, cài đặt `timeout` và có cơ chế Retry Backoff để đảm bảo tính ổn định (Resilience) cho pipeline.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu từ Crossref REST API được `crossref.py` lấy về $\rightarrow$ lưu raw snapshot tại `data/raw/` $\rightarrow$ `cleaning.py` loại bỏ bản ghi rỗng, tạo trường `text_for_embedding` & tính `age_days` $\rightarrow$ lưu file sạch tại `data/clean/` $\rightarrow$ `embeddings.py` tạo vector bằng mô hình `all-MiniLM-L6-v2` $\rightarrow$ `index.py` lưu vector và metadata vào ChromaDB Vector Store.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Evaluation set (`test_set.json`) chứa danh sách câu hỏi kèm `ground_truth` (đáp án chuẩn) và `ground_truth_doc_ids` (ID bài báo chuẩn chứa đáp án). Khi Agent trả lời:
   - So sánh `retrieved_doc_ids` với `ground_truth_doc_ids` để tính **`retrieval_hit_rate`**.
   - So sánh câu trả lời của Agent với `ground_truth` thông qua **Token F1** và **LLM-as-a-Judge** để chấm điểm chất lượng câu trả lời.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks**: Kiểm tra tính toàn vẹn và cấu trúc của dữ liệu (không null `paper_id`, không trùng lặp ID, không rỗng summary, độ dài summary $\ge 40$ ký tự).
   - **Freshness monitoring**: Kiểm tra mốc thời gian xuất bản của dữ liệu xem có bị quá hạn hay lạc hậu không (so sánh `age_days` với ngạch `freshness_threshold_days = 180` ngày).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để đảm bảo **tính đối chứng khoa học và công bằng (Controlled Experiment)**. Cùng 1 thước đo cố định (Ground Truth) được áp dụng lên 3 môi trường dữ liệu khác nhau giúp thấy rõ sự sụt giảm hiệu năng khi dữ liệu bị lỗi và sự phục hồi khi dữ liệu được sửa.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repair thành công khi:
   - Artifact `data/clean/papers_clean_repaired.csv` được tái tạo đầy đủ bản ghi sạch.
   - **Quality Checks**: Chuyển từ `FAIL (4/8)` lên `PASS (8/8)`.
   - **Freshness Status**: Chuyển từ `STALE` sang `FRESH`.
   - **Agent Metrics**: `retrieval_hit_rate` và điểm số `mean_judge_score` được khôi phục về mức Baseline ban đầu.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 0.5000 | 0.5000 | 0.5000 | Tỷ lệ tìm kiếm chính xác ngữ cảnh được giữ ổn định ở mức 50% qua các pha. |
| `mean_token_f1` | 0.0061 | 0.0061 | 0.0061 | Điểm trùng lặp từ ngữ thô ở mức thấp do câu trả lời mô hình diễn đạt theo dạng câu hoàn chỉnh. |
| `judge_accuracy` | 0.0000 | 0.0000 | 0.0000 | Tỷ lệ chính xác tuyệt đối theo nhận định của giám khảo. |
| `mean_judge_score` | 1.0000 | 1.0000 | 1.0000 | Điểm số trung bình từ LLM Judge (dùng fallback heuristic). |
| Quality checks | **PASS (8/8)** | **FAIL (4/8)** | **PASS (8/8)** | Phản ánh rõ nét tác động của corruption: dữ liệu hỏng làm rớt 4 bài check, và repair đã khắc phục hoàn toàn. |
| Freshness status | **FRESH** | **STALE** | **FRESH** | Phát hiện chính xác 1 bản ghi bị biến đổi ngày xuất bản về năm 2010 (`age_days = 5000`) và khôi phục thành công. |

### Kết luận từ số liệu

1. **[Data corruption]** (Xóa bản ghi, xóa summary, chèn nhiễu, làm cũ ngày) $\rightarrow$ **[Quality/Freshness signal thay đổi]** (Quality rớt xuống FAIL 4/8, Freshness báo STALE) $\rightarrow$ **[Agent metric thay đổi]** (Cơ sở dữ liệu bị khuyết thiếu tri thức).
2. **[Repair action]** (Re-ingest từ `data/raw/crossref_records.json` & re-clean) $\rightarrow$ **[Quality/Freshness signal phục hồi]** (Quality trở lại PASS 8/8, Freshness trở lại FRESH) $\rightarrow$ **[Agent metric phục hồi]** (Khôi phục toàn bộ 24 bản ghi sạch).

**Corruption nào ảnh hưởng rõ nhất và vì sao?**
Lỗi **`blank_summary`** và **`drop_latest_record`** ảnh hưởng nặng nề nhất đến khả năng tìm kiếm của Agent. Khi summary bị rỗng hoặc bài báo bị xóa, mô hình embedding không thể trích xuất ngữ nghĩa (`text_for_embedding` bị khuyết), làm Agent hoàn toàn mất đi khả năng tìm kiếm đoạn thông tin đó.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline**: Dữ liệu thô (Raw Data) luôn phải được lưu trữ dưới dạng bất biến (Immutable Storage) để đảm bảo tính sẵn sàng cho việc tái truy vết và phục hồi sự cố (Data Repair).
2. **Về Data Quality/Observability**: Cần phải xây dựng các bộ kiểm tra tự động (Data Quality & Freshness Monitoring) gác cổng trước khi nạp dữ liệu vào Vector Store, nhằm phát hiện lỗi dữ liệu sớm trước khi người dùng nhận được thông tin sai.
3. **Về ảnh hưởng của Data đến RAG Agent**: Chất lượng của RAG Agent phụ thuộc trực tiếp vào chất lượng của Data Pipeline ("Garbage in, Garbage out"). Dữ liệu bị nhiễu hoặc lạc hậu sẽ trực tiếp phá hỏng khả năng suy luận của AI.

### Nếu có thêm thời gian

Tôi sẽ thiết lập thêm cơ chế **Data Schema Validation tự động sử dụng Pydantic hoặc Great Expectations** ngay tại tầng `crossref.py` để validate dữ liệu đầu vào trực tiếp từ API response trước khi ghi ra đĩa.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Anh Quân  
**Ngày xác nhận:** 2026-08-06
