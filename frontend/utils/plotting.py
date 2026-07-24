import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_financial_plot(frame: pd.DataFrame, ticker: str) -> go.Figure:
    """
    Hàm tạo biểu đồ nến và volume cho mã chứng khoán.
    """
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
    return figure

def create_business_result_chart(frame: pd.DataFrame, ticker: str) -> go.Figure:
    """
    Hàm tạo biểu đồ Kết quả kinh doanh (Doanh thu, Lợi nhuận, Tăng trưởng) với nền trắng mặc định.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Cột 1: Doanh thu
    fig.add_trace(
        go.Bar(
            x=frame['period'], 
            y=frame['revenue'], 
            name="Doanh thu (tỷ)", 
            marker_color="#e56b6f" 
        ),
        secondary_y=False,
    )
    
    # Cột 2: Lợi nhuận
    fig.add_trace(
        go.Bar(
            x=frame['period'], 
            y=frame['profit'], 
            name="Lợi nhuận (tỷ)", 
            marker_color="#7a9e9f" 
        ),
        secondary_y=False,
    )
    
    # Đường dây: Tăng trưởng LNST
    fig.add_trace(
        go.Scatter(
            x=frame['period'], 
            y=frame['growth'], 
            name="Tăng trưởng LNST (%)", 
            mode="lines+markers+text",
            # Dùng màu vàng cam (amber) để có độ tương phản tốt hơn trên nền trắng
            marker=dict(color="#f59e0b", size=6), 
            line=dict(color="#f59e0b", width=2),
            text=frame['growth'].apply(lambda x: f"{x:.2f} %" if pd.notnull(x) else ""), 
            textposition="top center", 
            textfont=dict(color="#0f172a", size=11, weight="bold") # Chữ màu đậm
        ),
        secondary_y=True,
    )
    
    # Tùy chỉnh Layout Nền Trắng
    fig.update_layout(
        template="plotly_white", # Sử dụng theme trắng mặc định của Plotly
        barmode='group',
        font=dict(color="#0f172a"), # Đổi font chữ toàn biểu đồ sang màu tối
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=-0.2, 
            xanchor="center", 
            x=0.5
        ),
        margin={"l": 40, "r": 40, "t": 40, "b": 20},
        hovermode="x unified"
    )
    
    # Cập nhật màu lưới (grid) nhạt hơn cho nền trắng
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", zerolinecolor="#cbd5e1", secondary_y=False)
    fig.update_yaxes(showgrid=False, zeroline=False, secondary_y=True)
    
    return fig