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