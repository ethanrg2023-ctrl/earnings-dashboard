import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from PIL import Image
import numpy as np
import cv2

st.set_page_config(page_title="Alpha Trading Desk AI", layout="wide")

st.markdown("<h1 style='text-align:center;'>📊 Alpha Trading Desk AI</h1>", unsafe_allow_html=True)

# -------------------------
# SESSION STATE
# -------------------------
if "trades" not in st.session_state:
    st.session_state.trades = []

# -------------------------
# SIDEBAR - TRADE ENTRY
# -------------------------
st.sidebar.header("➕ Trade Entry")

ticker = st.sidebar.text_input("Ticker")
buy = st.sidebar.number_input("Buy Price", min_value=0.0)
sell = st.sidebar.number_input("Sell Price", min_value=0.0)
qty = st.sidebar.number_input("Quantity", min_value=1)
date = st.sidebar.date_input("Date", value=datetime.today())
strategy = st.sidebar.selectbox("Strategy", ["Breakout", "Momentum", "Reversal", "Scalp"])
notes = st.sidebar.text_area("Notes")

if st.sidebar.button("Add Trade"):
    pnl = (sell - buy) * qty
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

    st.sidebar.success("Trade added")

# -------------------------
# DATA
# -------------------------
df = pd.DataFrame(st.session_state.trades)

st.markdown("### 📌 Portfolio Overview")

if df.empty:
    st.warning("No trades recorded yet.")
else:
    df = df.sort_values("Date")
    df["Cumulative"] = df["PnL"].cumsum()

    total_pnl = df["PnL"].sum()
    win_rate = (df["PnL"] > 0).mean() * 100
    best_trade = df["PnL"].max()
    worst_trade = df["PnL"].min()
    avg_trade = df["PnL"].mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total PnL", f"${total_pnl:,.2f}")
    c2.metric("Win Rate", f"{win_rate:.1f}%")
    c3.metric("Best Trade", f"${best_trade:,.2f}")
    c4.metric("Worst Trade", f"${worst_trade:,.2f}")
    c5.metric("Avg Trade", f"${avg_trade:,.2f}")

    # -------------------------
    # EQUITY CURVE
    # -------------------------
    st.markdown("### 📈 Equity Curve")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Cumulative"], name="Equity"))

    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # TRADE TABLE
    # -------------------------
    st.markdown("### 🧾 Trade Log")
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)

# -------------------------
# 📸 SCREENSHOT ANALYZER
# -------------------------
st.markdown("### 📸 Chart Screenshot Analysis")

uploaded_file = st.file_uploader("Upload chart image", type=["png", "jpg", "jpeg"])

def analyze_chart(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape

    # Trend
    left = gray[:, :w//2].mean()
    right = gray[:, w//2:].mean()

    if right > left + 5:
        trend = "Uptrend"
    elif right < left - 5:
        trend = "Downtrend"
    else:
        trend = "Sideways"

    # Volatility
    edges = cv2.Canny(gray, 50, 150)
    edge_density = edges.mean()
    volatility = "High" if edge_density > 25 else "Low"

    # Candle structure (approx)
    top = gray[:h//3, :].mean()
    mid = gray[h//3:2*h//3, :].mean()
    bot = gray[2*h//3:, :].mean()

    if abs(top - bot) < 5:
        candle = "Doji"
        meaning = "Indecision"
    elif bot < mid < top:
        candle = "Bullish"
        meaning = "Buying pressure"
    elif top < mid < bot:
        candle = "Bearish"
        meaning = "Selling pressure"
    elif top > mid and bot > mid:
        candle = "Rejection Wick"
        meaning = "Potential reversal"
    else:
        candle = "Mixed"
        meaning = "Unclear"

    # Strategy + grading
    if trend == "Uptrend" and candle == "Bullish" and volatility == "High":
        setup = "Momentum Breakout"
        entry = "Buy pullback"
        exit = "Trail stop"
        grade = "A"
    elif trend == "Downtrend" and candle == "Bearish":
        setup = "Short Continuation"
        entry = "Sell rally"
        exit = "Cover support"
        grade = "A"
    elif candle == "Doji":
        setup = "No Trade"
        entry = "Wait"
        exit = "-"
        grade = "F"
    else:
        setup = "Weak Setup"
        entry = "Small size"
        exit = "Tight stop"
        grade = "C"

    return {
        "trend": trend,
        "volatility": volatility,
        "candle": candle,
        "meaning": meaning,
        "setup": setup,
        "entry": entry,
        "exit": exit,
        "grade": grade
    }

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)

    result = analyze_chart(image)

    st.markdown("### 🧠 AI Market Read")

    c1, c2, c3 = st.columns(3)
    c1.metric("Trend", result["trend"])
    c2.metric("Volatility", result["volatility"])
    c3.metric("Grade", result["grade"])

    st.markdown("### 🕯️ Candle")
    st.info(f"{result['candle']} → {result['meaning']}")

    st.markdown("### 🎯 Trade Plan")
    st.success(f"Entry: {result['entry']}")
    st.error(f"Exit: {result['exit']}")

    st.write("Setup:", result["setup"])

# -------------------------
# ⚡ SCANNER
# -------------------------
st.markdown("### ⚡ Trade Scanner")

c1, c2, c3 = st.columns(3)

move = c1.slider("Price Change %", -10.0, 10.0, 0.0)
range_pct = c2.slider("Candle Range %", 0.0, 10.0, 0.0)
volume = c3.checkbox("Volume Spike")

def scan_logic(move, range_pct, volume):
    if move > 3 and range_pct > 2 and volume:
        return "🔥 Breakout"
    elif move > 2:
        return "📈 Momentum"
    elif move < -3:
        return "⚠️ Sell Pressure"
    return "No Setup"

st.info(scan_logic(move, range_pct, volume))

# -------------------------
# EXPORT / RESET
# -------------------------
if not df.empty:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📤 Export CSV", csv, "trades.csv")

if st.button("Reset Portfolio"):
    st.session_state.trades = []
    st.rerun()
