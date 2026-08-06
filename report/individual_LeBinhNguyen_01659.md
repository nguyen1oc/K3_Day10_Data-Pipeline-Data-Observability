# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Lê Bình Nguyên |
| MSSV | 2A202601659 |
| Khóa/Lớp | K3 |
| Tên nhóm | bopc |
| Vai trò chính | Clean data và sinh testcase |
| Repository | https://github.com/VinUni-AI20k/K3_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Cleaning pipeline | src/ingestion/cleaning.py | Raw paper records từ Crossref | Cleaned CSV/JSON, dataframe sạch, text_for_embedding | Hoàn thành |
| Test case generation và validation | src/evaluation/testset.py | Cleaned dataframe và file data/eval/test_set.json | Test set đã được đóng băng và kiểm tra schema/document ID | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Hiểu luồng pipeline | Pipeline baseline | Hiểu cách dữ liệu sạch và testcase được dùng để chạy evaluation |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Chuẩn hóa dữ liệu thô thành dữ liệu sạch | src/ingestion/cleaning.py | Các file data/clean/papers_clean.csv và data/clean/papers_clean.json | Kiểm tra artifact và report baseline |
| Áp dụng quy tắc cleaning | src/ingestion/cleaning.py | Loại bỏ record thiếu title/summary ngắn, làm sạch HTML/XML, tạo text_for_embedding, tính age_days | Xem kết quả trong cleaned dataset |
| Sinh và kiểm tra testcase cho evaluation | src/evaluation/testset.py | File data/eval/test_set.json | Kiểm tra schema và kiểm tra ground_truth_doc_ids tồn tại trong cleaned data |

Output cụ thể mà phần việc tạo ra là dữ liệu sạch để dùng cho embedding và test set dùng cho evaluation.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong pipeline RAG, dữ liệu đầu vào cần được chuẩn hóa trước khi embedding và đánh giá. Nếu raw record có title thiếu, summary quá ngắn, có tag HTML/XML hoặc dữ liệu ngày tháng không hợp lệ thì dữ liệu sẽ không đủ chất lượng để dùng cho retrieval và evaluation.

### Cách triển khai

Tôi triển khai các quy tắc cleaning để loại bỏ record không đủ điều kiện, làm sạch title và summary, tính age_days từ published date, nối authors/categories thành chuỗi có cấu trúc, tạo text_for_embedding và deduplicate theo paper_id. Ngoài ra, tôi chuẩn bị và kiểm tra test set để đảm bảo từng câu hỏi có ground truth và document ID hợp lệ trước khi chạy evaluation.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Raw paper records từ Crossref và ngày chạy để tính age_days |
| Output | Dataframe sạch, file CSV/JSON cleaned, text_for_embedding và test set đã validate |
| Module phụ thuộc | src/ingestion/crossref.py, src/retrieval/index.py |
| Module sử dụng output | src/pipelines/phase1.py, src/evaluation/metrics.py |
| Điều kiện lỗi cần xử lý | Record thiếu title, summary quá ngắn, summary rỗng sau khi làm sạch, hoặc ground_truth_doc_ids không tồn tại trong cleaned data |

### Cách xác minh

```bash
python script\run_corruption_flow.py
```

- Kết quả mong đợi: pipeline dùng được dữ liệu sạch và test set đã chuẩn bị.
- Kết quả thực tế: script chạy thành công và sinh ra các artifact metrics/report từ pipeline.
- Artifact/log: data/clean/, data/eval/test_set.json, data/results/baseline_metrics.json.

## 5. Một quyết định kỹ thuật quan trọng

- Bối cảnh: Cần có một tập dữ liệu và test set ổn định trước khi chạy evaluation.
- Các phương án đã cân nhắc: dùng raw data trực tiếp hoặc dùng một cleaned dataset và frozen test set.
- Phương án đã chọn: dùng cleaned dataset và giữ một frozen test set thống nhất.
- Lý do: giúp dữ liệu đầu vào nhất quán và các câu hỏi đánh giá có thể so sánh được.
- Bằng chứng quyết định phù hợp: file data/eval/test_set.json và các artifact clean dataset được dùng trong pipeline baseline.

## 6. Một lỗi hoặc blocker đã xử lý

- Triệu chứng/lỗi nguyên văn: Một số record bị loại bỏ vì thiếu title hoặc summary quá ngắn, và một số testcase có document ID không khớp với cleaned data.
- Lệnh hoặc bước tái hiện: chạy pipeline và kiểm tra validation trong module cleaning/testset.
- Nguyên nhân gốc: dữ liệu raw có nhiều trường thiếu hoặc không đủ chất lượng, đồng thời test set cần phải khớp với các paper_id có thật trong cleaned dataset.
- Cách xử lý: loại bỏ các record không đạt tiêu chuẩn và chỉnh sửa/kiểm tra lại test set trước khi chạy evaluation.
- Cách xác minh sau khi sửa: kiểm tra lại cleaned dataset và test set bằng cách chạy pipeline và xem các output trong data/clean và data/eval.
- Điều học được: việc chuẩn hóa dữ liệu và kiểm tra test set trước khi chạy là bước rất quan trọng.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu đi từ Crossref đến vector index bằng cách: fetch raw records, chuyển thành clean records, tạo text_for_embedding và build Chroma index.
2. Evaluation set và ground-truth document IDs được dùng để đo retrieval/answer quality bằng cách so sánh câu trả lời của agent với câu hỏi và document IDs chuẩn.
3. Clean data và test set là nền tảng cho mọi bước sau, vì nếu đầu vào không chuẩn thì kết quả evaluation sẽ bị ảnh hưởng.
4. Test set cần được giữ thống nhất giữa các trạng thái baseline và sau corruption để so sánh có ý nghĩa.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Nhận xét của cá nhân |
| --- | ---: | --- |
| retrieval_hit_rate | 0.9000 | Dữ liệu sạch giúp pipeline có chất lượng retrieval tốt hơn so với dữ liệu kém chuẩn |
| mean_token_f1 | 0.0805 | F1 phản ánh chất lượng câu trả lời khi đầu vào đã được chuẩn hóa |
| judge_accuracy | 0.0000 | Đây là metric chưa cho thấy khác biệt rõ trong kết quả hiện tại |
| mean_judge_score | 1.0000 | Score ổn định nhưng không phải chỉ số chính để đánh giá phần việc cleaning/testset |

### Kết luận từ số liệu

Clean data và test set chuẩn là nền tảng để pipeline có thể chạy ổn định. Khi dữ liệu đầu vào được chuẩn hóa và test set đúng schema thì các bước tiếp theo như embedding và evaluation mới có thể diễn ra đúng mục đích.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Clean data là bước nền tảng: nếu dữ liệu đầu vào không sạch thì toàn bộ pipeline sẽ bị ảnh hưởng.
2. Test set cần được chuẩn hóa kỹ trước khi dùng, vì một lỗi nhỏ trong ground_truth_doc_ids có thể làm evaluation sai.
3. Data quality ảnh hưởng trực tiếp đến tính ổn định của pipeline và kết quả retrieval.

### Nếu có thêm thời gian

Tôi sẽ cải thiện thêm việc kiểm tra schema tự động trước khi sinh test set và chuẩn hóa dữ liệu ở mức chặt chẽ hơn để giảm lỗi ở các bản ghi đầu vào.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lê Bình Nguyên
**Ngày xác nhận:** 2026-08-06
