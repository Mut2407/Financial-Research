# Lộ Trình Triển Khai Chi Tiết Các Yêu Cầu Đang Thiếu (Financial Distress System UI)

Dựa trên tài liệu spec **`Financial_Application.txt`**, hệ thống được chia làm **8 Yêu cầu (Steps)** theo đúng thứ tự luồng xử lý pipeline dữ liệu tài chính từ đầu đến cuối.

---

## Danh Sách 8 Yêu Cầu Theo Thứ Tự Pipeline

1. **Yêu cầu 1: Quản lý & Lọc danh sách Doanh nghiệp (Company Listing & Sector Filtering)** *(Thực hiện đầu tiên)*
2. **Yêu cầu 2: Thu thập & Hiển thị Báo cáo Tài chính 3 Bảng (Financial Statements Ingestion & Viewer)**
3. **Yêu cầu 3: Chuẩn hóa Chỉ tiêu & Báo cáo Chất lượng Dữ liệu Thô (Data Normalization & Data Quality Checks)**
4. **Yêu cầu 4: Màn hình Phân tích & Tính toán Chỉ số Tài chính (Financial Ratio Engine)**
5. **Yêu cầu 5: Gán nhãn Rủi ro Kiệt quệ Tài chính & Altman Z-Score (Distress Labeling & Z-Score)**
6. **Yêu cầu 6: Màn hình Xuất Dataset & Báo cáo Tổng hợp (Dataset Export & Quality Summary)**
7. **Yêu cầu 7: Màn hình Huấn luyện & Đánh giá Mô hình AI/Machine Learning (AI/ML Studio & Model Evaluation)**
8. **Yêu cầu 8: Màn hình Cảnh báo Rủi ro & So sánh Doanh nghiệp cùng Ngành (Risk Monitoring & Peer Comparison)**

---

## Chi Tiết Kế Hoạch Cho **Yêu Cầu 1: Quản lý & Lọc danh sách Doanh nghiệp**

### Mục tiêu:
Xây dựng giao diện xem và lọc danh sách toàn bộ các doanh nghiệp niêm yết trên các sàn (HOSE, HNX, UPCOM), cho phép lọc theo ngành nghề và đặc biệt có tính năng **Loại bỏ nhóm Ngành Tài chính** (Ngân hàng, Chứng khoán, Bảo hiểm, Quỹ đầu tư) để đảm bảo dữ liệu không bị sai lệch khi đưa vào mô hình dự đoán.

### Proposed Changes

#### [Frontend Types & Services]
##### [MODIFY] [index.ts](file:///c:/Users/KYVY/Sub_Main_Project/react-frontend/src/types/index.ts)
- Cập nhật `interface Company` bổ sung các trường: `sector` / `industry`, `exchange` (HOSE/HNX/UPCOM), `is_financial` (boolean), `status` (Niêm yết/Hủy niêm yết).

##### [MODIFY] [api.ts](file:///c:/Users/KYVY/Sub_Main_Project/react-frontend/src/services/api.ts)
- Bổ sung params hỗ trợ lọc: `exchange`, `industry`, `exclude_financial` trong hàm `getCompanies`.

#### [Frontend Components & Views]
##### [NEW] [CompanyList.tsx](file:///c:/Users/KYVY/Sub_Main_Project/react-frontend/src/features/company/CompanyList.tsx)
- Màn hình quản lý danh sách doanh nghiệp:
  - Bộ lọc Sàn niêm yết (Tất cả, HOSE, HNX, UPCOM).
  - Bộ lọc Ngành nghề (Sản xuất, Bất động sản, Xây dựng, Công nghệ, v.v.).
  - **Nút công tắc (Toggle)**: *Loại bỏ ngành Tài chính (Ngân hàng, Chứng khoán, Bảo hiểm, Quỹ)*.
  - Bảng danh sách doanh nghiệp kèm Badge ngành nghề và trạng thái lọc.
  - Thống kê tổng số doanh nghiệp thỏa mãn điều kiện lọc.

##### [MODIFY] [AppLayout.tsx](file:///c:/Users/KYVY/Sub_Main_Project/react-frontend/src/components/layout/AppLayout.tsx) & [App.tsx](file:///c:/Users/KYVY/Sub_Main_Project/react-frontend/src/App.tsx)
- Bổ sung menu item **"Danh sách Công ty"** trên Navigation Sidebar.

---

## Verification Plan

### Automated Tests
- Kiểm tra TypeScript compile: `npx tsc --noEmit`
- Kiểm tra Vite build: `npm run build`

### Manual Verification
- Mở trình duyệt, chuyển đến trang "Danh sách Công ty".
- Thử bật/tắt nút "Loại bỏ ngành Tài chính" và xác nhận các mã Ngân hàng/Chứng khoán (như VCB, BID, SSI, HCM...) được ẩn/hiện chính xác.
- Kiểm tra các bộ lọc theo Sàn HOSE / HNX / UPCOM.
