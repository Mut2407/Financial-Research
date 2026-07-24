import pandas as pd
import streamlit as st

# Chỉ import get_companies, loại bỏ get_financial_reports bị lỗi
from utils.api_client import get_companies, ApiClientError
from utils.plotting import create_business_result_chart

def get_mock_financial_reports(ticker: str, period: str) -> dict:
    """
    Dữ liệu Mock giả lập Báo cáo tài chính để test UI/UX.
    Đã điều chỉnh các con số để khớp 100% với bản thiết kế.
    """
    if period == "quarter":
        data = [
            {"period": "Q1/2025", "revenue": 200, "profit": 15, "growth": 1597.92},
            {"period": "Q2/2025", "revenue": 280, "profit": -5, "growth": -134.50},
            {"period": "Q3/2025", "revenue": 240, "profit": -2, "growth": -98.75},
            {"period": "Q4/2025", "revenue": 110, "profit": -15, "growth": -316.08},
            {"period": "Q1/2026", "revenue": 190, "profit": 5, "growth": -81.23}
        ]
    else:
        # Giả lập thêm dữ liệu theo năm để test nút chuyển đổi
        data = [
            {"period": "2023", "revenue": 850, "profit": 120, "growth": 45.5},
            {"period": "2024", "revenue": 920, "profit": 150, "growth": 25.0},
            {"period": "2025", "revenue": 830, "profit": -7, "growth": -104.6},
        ]
    
    return {"data": data}

def render() -> None:
    # Header chia cột để đặt nút Quý / Năm
    col_title, col_toggle = st.columns([3, 1])
    with col_title:
        st.markdown("### Kết quả kinh doanh — UI/UX Mockup")
        st.caption("Giao diện đang sử dụng Mock Data để review thiết kế trong khi chờ Backend hoàn thiện API.")
    with col_toggle:
        period_type = st.radio("Chế độ xem:", ["Quý", "Năm"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("---")

    # ==========================================
    # 1. LẤY DANH SÁCH MÃ TỪ DATABASE 
    # ==========================================
    try:
        companies_payload = get_companies(limit=100)
        available_tickers = [comp["ticker"] for comp in companies_payload.get("data", [])]
    except ApiClientError as e:
        st.error("Không thể kết nối đến Backend để tải danh sách mã chứng khoán.")
        st.code(str(e))
        return

    if not available_tickers:
        st.info("Hệ thống hiện chưa có dữ liệu công ty nào. Vui lòng sang tab 'Data Explorer' chạy Ingestion trước.")
        return

    # Dropdown danh sách mã
    selected_ticker = st.selectbox("Chọn mã chứng khoán để xem báo cáo:", available_tickers)
    period_param = "quarter" if period_type == "Quý" else "year"

    # ==========================================
    # 2. RENDER BIỂU ĐỒ BẰNG MOCK DATA
    # ==========================================
    with st.spinner(f"Đang tải giao diện báo cáo tài chính cho {selected_ticker}..."):
        payload = get_mock_financial_reports(selected_ticker, period_param)
        
        if not payload or not payload.get("data"):
            st.info(f"Không tìm thấy dữ liệu báo cáo cho mã {selected_ticker}.")
        else:
            df_reports = pd.DataFrame(payload["data"])
            
            # Vẽ biểu đồ
            fig = create_business_result_chart(df_reports, selected_ticker)
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Xem bảng số liệu chi tiết"):
                st.dataframe(df_reports, use_container_width=True, hide_index=True)