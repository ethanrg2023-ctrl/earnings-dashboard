import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from PIL import Image
import numpy as np

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Alpha Pro Trading Engine", layout="wide")
st.markdown("<h1 style='text-align:center;'>📊 Alpha PRO Trading Engine</h1>", unsafe_allow_html=True)

# -------------------------
# STATE
# -------------------------
if "trades" not in st.session_state:
    st.session_state.trades = []

# -------------------------
# TRADE ENTRY
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

    st.sidebar.success("Trade added")

df = pd.DataFrame(st.session_state.trades)

# -------------------------
# PORTFOLIO
# -------------------------
st.markdown("### 📌 Portfolio Overview")

if not df.empty:
    df = df.sort_values("Date")
    df["Cumulative"] = df["PnL"].cumsum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total PnL", f"${df['PnL'].sum():,.2f}")
    c2.metric("Win Rate", f"{(df['PnL'] > 0).mean()*100:.1f}%")
    c3.metric("Best", f"${df['PnL'].max():,.2f}")
    c4.metric("Worst", f"${df['PnL'].min():,.2f}")
    c5.metric("Avg", f"${df['PnL'].mean():,.2f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Cumulative"], name="Equity"))
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)
else:
    st.warning("No trades yet.")

# -------------------------
# 📸 PRO CHART ANALYSER
# -------------------------
st.markdown("### 📸 Pro Chart Analysis Engine")

uploaded = st.file_uploader("Upload chart image", type=["png", "jpg", "jpeg"])


def analyze_chart(image):
    img = np.array(image.convert("L"))
    h, w = img.shape

    # -------------------------
    # TREND SCORE (0–100)
    # -------------------------
    left = img[:, :w//3].mean()
    mid = img[:, w//3:2*w//3].mean()
    right = img[:, 2*w//3:].mean()

    trend_score = (right - left)

    if trend_score > 5:
        trend = "Uptrend"
    elif trend_score < -5:
        trend = "Downtrend"
    else:
        trend = "Sideways"

    # -------------------------
    # VOLATILITY
    # -------------------------
    vol = img.std()
    volatility = "High" if vol > 55 else "Low"

    # -------------------------
    # CANDLE STRUCTURE MODEL
    # -------------------------
    top = img[:h//3].mean()
    mid_zone = img[h//3:2*h//3].mean()
    bot = img[2*h//3:].mean()

    body = abs(mid_zone - (top + bot) / 2)
    upper_wick = abs(top - mid_zone)
    lower_wick = abs(bot - mid_zone)

    # Candle classification
    if body < 3:
        candle = "Doji"
        meaning = "Market indecision"

    elif lower_wick > upper_wick * 1.7:
        candle = "Bullish Rejection Wick"
        meaning = "Buyers defended support"

    elif upper_wick > lower_wick * 1.7:
        candle = "Bearish Rejection Wick"
        meaning = "Sellers defended resistance"

    elif mid_zone > top and mid_zone > bot:
        candle = "Strong Bullish Pressure"
        meaning = "Aggressive buyers"

    elif mid_zone < top and mid_zone < bot:
        candle = "Strong Bearish Pressure"
        meaning = "Aggressive sellers"

    else:
        candle = "Neutral Candle"
        meaning = "No edge"

    # -------------------------
    # PRO DECISION ENGINE (A+ → F)
    # -------------------------
    score = 0

    if trend == "Uptrend":
        score += 2
    if "Bullish" in candle:
        score += 2
    if volatility == "High":
        score += 1
    if "Rejection" in candle:
        score += 2

    if score >= 6:
        grade = "A+"
        setup = "High Probability Continuation"
        entry = "Buy breakout or pullback"
        stop = "Below structure low"
        target = "Next resistance"
        risk = "Medium"

    elif score == 5:
        grade = "A"
        setup = "Strong Setup"
        entry = "Buy confirmation candle"
        stop = "Tight below wick"
        target = "Trend continuation"
        risk = "Low"

    elif score == 4:
        grade = "B"
        setup = "Playable Setup"
        entry = "Small position entry"
        stop = "Tight stop"
        target = "Scalp move"
        risk = "Medium"

    elif score == 3:
        grade = "C"
        setup = "Weak Setup"
        entry = "Optional trade"
        stop = "Strict stop"
        target = "Small move"
        risk = "High"

    else:
        grade = "F"
        setup = "No Trade Zone"
        entry = "Stay out"
        stop = "-"
        target = "-"
        risk = "High"

    return {
        "trend": trend,
        "volatility": volatility,
        "candle": candle,
        "meaning": meaning,
        "setup": setup,
        "entry": entry,
        "stop": stop,
        "target": target,
        "risk": risk,
        "grade": grade
    }


# -------------------------
# SAFE EXECUTION
# -------------------------
if uploaded is not None:
    img = Image.open(uploaded)
    result = analyze_chart(img)

    st.markdown("### 🧠 AI Trading Analysis")

    c1, c2, c3 = st.columns(3)
    c1.metric("Trend", result["trend"])
    c2.metric("Volatility", result["volatility"])
    c3.metric("Grade", result["grade"])

    st.markdown("### 🕯️ Candle Insight")
    st.info(f"{result['candle']} → {result['meaning']}")

    st.markdown("### 🎯 Trade Plan")
    st.success(f"Entry: {result['entry']}")
    st.warning(f"Stop: {result['stop']}")
    st.error(f"Target: {result['target']}")

    st.markdown("### ⚠️ Risk")
    st.write(result["risk"])

    st.markdown("### 📊 Setup")
    st.write(result["setup"])
else:
    st.info("Upload a chart image to generate pro analysis.")

# -------------------------
# SCANNER
# -------------------------
st.markdown("### ⚡ Trade Scanner")

c1, c2, c3 = st.columns(3)

move = c1.slider("Price Change %", -10.0, 10.0, 0.0)
rng = c2.slider("Range %", 0.0, 10.0, 0.0)
vol = c3.checkbox("Volume Spike")

def scan(move, rng, vol):
    if move > 3 and rng > 2 and vol:
        return "🔥 Breakout"
    elif move > 2:
        return "📈 Momentum"
    elif move < -3:
        return "⚠️ Sell Pressure"
    return "No Setup"

st.info(scan(move, rng, vol))

# -------------------------
# EXPORT / RESET
# -------------------------
if not df.empty:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📤 Export CSV", csv, "trades.csv")

if st.button("Reset Portfolio"):
    st.session_state.trades = []
    st.rerun()
