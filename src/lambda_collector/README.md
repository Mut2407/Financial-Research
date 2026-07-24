# Lambda Collector (Giai đoạn Thu thập - Ingestion)

Thư mục này chứa code Python để kích hoạt hệ thống chạy định kỳ.

### Các việc cần làm (To-Do):
1. Tạo \main.py\: Hàm gọi API Vnstock để lấy danh sách 30 mã VN30.
2. Dùng thư viện \oto3\ kết nối vào Amazon SQS.
3. Tạo 30 tin nhắn (mỗi tin chứa 1 mã cổ phiếu) thả vào SQS.
4. Tạo \equirements.txt\: Chứa các thư viện cần thiết (boto3, requests).
