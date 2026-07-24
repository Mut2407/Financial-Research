# Hạ tầng (Infrastructure as Code)

Thư mục này chứa code Terraform. Phân công cho bạn làm DevOps.

### Các việc cần làm (To-Do):
1. Tạo \provider.tf\ cấu hình AWS và S3 Backend.
2. Tạo \main.tf\ khởi tạo: S3 Buckets (Raw & Curated), SQS Queue, EventBridge Rule.
3. Cấu hình \iam.tf\ cấp quyền Least Privilege cho các Lambda.
4. Tạo API Gateway và kết nối nó vào Lambda Reader.
