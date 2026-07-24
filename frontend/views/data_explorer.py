from datetime import date, timedelta
import math # Import thêm thư viện math để tính tổng số trang

import pandas as pd
import streamlit as st

from utils.api_client import ApiClientError, get_prices, run_pipeline


def render() -> None:
    st.markdown("### Data Explorer — Live Ingestion")
    st.caption("Luồng thật: Vnstock Free API (API key) → Raw JSON → validation/indicators → Curated Parquet → API.")

    with st.form("live_ingestion"):
        ticker_text = st.text_input("Ticker", value="FPT", help="Có thể nhập nhiều mã, phân cách bằng dấu phẩy.")
        col_start, col_end, col_interval = st.columns([1, 1, 0.7])
        start_date = col_start.date_input("Từ ngày", value=date.today() - timedelta(days=90))
        end_date = col_end.date_input("Đến ngày", value=date.today())
        interval = col_interval.selectbox("Interval", ["1D"])
        submitted = st.form_submit_button("Chạy ingestion thật", type="primary", width="stretch")

    if submitted:
        tickers = list(dict.fromkeys(item.strip().upper() for item in ticker_text.split(",") if item.strip()))
        if not tickers:
            st.error("Cần ít nhất một ticker.")
        elif start_date > end_date:
            st.error("Từ ngày phải nhỏ hơn hoặc bằng đến ngày.")
        else:
            with st.spinner("Đang gọi Vnstock Free API, ghi Raw và cập nhật Curated..."):
                try:
                    result = run_pipeline(tickers, start_date.isoformat(), end_date.isoformat(), interval)
                    st.session_state["last_pipeline_result"] = result
                    st.cache_data.clear()
                except ApiClientError as error:
                    st.error(str(error))

    result = st.session_state.get("last_pipeline_result")
    if not result:
        st.info("Docker Compose đã bootstrap dữ liệu mẫu. Form trên chỉ chạy khi bạn muốn lấy dữ liệu mới từ nguồn thật.")
        return

    ingestion = result["ingestion"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Requested", ingestion["requested"])
    col2.metric("Passed", ingestion["passed"])
    col3.metric("Failed", ingestion["failed"])
    st.caption(f"Raw file: {ingestion['raw_path']}")
    st.dataframe(pd.DataFrame(ingestion["details"]), width="stretch", hide_index=True)

    successful = [item["ticker"] for item in ingestion["details"] if item["status"] == "PASS"]
    if successful:
        selected = st.selectbox("Preview dữ liệu qua consumption API", successful)
        try:
            preview = pd.DataFrame(get_prices(
                selected, 
                start_date.isoformat(), 
                end_date.isoformat(), 
                limit=10000
            )["data"])
            
            if preview.empty:
                st.info("Không có dữ liệu cho khoảng thời gian này.")
            else:
                rows_per_page = 15 # Số dòng mỗi trang
                total_rows = len(preview)
                total_pages = math.ceil(total_rows / rows_per_page)

                if "explorer_page" not in st.session_state:
                    st.session_state.explorer_page = 1

                # Reset lại trang về 1 nếu thay đổi Ticker làm số trang bị hụt
                if st.session_state.explorer_page > total_pages:
                    st.session_state.explorer_page = 1

                col_prev, col_page_info, col_next = st.columns([1, 2, 1])
                
                with col_prev:
                    if st.button("⬅️ Trang trước") and st.session_state.explorer_page > 1:
                        st.session_state.explorer_page -= 1
                        
                with col_page_info:
                    st.write(f"Trang {st.session_state.explorer_page} / {total_pages} (Tổng: {total_rows} dòng)")
                    
                with col_next:
                    if st.button("Trang tiếp ➡️") and st.session_state.explorer_page < total_pages:
                        st.session_state.explorer_page += 1

                # Cắt dataframe theo trang
                start_idx = (st.session_state.explorer_page - 1) * rows_per_page
                end_idx = start_idx + rows_per_page
                paged_preview = preview.iloc[start_idx:end_idx]
                
                # Hiển thị bảng dữ liệu đã phân trang
                st.dataframe(paged_preview, width="stretch", hide_index=True)

        except ApiClientError as error:
            st.error(str(error))