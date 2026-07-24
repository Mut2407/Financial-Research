# Lambda Worker (Giai đoạn Thu thập - Ingestion)

Thư mục này chứa code Python cào dữ liệu thực tế. Yêu cầu đóng gói bằng Docker vì thư viện khá nặng.

### Các việc cần làm (To-Do):
1. Tạo \main.py\: Nhận tin nhắn chứa tên mã từ SQS.
2. Dùng \nstock\ cào giá lịch sử của mã đó (OHLCV).
3. Dùng \pandas\ xử lý thô và xuất ra định dạng JSON.
4. Dùng \oto3\ upload file JSON này lên **S3 Raw Bucket**.
5. Viết \Dockerfile\ và \equirements.txt\ để đẩy lên Amazon ECR.
