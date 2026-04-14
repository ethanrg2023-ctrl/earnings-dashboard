import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from PIL import Image

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="SMC Trading System", layout="wide")
st.title("🏦 Institutional SMC Trading System (Fixed)")

# =====================================================
# SESSION STATE (TRADE JOURNAL RESTORED)
# =====================================================
if "trades" not in st.session_state:
    st.session_state.trades = []

# =====================================================
# DATA
# =====================================================
def get_ohlc(ticker):
    df = yf.download(ticker, period="5d", interval="15m", progress=False)
    if df is None or df.empty:
        return pd.DataFrame()
    return df.dropna()

# =====================================================
# SMC ENGINE
# =====================================================
def smc_engine(df):
    if df.empty:
        return {"trend": "No Data", "structure": []}

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

    if len(structure) >= 2:
        if structure[-1] == "BOS_UP" and structure[-2] == "BOS_DOWN":
            trend = "Reversal Bullish"
        elif structure[-1] == "BOS_DOWN" and structure[-2] == "BOS_UP":
            trend = "Reversal Bearish"

    return {"trend": trend, "structure": structure}

# =====================================================
# SUPPORT / RESISTANCE
# =====================================================
def support_resistance(df):
    if df.empty:
        return {"support": [], "resistance": []}

    highs = df["High"].values
    lows = df["Low"].values

    res, sup = [], []

    for i in range(3, len(df)-3):
        if highs[i] == np.max(highs[i-3:i+3]):
            res.append(highs[i])
        if lows[i] == np.min(lows[i-3:i+3]):
            sup.append(lows[i])

    return {
        "resistance": sorted(set(res))[-5:],
        "support": sorted(set(sup))[:5]
    }

# =====================================================
# FVG
# =====================================================
def detect_fvg(df):
    if df.empty:
        return {"bullish_fvg": [], "bearish_fvg": []}

    highs = df["High"].values
    lows = df["Low"].values

    bull, bear = [], []

    for i in range(2, len(df)):
        if lows[i] > highs[i-2]:
            bull.append((highs[i-2], lows[i]))
        if highs[i] < lows[i-2]:
            bear.append((lows[i-2], highs[i]))

    return {"bullish_fvg": bull[-5:], "bearish_fvg": bear[-5:]}

# =====================================================
# AUTO ENTRY
# =====================================================
def auto_entry(df, smc, sr):
    if df.empty:
        return {"signal": "NO DATA", "entry": None, "stop": None, "target": None}

    last = df["Close"].iloc[-1]

    if smc["trend"] in ["Bullish", "Reversal Bullish"] and sr["support"]:
        return {
            "signal": "BUY",
            "entry": float(last),
            "stop": float(sr["support"][-1]),
            "target": float(sr["resistance"][-1]) if sr["resistance"] else float(last*1.02)
        }

    if smc["trend"] in ["Bearish", "Reversal Bearish"] and sr["resistance"]:
        return {
            "signal": "SELL",
            "entry": float(last),
            "stop": float(sr["resistance"][-1]),
            "target": float(sr["support"][-1]) if sr["support"] else float(last*0.98)
        }

    return {"signal": "NO TRADE", "entry": None, "stop": None, "target": None}

# =====================================================
# WIN PROBABILITY
# =====================================================
def win_probability(smc, sr, fvg, signal):
    score = 50

    if "Bullish" in smc["trend"]:
        score += 15
    elif "Bearish" in smc["trend"]:
        score += 15

    if sr["support"] and sr["resistance"]:
        score += 10

    if fvg["bullish_fvg"] or fvg["bearish_fvg"]:
        score += 10

    if signal in ["BUY", "SELL"]:
        score += 10
    else:
        score -= 15

    return max(5, min(95, score))

# =====================================================
# GRADING
# =====================================================
def grade(prob):
    if prob >= 80:
        return "A+"
    elif prob >= 70:
        return "A"
    elif prob >= 60:
        return "B"
    elif prob >= 50:
        return "C"
    return "F"

# =====================================================
# 📒 TRADE JOURNAL (RESTORED PROPERLY)
# =====================================================
st.sidebar.header("📒 Trade Journal")

t_ticker = st.sidebar.text_input("Ticker")
buy = st.sidebar.number_input("Buy", 0.0)
sell = st.sidebar.number_input("Sell", 0.0)
qty = st.sidebar.number_input("Qty", 1)
date = st.sidebar.date_input("Date")

if st.sidebar.button("Add Trade"):
    pnl = (sell - buy) * qty if buy > 0 else 0

    st.session_state.trades.append({
        "Date": date,
        "Ticker": t_ticker,
        "Buy": buy,
        "Sell": sell,
        "Qty": qty,
        "PnL": pnl
    })

# =====================================================
# TRADE TABLE + PnL
# =====================================================
df_trades = pd.DataFrame(st.session_state.trades)

st.markdown("## 📊 Trade Performance")

if not df_trades.empty:
    df_trades["Cumulative"] = df_trades["PnL"].cumsum()

    st.metric("Total PnL", f"${df_trades['PnL'].sum():.2f}")
    st.metric("Win Rate", f"{(df_trades['PnL'] > 0).mean()*100:.1f}%")

    st.dataframe(df_trades)

# =====================================================
# MARKET ENGINE
# =====================================================
asset = st.text_input("Enter Asset (AAPL, TSLA, NVDA)")

if asset:
    df = get_ohlc(asset)

    if df.empty:
        st.error("No market data found.")
        st.stop()

    smc = smc_engine(df)
    sr = support_resistance(df)
    fvg = detect_fvg(df)
    trade = auto_entry(df, smc, sr)

    prob = win_probability(smc, sr, fvg, trade["signal"])
    g = grade(prob)

    # =====================
    # OUTPUT
    # =====================
    st.metric("Trend", smc["trend"])
    st.metric("Signal", trade["signal"])
    st.metric("Win Probability", f"{prob:.1f}%")
    st.metric("Grade", g)

    st.write("Entry:", trade["entry"])
    st.write("Stop:", trade["stop"])
    st.write("Target:", trade["target"])
