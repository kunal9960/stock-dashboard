import json
import pandas as pd
import streamlit as st
import plotly.io as pio
import plotly.graph_objects as go
from itertools import islice
from datetime import datetime
from plotly.subplots import make_subplots
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Page Config
icon = "favicon.png"
st.set_page_config(page_title="Stock Dashboard", page_icon=icon, layout="wide")
st.html("styles.html")
pio.templates.default = "plotly_white"

def batched(iterable, n_cols):
    if n_cols < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n_cols)):
        yield batch

@st.cache_data
def _read_service_account_secret():
    return json.loads(st.secrets["textkey"])

@st.cache_resource
def connect_to_gsheets():
    s_acc = _read_service_account_secret()
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(s_acc, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1fD_vCTgPPWJp-aDDIT00-6Sxq5x6dBOYmRA9D3vfk1A")
    return spreadsheet

@st.cache_data
def download_data(_spreadsheet):
    ticker_sheet = _spreadsheet.worksheet("ticker")
    tickers = pd.DataFrame(ticker_sheet.get_all_records())

    history_dfs = {}
    for ticker in tickers["ticker"]:
        try:
            sheet = _spreadsheet.worksheet(ticker)
            df = pd.DataFrame(sheet.get_all_records())
            history_dfs[ticker] = df
        except:
            st.warning(f"Worksheet for ticker '{ticker}' not found.")
    
    return tickers, history_dfs

@st.cache_data
def transform_data(ticker_df, history_dfs):
    ticker_df["last_trade_time"] = pd.to_datetime(
        ticker_df["last_trade_time"],
        infer_datetime_format=True,
        errors='coerce'
    )

    for col in [
        "last_price", "previous_day_price", "change", "change_pct", "volume", "volume_avg", "shares",
        "day_high", "day_low", "market_cap", "p_e_ratio", "eps",
    ]:
        ticker_df[col] = pd.to_numeric(ticker_df[col], errors='coerce')

    for ticker in list(ticker_df["ticker"]):
        history_dfs[ticker]["date"] = pd.to_datetime(
            history_dfs[ticker]["date"],
            infer_datetime_format=True,
            errors='coerce'
        )
        for col in ["open", "high", "low", "close", "volume"]:
            history_dfs[ticker][col] = pd.to_numeric(history_dfs[ticker][col], errors='coerce')

    ticker_to_open = [list(history_dfs[t]["open"]) for t in list(ticker_df["ticker"])]
    ticker_df["open"] = ticker_to_open

    return ticker_df, history_dfs

def plot_sparkline(data):
    fig_spark = go.Figure(
        data=go.Scatter(
            y=data,
            mode="lines",
            fill="tozeroy",
            line_color="#6abfb7",
            fillcolor="#d6edeb",
        ),
    )
    fig_spark.update_traces(hovertemplate="Price: $ %{y:.2f}")
    fig_spark.update_xaxes(visible=False, fixedrange=True)
    fig_spark.update_yaxes(visible=False, fixedrange=True)
    fig_spark.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        height=50,
        margin=dict(t=10, l=0, b=3, r=2, pad=0),
    )
    return fig_spark

def display_watchlist_card(ticker, symbol_name, last_price, change_pct, open):
    with st.container(border=True):
        st.html(f'<span class="watchlist_card"></span>')
        tl, tr = st.columns([1, 1])
        bl, br = st.columns([0.8, 1.3])

        with tl:
            st.html(f'<span class="watchlist_symbol_name"></span>')
            st.markdown(f"{symbol_name}")

        with tr:
            st.html(f'<span class="watchlist_ticker"></span>')
            st.markdown(f"{ticker}")
            negative_gradient = float(change_pct) < 0
            st.markdown(
                f":{'red' if negative_gradient else 'green'}[{'▼' if negative_gradient else '▲'} {change_pct} %]"
            )

        with bl:
            st.html(f'<span class="watchlist_price_label"></span>')
            st.markdown("Current Value")
            st.html(f'<span class="watchlist_price_value"></span>')
            st.markdown(f"${last_price:.2f}")

        with br:
            fig_spark = plot_sparkline(open)
            st.plotly_chart(fig_spark, config=dict(displayModeBar=False), use_container_width=True)

def display_watchlist(ticker_df):
    n_cols = 4
    for row in batched(ticker_df.itertuples(), n_cols):
        cols = st.columns(n_cols)
        for col, ticker in zip(cols, row):
            if ticker:
                with col:
                    display_watchlist_card(
                        ticker.ticker,
                        ticker.symbol_name,
                        ticker.last_price,
                        ticker.change_pct,
                        ticker.open
                    )

