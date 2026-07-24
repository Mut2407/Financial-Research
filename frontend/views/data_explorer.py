from datetime import date, timedelta

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
            preview = pd.DataFrame(get_prices(selected, limit=1000)["data"])
            st.dataframe(preview.tail(20), width="stretch", hide_index=True)
        except ApiClientError as error:
            st.error(str(error))
