# Lambda Reader (Giai đoạn Phục vụ - Serving)

Thư mục này chứa code Python đóng vai trò như Backend Server API.

### Các việc cần làm (To-Do):
1. Tạo \main.py\: Nhận request từ Web thông qua API Gateway (ví dụ params: \?ticker=FPT\).
2. Biến tham số đó thành câu lệnh SQL: \SELECT * FROM vnstock_db.table WHERE ticker='FPT'\.
3. Dùng \oto3\ ra lệnh cho **Amazon Athena** quét dữ liệu thực thi câu SQL này.
4. Đọc kết quả từ Athena, gói gọn thành chuẩn JSON và \eturn\ về cho API Gateway trả cho Client.
