from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils.api_client import ApiClientError, get_companies, get_prices


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


def _render_chart(frame: pd.DataFrame, ticker: str) -> None:
    colors = frame.apply(
        lambda row: "#089981" if row["close_price"] >= row["open_price"] else "#F23645",
        axis=1,
    )
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.78, 0.22],
    )
    figure.add_trace(
        go.Candlestick(
            x=frame["trading_date"],
            open=frame["open_price"],
            high=frame["high_price"],
            low=frame["low_price"],
            close=frame["close_price"],
            name=ticker,
            increasing_line_color="#089981",
            decreasing_line_color="#F23645",
        ),
        row=1,
        col=1,
    )
    if "ma20" in frame:
        figure.add_trace(
            go.Scatter(x=frame["trading_date"], y=frame["ma20"], name="MA20", line={"color": "#2563eb"}),
            row=1,
            col=1,
        )
    figure.add_trace(
        go.Bar(x=frame["trading_date"], y=frame["volume"], marker_color=colors, name="Volume"),
        row=2,
        col=1,
    )
    figure.update_layout(
        template="plotly_white",
        height=620,
        margin={"l": 10, "r": 10, "t": 35, "b": 10},
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
    )
    st.plotly_chart(figure, width="stretch")


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
    _render_chart(frame, company["ticker"])

    with st.expander("Xem dữ liệu curated"):
        st.dataframe(frame, width="stretch", hide_index=True)
