import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
from PIL import Image
import yfinance as yf

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="Institutional SMC Engine", layout="wide")
st.markdown("<h1 style='text-align:center;'>🏦 Institutional SMC Trading Engine</h1>", unsafe_allow_html=True)

# =====================================================
# STATE
# =====================================================
if "trades" not in st.session_state:
    st.session_state.trades = []

# =====================================================
# TRADE LOG
# =====================================================
st.sidebar.header("➕ Trade Entry")

ticker = st.sidebar.text_input("Ticker")
buy = st.sidebar.number_input("Buy Price", min_value=0.0)
sell = st.sidebar.number_input("Sell Price", min_value=0.0)
qty = st.sidebar.number_input("Quantity", min_value=1)
date = st.sidebar.date_input("Date", value=datetime.today())
strategy = st.sidebar.selectbox("Strategy", ["SMC", "Breakout", "Momentum", "Reversal"])
notes = st.sidebar.text_area("Notes")

if st.sidebar.button("Add Trade"):
    pnl = (sell - buy) * qty if buy > 0 else 0
    pnl_pct = ((sell - buy) / buy) * 100 if buy > 0 else 0

    st.session_state.trades.append({
        "Date": pd.to_datetime(date),
        "Ticker": ticker.upper(),
        "Strategy": strategy,
        "Buy": buy,
        "Sell": sell,
        "Qty": qty,
        "PnL": pnl,
        "PnL %": pnl_pct,
        "Notes": notes
    })

# =====================================================
# DATA
# =====================================================
df_trades = pd.DataFrame(st.session_state.trades)

st.markdown("### 📌 Portfolio Overview")

if not df_trades.empty:
    df_trades = df_trades.sort_values("Date")
    df_trades["Cumulative"] = df_trades["PnL"].cumsum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total PnL", f"${df_trades['PnL'].sum():,.2f}")
    c2.metric("Win Rate", f"{(df_trades['PnL'] > 0).mean()*100:.1f}%")
    c3.metric("Best", f"${df_trades['PnL'].max():,.2f}")
    c4.metric("Worst", f"${df_trades['PnL'].min():,.2f}")
    c5.metric("Avg", f"${df_trades['PnL'].mean():,.2f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_trades["Date"], y=df_trades["Cumulative"]))
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df_trades.sort_values("Date", ascending=False))
else:
    st.warning("No trades yet.")

# =====================================================
# OHLC DATA
# =====================================================
def get_ohlc(ticker, period="5d", interval="15m"):
    df = yf.download(ticker, period=period, interval=interval)
    return df.dropna()

# =====================================================
# SMC ENGINE (BOS / CHoCH)
# =====================================================
def smc_engine(df):
    highs = df["High"].values
    lows = df["Low"].values
    closes = df["Close"].values

    structure = []
    trend = "Range"

    last_high = highs[0]
    last_low = lows[0]

    for i in range(1, len(df)):
        if closes[i] > last_high:
            structure.append("BOS_UP")
            trend = "Bullish"
            last_high = highs[i]

        elif closes[i] < last_low:
            structure.append("BOS_DOWN")
            trend = "Bearish"
            last_low = lows[i]

    # CHoCH detection
    if len(structure) > 2:
        if structure[-1] == "BOS_UP" and structure[-2] == "BOS_DOWN":
            trend = "Reversal Bullish"
        elif structure[-1] == "BOS_DOWN" and structure[-2] == "BOS_UP":
            trend = "Reversal Bearish"

    return {
        "trend": trend,
        "structure": structure
    }

# =====================================================
# SUPPORT / RESISTANCE
# =====================================================
def support_resistance(df):
    highs = df["High"].values
    lows = df["Low"].values

    res = []
    sup = []

    for i in range(3, len(df)-3):
        if highs[i] == max(highs[i-3:i+3]):
            res.append(highs[i])
        if lows[i] == min(lows[i-3:i+3]):
            sup.append(lows[i])

    return {
        "resistance": sorted(set(res))[-5:],
        "support": sorted(set(sup))[:5]
    }

# =====================================================
# FVG ENGINE
# =====================================================
def detect_fvg(df):
    highs = df["High"].values
    lows = df["Low"].values

    bull = []
    bear = []

    for i in range(2, len(df)):
        if lows[i] > highs[i-2]:
            bull.append((highs[i-2], lows[i]))
        if highs[i] < lows[i-2]:
            bear.append((lows[i-2], highs[i]))

    return {
        "bullish_fvg": bull[-5:],
        "bearish_fvg": bear[-5:]
    }

# =====================================================
# AUTO ENTRY ENGINE
# =====================================================
def auto_entry(df, smc, sr):
    last = df["Close"].iloc[-1]

    signal = "NO TRADE"
    entry = stop = target = None
    risk = "HIGH"

    if smc["trend"] in ["Bullish", "Reversal Bullish"]:
        if sr["support"]:
            entry = last
            stop = sr["support"][-1]
            target = sr["resistance"][-1] if sr["resistance"] else None
            signal = "BUY"
            risk = "1-2%"

    elif smc["trend"] in ["Bearish", "Reversal Bearish"]:
        if sr["resistance"]:
            entry = last
            stop = sr["resistance"][-1]
            target = sr["support"][-1] if sr["support"] else None
            signal = "SELL"
            risk = "1-2%"

    return {
        "signal": signal,
        "entry": entry,
        "stop": stop,
        "target": target,
        "risk": risk
    }

# =====================================================
# INSTITUTIONAL TRADING ENGINE UI
# =====================================================
st.markdown("### 🏦 Institutional SMC Engine")

asset = st.text_input("Enter Asset (e.g. AAPL, TSLA, NVDA)")

if asset:
    df = get_ohlc(asset)

    smc = smc_engine(df)
    sr = support_resistance(df)
    fvg = detect_fvg(df)
    trade = auto_entry(df, smc, sr)

    st.metric("Market Trend", smc["trend"])
    st.metric("Signal", trade["signal"])

    st.write("Entry:", trade["entry"])
    st.write("Stop:", trade["stop"])
    st.write("Target:", trade["target"])
    st.write("Risk:", trade["risk"])

    st.markdown("### 🧱 Resistance")
    st.write(sr["resistance"])

    st.markdown("### 🧱 Support")
    st.write(sr["support"])

    st.markdown("### 🟦 Bullish FVG")
    st.write(fvg["bullish_fvg"])

    st.markdown("### 🟥 Bearish FVG")
    st.write(fvg["bearish_fvg"])

    st.markdown("### 📉 Structure")
    st.write(smc["structure"][-10:])

# =====================================================
# RESET
# =====================================================
if st.button("Reset Portfolio"):
    st.session_state.trades = []
    st.rerun()
