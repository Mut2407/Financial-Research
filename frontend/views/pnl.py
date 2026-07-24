import pandas as pd
import streamlit as st

from utils.api_client import get_prices, ApiClientError

def get_mock_portfolio() -> pd.DataFrame:
    """Dữ liệu danh mục giả lập để test giao diện PnL."""
    data = [
        {"ticker": "FPT", "quantity": 1500, "average_price": 95.5},
        {"ticker": "VIC", "quantity": 2000, "average_price": 42.0},
        {"ticker": "VNM", "quantity": 800, "average_price": 68.5},
    ]
    return pd.DataFrame(data)

@st.cache_data(ttl=60)
def fetch_latest_price(ticker: str) -> float:
    """Gọi API Backend để lấy giá đóng cửa gần nhất của mã cổ phiếu."""
    try:
        payload = get_prices(ticker, limit=1)
        if payload and payload.get("data"):
            return payload["data"][0]["close_price"]
    except ApiClientError:
        pass
    return 0.0

def render() -> None:
    st.markdown("### 📊 Profit & Loss")
    st.caption("Mô-đun theo dõi hiệu quả danh mục đầu tư. (Đang sử dụng Mock Data để test UI độc lập).")

    portfolio_df = get_mock_portfolio()
    
    if portfolio_df.empty:
        st.info("Danh mục đầu tư đang trống.")
        return

    with st.spinner("Đang đồng bộ giá thị trường mới nhất..."):
        # Lấy giá thị trường hiện tại
        portfolio_df["market_price"] = portfolio_df["ticker"].apply(fetch_latest_price)
        
        # Xử lý các trường hợp chưa cào dữ liệu (giá = 0)
        portfolio_df["market_price"] = portfolio_df["market_price"].replace(0, pd.NA)
        portfolio_df["market_price"] = portfolio_df["market_price"].fillna(portfolio_df["average_price"])

        # Tính toán
        portfolio_df["total_cost"] = portfolio_df["quantity"] * portfolio_df["average_price"]
        portfolio_df["market_value"] = portfolio_df["quantity"] * portfolio_df["market_price"]
        portfolio_df["unrealized_pnl"] = portfolio_df["market_value"] - portfolio_df["total_cost"]
        portfolio_df["pnl_percent"] = (portfolio_df["unrealized_pnl"] / portfolio_df["total_cost"]) * 100

    # --- Hiển thị Tổng quan (Metrics) ---
    total_cost = portfolio_df["total_cost"].sum()
    total_market_value = portfolio_df["market_value"].sum()
    total_pnl = portfolio_df["unrealized_pnl"].sum()
    total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng vốn đầu tư", f"{total_cost:,.0f} ₫")
    col2.metric("Giá trị hiện tại", f"{total_market_value:,.0f} ₫")
    col3.metric("Tổng Lãi/Lỗ", f"{total_pnl:,.0f} ₫", f"{total_pnl_pct:,.2f}%")

    st.markdown("---")
    st.markdown("#### Chi tiết danh mục")
    
    # --- Format bảng dữ liệu ---
    # Sắp xếp lại thứ tự cột cho dễ nhìn
    display_df = portfolio_df[[
        "ticker", "quantity", "average_price", "market_price", 
        "total_cost", "market_value", "unrealized_pnl", "pnl_percent"
    ]].copy()

    # Tô màu xanh/đỏ cho các cột Lãi/Lỗ
    styled_df = display_df.style.format({
        "quantity": "{:,.0f}",
        "average_price": "{:,.2f}",
        "market_price": "{:,.2f}",
        "total_cost": "{:,.0f}",
        "market_value": "{:,.0f}",
        "unrealized_pnl": "{:,.0f}",
        "pnl_percent": "{:,.2f}%"
    }).applymap(
        lambda val: 'color: #089981' if val > 0 else 'color: #F23645' if val < 0 else '', 
        subset=['unrealized_pnl', 'pnl_percent']
    )
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)