@st.experimental_fragment
def display_symbol_history(ticker_df, history_dfs):
    st.write("<h2><b>🚀 <u>Period Performance Analysis</b></h2>", unsafe_allow_html=True)
    left_widget, right_widget, _ = st.columns([1, 1, 1.5])

    selected_ticker = left_widget.selectbox("📰 Currently Showing", list(history_dfs.keys()))
    selected_period = right_widget.selectbox("⏱️ Period", ("Week", "Month", "Trimester", "Year"), 2)

    history_df = history_dfs[selected_ticker].set_index("date")

    mapping_period = {
        "Week": 7,
        "Month": 31,
        "Trimester": 90,
        "Year": 365
    }

    today = datetime.today().date()
    delay_days = mapping_period[selected_period]
    history_df = history_df[(today - pd.Timedelta(delay_days, unit="d")):today]

    f_candle = plot_candlestick(history_df)
    left_chart, right_indicator = st.columns([2, 1.5])

    with left_chart:
        st.plotly_chart(f_candle, use_container_width=True)

    with right_indicator:
        st.write("<h2 style='font-weight: bold;'>Period Metrics</h2>", unsafe_allow_html=True)
        l, r = st.columns(2)
        with l:
            st.metric("Lowest Volume Day Trade", f'{history_df["volume"].min():,}')
            st.metric("Lowest Close Price", f'{history_df["close"].min():,} $')
        with r:
            st.metric("Highest Volume Day Trade", f'{history_df["volume"].max():,}')
            st.metric("Highest Close Price", f'{history_df["close"].max():,} $')
        st.metric("Average Daily Volume", f'{int(history_df["volume"].mean()):,}')
        st.metric(
            "Current Market Cap",
            "{:,} $".format(
                ticker_df[ticker_df["ticker"] == selected_ticker]["market_cap"].values[0]
            )
        )

    st.dataframe(history_df)

def plot_candlestick(history_df):
    f_candle = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.1)
    f_candle.add_trace(
        go.Candlestick(
            x=history_df.index,
            open=history_df["open"],
            high=history_df["high"],
            low=history_df["low"],
            close=history_df["close"],
            name="Dollars",
        ), row=1, col=1
    )
    f_candle.add_trace(
        go.Bar(
            x=history_df.index,
            y=history_df["volume"],
            name="Volume Traded"
        ), row=2, col=1
    )
    f_candle.update_layout(
        title="Stock Price Trends",
        showlegend=True,
        xaxis_rangeslider_visible=False,
        yaxis1=dict(title="OHLC"),
        yaxis2=dict(title="Volume"),
        hovermode="x",
        font_size=20,
        margin=dict(l=0, r=0, t=80, b=98, pad=0),
        height=520,
    )
    return f_candle

def display_overview(ticker_df):
    def format_currency(val): return "$ {:,.2f}".format(val)
    def format_percentage(val): return "{:,.2f} %".format(val)
    def format_change(val): return "color: red;" if (val < 0) else "color: green;"
    def apply_odd_row_class(row): return ["background-color: #f8f8f8" if row.name % 2 != 0 else "" for _ in row]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.write("<h2><b>💼 <u>Stock Preview</b></h2>", unsafe_allow_html=True)
        st.write("<i>This data is extracted from :blue[📄 Google Sheets] using a :green[🐍 Python] script via a Service Account.</i>", unsafe_allow_html=True)
    with col2:
        st.image("stock-body.gif", width=130)

    styled_df = (
        ticker_df.style
        .format({"last_price": format_currency, "change_pct": format_percentage})
        .apply(apply_odd_row_class, axis=1)
        .map(format_change, subset=["change_pct"])
    )

    st.dataframe(
        styled_df,
        column_order=[col for col in ticker_df.columns if not col.startswith("_airbyte")],
        column_config={
            "open": st.column_config.AreaChartColumn(
                "Last 12 Months",
                width="large",
                help="Open Price for the last 12 Months",
            ),
        },
        hide_index=True,
        height=250,
        use_container_width=True,
    )

# Main Execution
col1, col2 = st.columns([1, 2])
with col1:
    st.write("<h2><b>📈 <u>Stock Dashboard</b></h2>", unsafe_allow_html=True)
    st.write("<i>A stock dashboard that provides real-time data, performance charts, and key financial metrics for understanding the financial behaviour of companies.</i>", unsafe_allow_html=True)
with col2:
    st.image("stock-header.gif", width=155)

gsheets_connection = connect_to_gsheets()
ticker_df, history_dfs = download_data(gsheets_connection)
ticker_df, history_dfs = transform_data(ticker_df, history_dfs)
display_watchlist(ticker_df)
st.divider()
display_symbol_history(ticker_df, history_dfs)
st.divider()
display_overview(ticker_df)

st.markdown(
    "[![GitHub Badge](https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=fff&style=flat)](https://github.com/kunal9960/stocks-dashboard)&nbsp;&nbsp;" +
    "[![Streamlit Badge](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=fff&style=flat)](https://stock-dashboard-kunal.streamlit.app/)"
)

# Footer
ft = """
<style>
a:link , a:visited{ color: #BFBFBF; background-color: transparent; text-decoration: none; }
a:hover, a:active { color: #0283C3; background-color: transparent; text-decoration: underline; }
footer{ visibility:hidden; }
.footer { position: relative; left: 0; top:150px; bottom: 0; width: 100%; background-color: transparent; color: #808080; text-align: left; }
</style>
<div class="footer">
<p style='font-size: 1em;'>Made with <a href="https://streamlit.io/" target="_blank">Streamlit</a> with ❤️ <a href="https://github.com/kunal9960" target="_blank"> by Kunal</a> © 2025</p>
</div>
"""
st.write(ft, unsafe_allow_html=True)
