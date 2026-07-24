# Lambda Processor / Glue ETL (Giai đoạn Xử lý - ETL)

Thư mục này chứa code Python tự động làm sạch dữ liệu. Có thể đóng gói bằng Docker.

### Các việc cần làm (To-Do):
1. Tạo \main.py\: Tự động thức dậy khi có sự kiện (Event) file JSON mới rớt vào S3 Raw.
2. Dùng \wswrangler\ và \pandas\ đọc file JSON đó.
3. Xóa các dòng bị lỗi, null, hoặc trùng lặp.
4. Convert JSON sang định dạng siêu nén **Parquet**.
5. Ghi file Parquet lên **S3 Curated Bucket** và tự động ghi Schema vào **Glue Data Catalog**.
