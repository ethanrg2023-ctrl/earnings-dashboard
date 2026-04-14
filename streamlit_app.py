import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from PIL import Image
import numpy as np

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Alpha Trading Desk", layout="wide")

st.markdown("<h1 style='text-align:center;'>📊 Alpha Trading Desk</h1>", unsafe_allow_html=True)

# -------------------------
# STATE
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
    if buy > 0:
        pnl = (sell - buy) * qty
        pnl_pct = ((sell - buy) / buy) * 100
    else:
        pnl = 0
        pnl_pct = 0

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

if not df.empty:
    df = df.sort_values("Date")
    df["Cumulative"] = df["PnL"].cumsum()

    total_pnl = df["PnL"].sum()
    win_rate = (df["PnL"] > 0).mean() * 100
    best = df["PnL"].max()
    worst = df["PnL"].min()
    avg = df["PnL"].mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total PnL", f"${total_pnl:,.2f}")
    c2.metric("Win Rate", f"{win_rate:.1f}%")
    c3.metric("Best", f"${best:,.2f}")
    c4.metric("Worst", f"${worst:,.2f}")
    c5.metric("Avg", f"${avg:,.2f}")

    # Equity curve
    st.markdown("### 📈 Equity Curve")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Cumulative"], name="Equity"))
    fig.update_layout(template="plotly_dark", height=400)

    st.plotly_chart(fig, use_container_width=True)

    # Table
    st.markdown("### 🧾 Trade Log")
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)

else:
    st.warning("No trades yet.")

# -------------------------
# 📸 SCREENSHOT ANALYSIS (NO CV2)
# -------------------------
st.markdown("### 📸 Chart Analysis")

uploaded = st.file_uploader("Upload chart image", type=["png", "jpg", "jpeg"])


def analyze_chart(image):
    import numpy as np

    img = np.array(image.convert("L"))
    h, w = img.shape

    # -------------------------
    # TREND (STRUCTURE BASED)
    # -------------------------
    thirds = np.array_split(img, 3, axis=1)
    means = [t.mean() for t in thirds]

    if means[2] > means[1] > means[0]:
        trend = "Uptrend"
    elif means[2] < means[1] < means[0]:
        trend = "Downtrend"
    else:
        trend = "Sideways"

    # -------------------------
    # VOLATILITY
    # -------------------------
    vol_score = img.std()
    volatility = "High" if vol_score > 50 else "Low"

    # -------------------------
    # CANDLE STRUCTURE (REAL LOGIC)
    # -------------------------
    top = img[:h//3].mean()
    mid = img[h//3:2*h//3].mean()
    bot = img[2*h//3:].mean()

    body_strength = abs(mid - (top + bot) / 2)
    wick_upper = abs(top - mid)
    wick_lower = abs(bot - mid)

    # Detect candle type
    if body_strength < 3:
        candle = "Doji"
        meaning = "Indecision — market has no clear direction"

    elif wick_lower > wick_upper * 1.5:
        candle = "Bullish Pin Bar"
        meaning = "Buyers rejected lower prices (support holding)"

    elif wick_upper > wick_lower * 1.5:
        candle = "Bearish Pin Bar"
        meaning = "Sellers rejected higher prices (resistance holding)"

    elif mid > top and mid > bot:
        candle = "Strong Bullish Candle"
        meaning = "Aggressive buying — continuation likely"

    elif mid < top and mid < bot:
        candle = "Strong Bearish Candle"
        meaning = "Aggressive selling — downside likely"

    else:
        candle = "Mixed Candle"
        meaning = "No clear edge"

    # -------------------------
    # DECISION ENGINE
    # -------------------------
    if trend == "Uptrend" and "Bullish" in candle and volatility == "High":
        setup = "Trend Continuation"
        entry = "Buy pullback / breakout"
        stop = "Below recent low"
        target = "Next resistance"
        risk = "Medium"
        grade = "A"

    elif trend == "Uptrend" and "Pin Bar" in candle:
        setup = "Pullback Reversal"
        entry = "Buy near support"
        stop = "Below wick"
        target = "Trend continuation"
        risk = "Low"
        grade = "A"

    elif trend == "Downtrend" and "Bearish" in candle:
        setup = "Short Continuation"
        entry = "Sell rally"
        stop = "Above recent high"
        target = "Next support"
        risk = "Medium"
        grade = "A"

    elif candle == "Doji":
        setup = "No Trade"
        entry = "Wait for confirmation"
        stop = "-"
        target = "-"
        risk = "High"
        grade = "F"

    else:
        setup = "Weak Setup"
        entry = "Reduce size"
        stop = "Tight stop"
        target = "Small move"
        risk = "High"
        grade = "C"

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
# -------------------------
# ⚡ SCANNER
# -------------------------
st.markdown("### ⚡ Trade Scanner")

c1, c2, c3 = st.columns(3)

move = c1.slider("Price Change %", -10.0, 10.0, 0.0)
range_pct = c2.slider("Range %", 0.0, 10.0, 0.0)
volume = c3.checkbox("Volume Spike")


def scan(move, rng, vol):
    if move > 3 and rng > 2 and vol:
        return "🔥 Breakout"
    elif move > 2:
        return "📈 Momentum"
    elif move < -3:
        return "⚠️ Sell Pressure"
    return "No Setup"


st.info(scan(move, range_pct, volume))

# -------------------------
# EXPORT + RESET
# -------------------------
if not df.empty:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📤 Export CSV", csv, "trades.csv")

if st.button("Reset Portfolio"):
    st.session_state.trades = []
    st.rerun()
