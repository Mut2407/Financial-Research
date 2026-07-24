from datetime import date

import pandas as pd
import streamlit as st
import math

from utils.api_client import ApiClientError, get_companies, get_prices
# Bổ sung hàm import vẽ biểu đồ
from utils.plotting import create_financial_plot


@st.cache_data(ttl=30)
def load_companies() -> list[dict]:
    return get_companies(limit=100)["data"]


@st.cache_data(ttl=30)
def load_prices(ticker: str, start_date: str | None, end_date: str | None) -> pd.DataFrame:
    payload = get_prices(ticker, start_date, end_date)
    frame = pd.DataFrame(payload["data"])
    if not frame.empty:
        frame["trading_date"] = pd.to_datetime(frame["trading_date"])
    return frame


def render() -> None:
    st.markdown("### Dashboard — Curated Market Data")
    st.caption("Dữ liệu được đọc từ FastAPI → DuckDB → Curated Parquet; giao diện không sinh mock data.")

    try:
        companies = load_companies()
    except ApiClientError as error:
        st.error(str(error))
        st.info("Hãy kiểm tra backend tại http://localhost:8000/health hoặc chạy `docker compose up --build`.")
        return

    if not companies:
        st.warning("Curated layer đang trống. Hãy chạy bootstrap hoặc ingest dữ liệu trong Data Explorer.")
        return

    labels = {
        f"{company['ticker']} — {company.get('name') or 'N/A'}": company
        for company in companies
    }
    selected_label = st.selectbox("Mã chứng khoán", labels.keys())
    company = labels[selected_label]

    use_filter = st.checkbox("Lọc theo khoảng ngày", value=False)
    start_date: date | None = None
    end_date: date | None = None
    if use_filter:
        col_start, col_end = st.columns(2)
        start_date = col_start.date_input("Từ ngày", value=date(2025, 1, 1))
        end_date = col_end.date_input("Đến ngày", value=date.today())
        if start_date > end_date:
            st.error("Từ ngày phải nhỏ hơn hoặc bằng đến ngày.")
            return

    try:
        frame = load_prices(
            company["ticker"],
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
        )
    except ApiClientError as error:
        st.error(str(error))
        return

    if frame.empty:
        st.info("Không có dữ liệu trong khoảng đã chọn.")
        return

    latest = frame.iloc[-1]
    previous_close = frame.iloc[-2]["close_price"] if len(frame) > 1 else latest["close_price"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Close", f"{latest['close_price']:,.2f}", f"{latest['close_price'] - previous_close:+,.2f}")
    col2.metric("Volume", f"{latest['volume']:,.0f}")
    ma20 = latest.get("ma20")
    col3.metric("MA20", "N/A" if pd.isna(ma20) else f"{ma20:,.2f}")
    rsi = latest.get("rsi_14")
    col4.metric("RSI 14", "N/A" if pd.isna(rsi) else f"{rsi:,.2f}")
    
    # Logic tối ưu: Chỉ gọi hàm xử lý và vẽ biểu đồ khi user ấn vào checkbox
    show_plot = st.checkbox("Hiển thị biểu đồ phân tích kỹ thuật", value=False)
    if show_plot:
        figure = create_financial_plot(frame, company["ticker"])
        st.plotly_chart(figure, width="stretch")

    with st.expander("Xem dữ liệu curated"):
            if frame.empty:
                st.info("Không có dữ liệu.")
                return
                
            # Thiết lập số dòng mỗi trang
            rows_per_page = 20 
            total_rows = len(frame)
            total_pages = math.ceil(total_rows / rows_per_page)

            # Quản lý trạng thái trang hiện tại trong Streamlit
            if "current_page" not in st.session_state:
                st.session_state.current_page = 1

            # Các nút điều hướng phân trang
            col_prev, col_page_info, col_next = st.columns([1, 2, 1])
            
            with col_prev:
                if st.button("⬅️ Trang trước") and st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    
            with col_page_info:
                st.write(f"Trang {st.session_state.current_page} / {total_pages} (Tổng: {total_rows} dòng)")
                
            with col_next:
                if st.button("Trang tiếp ➡️") and st.session_state.current_page < total_pages:
                    st.session_state.current_page += 1

            # Cắt dataframe theo trang hiện tại
            start_idx = (st.session_state.current_page - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            
            # Hiển thị dữ liệu đã được cắt
            paged_frame = frame.iloc[start_idx:end_idx]
            st.dataframe(paged_frame, width="stretch", hide_index=True)