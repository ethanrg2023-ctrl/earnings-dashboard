import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime

st.set_page_config(page_title="Fund Dashboard", layout="wide")

st.markdown("""
    <h1 style='text-align: center; color: white;'>
    📊 Alpha Trading Desk
    </h1>
""", unsafe_allow_html=True)


# -------------------------
# SESSION STATE
# -------------------------
if "trades" not in st.session_state:
    st.session_state.trades = []


# -------------------------
# SIDEBAR - INPUT
# -------------------------
st.sidebar.header("➕ New Trade Entry")

ticker = st.sidebar.text_input("Ticker")
buy = st.sidebar.number_input("Buy Price", min_value=0.0)
sell = st.sidebar.number_input("Sell Price", min_value=0.0)
qty = st.sidebar.number_input("Quantity", min_value=1, step=1)
date = st.sidebar.date_input("Date", value=datetime.today())
notes = st.sidebar.text_area("Notes")

if st.sidebar.button("Add Trade"):
    pnl = (sell - buy) * qty
    pnl_pct = ((sell - buy) / buy) * 100 if buy > 0 else 0

    st.session_state.trades.append({
        "Date": date,
        "Ticker": ticker.upper(),
        "Buy": buy,
        "Sell": sell,
        "Qty": qty,
        "PnL": pnl,
        "PnL %": pnl_pct,
        "Notes": notes
    })

    st.sidebar.success("Trade added")


# -------------------------
# DATAFRAME
# -------------------------
df = pd.DataFrame(st.session_state.trades)

# -------------------------
# KPI ROW (HEDGE FUND STYLE)
# -------------------------
st.markdown("### 📌 Portfolio Overview")

if df.empty:
    st.warning("No trades recorded yet.")
    st.stop()

total_pnl = df["PnL"].sum()
win_rate = (df["PnL"] > 0).mean() * 100
best_trade = df["PnL"].max()
worst_trade = df["PnL"].min()
avg_trade = df["PnL"].mean()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total PnL", f"${total_pnl:,.2f}")
col2.metric("Win Rate", f"{win_rate:.1f}%")
col3.metric("Best Trade", f"${best_trade:,.2f}")
col4.metric("Worst Trade", f"${worst_trade:,.2f}")
col5.metric("Avg Trade", f"${avg_trade:,.2f}")


# -------------------------
# EQUITY CURVE
# -------------------------
st.markdown("### 📈 Equity Curve")

df_sorted = df.sort_values("Date")
df_sorted["Cumulative PnL"] = df_sorted["PnL"].cumsum()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_sorted["Date"],
    y=df_sorted["Cumulative PnL"],
    mode="lines",
    name="Equity Curve"
))

fig.update_layout(
    height=400,
    template="plotly_dark",
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)


# -------------------------
# TRADE TABLE (CLEAN LOOK)
# -------------------------
st.markdown("### 🧾 Trade Book")

styled_df = df.copy()
styled_df = styled_df.sort_values("Date", ascending=False)

st.dataframe(
    styled_df,
    use_container_width=True,
    height=300
)


# -------------------------
# PERFORMANCE BY TICKER
# -------------------------
st.markdown("### 🎯 Performance by Asset")

ticker_perf = df.groupby("Ticker")["PnL"].sum().sort_values()

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=ticker_perf.index,
    y=ticker_perf.values
))

fig2.update_layout(
    height=400,
    template="plotly_dark",
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig2, use_container_width=True)


# -------------------------
# RESET
# -------------------------
st.markdown("### ⚠️ Risk Control")

if st.button("Reset Portfolio"):
    st.session_state.trades = []
    st.rerun()
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from PIL import Image
import numpy as np
import cv2

st.set_page_config(page_title="Alpha Desk AI", layout="wide")

st.title("🧠 Alpha Trading Desk AI (Offline)")

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
    pnl = (sell - buy) * qty
    pnl_pct = ((sell - buy) / buy) * 100 if buy > 0 else 0

    st.session_state.trades.append({
        "Date": pd.to_datetime(date),
        "Ticker": ticker,
        "Strategy": strategy,
        "PnL": pnl,
        "PnL %": pnl_pct
    })

# -------------------------
# DATAFRAME + METRICS
# -------------------------
df = pd.DataFrame(st.session_state.trades)

if not df.empty:
    df = df.sort_values("Date")
    df["Cumulative"] = df["PnL"].cumsum()

    st.subheader("📊 Performance")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total PnL", f"${df['PnL'].sum():.2f}")
    col2.metric("Win Rate", f"{(df['PnL']>0).mean()*100:.1f}%")
    col3.metric("Trades", len(df))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Cumulative"]))
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 📸 SCREENSHOT ANALYZER
# -------------------------
st.subheader("📸 Chart Screenshot Analysis")

uploaded_file = st.file_uploader("Upload chart image", type=["png", "jpg", "jpeg"])

def analyze_chart(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Edge detection = volatility proxy
    edges = cv2.Canny(gray, 50, 150)
    edge_density = edges.mean()

    # Brightness trend proxy
    h, w = gray.shape
    left = gray[:, :w//2].mean()
    right = gray[:, w//2:].mean()

    if right > left:
        trend = "Uptrend"
    elif right < left:
        trend = "Downtrend"
    else:
        trend = "Sideways"

    # Volatility classification
    if edge_density > 20:
        volatility = "High (Sharp Moves)"
    else:
        volatility = "Low"

    # Strategy suggestion
    if trend == "Uptrend" and volatility == "High (Sharp Moves)":
        setup = "Momentum / Breakout"
        entry = "Buy pullbacks"
        exit = "Trail stop below recent lows"

    elif trend == "Downtrend":
        setup = "Short / Sell Rallies"
        entry = "Enter on weak bounce"
        exit = "Cover near support"

    else:
        setup = "No Trade / Chop"
        entry = "Wait for breakout"
        exit = "N/A"

    return trend, volatility, setup, entry, exit

def analyze_chart(image):
    import numpy as np
    import cv2

    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape

    # -------------------------
    # TREND DETECTION
    # -------------------------
    left = gray[:, :w//2].mean()
    right = gray[:, w//2:].mean()

    if right > left + 5:
        trend = "Uptrend"
    elif right < left - 5:
        trend = "Downtrend"
    else:
        trend = "Sideways"

    # -------------------------
    # VOLATILITY (EDGE DENSITY)
    # -------------------------
    edges = cv2.Canny(gray, 50, 150)
    edge_density = edges.mean()

    if edge_density > 25:
        volatility = "High"
    else:
        volatility = "Low"

    # -------------------------
    # CANDLE "STRUCTURE" SIMULATION
    # -------------------------
    top = gray[:h//3, :].mean()
    middle = gray[h//3:2*h//3, :].mean()
    bottom = gray[2*h//3:, :].mean()

    # Interpret candle type
    if abs(top - bottom) < 5:
        candle = "Doji (Indecision)"
        meaning = "Market undecided — avoid entries"

    elif bottom < middle < top:
        candle = "Bullish Candle"
        meaning = "Buy pressure — continuation likely"

    elif top < middle < bottom:
        candle = "Bearish Candle"
        meaning = "Sell pressure — downside risk"

    elif top > middle and bottom > middle:
        candle = "Long Wick (Rejection)"
        meaning = "Reversal signal — strong rejection"

    else:
        candle = "Mixed Structure"
        meaning = "No clear edge"

    # -------------------------
    # STRATEGY LOGIC
    # -------------------------
    if trend == "Uptrend" and candle == "Bullish Candle" and volatility == "High":
        setup = "Momentum Breakout"
        entry = "Enter on small pullback"
        exit = "Trail below higher lows"
        grade = "A"

    elif trend == "Uptrend" and candle == "Long Wick (Rejection)":
        setup = "Pullback Buy"
        entry = "Buy near support"
        exit = "Target previous highs"
        grade = "B"

    elif trend == "Downtrend" and candle == "Bearish Candle":
        setup = "Trend Continuation Short"
        entry = "Sell rallies"
        exit = "Cover near support"
        grade = "A"

    elif candle == "Doji (Indecision)":
        setup = "No Trade"
        entry = "Wait"
        exit = "N/A"
        grade = "F"

    else:
        setup = "Low Quality Setup"
        entry = "Avoid or reduce size"
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
    st.image(image, caption="Uploaded Chart", use_container_width=True)

    trend, vol, setup, entry, exit = analyze_chart(image)

    st.markdown("### 🧠 AI Analysis")

    st.write(f"**Trend:** {trend}")
    st.write(f"**Volatility:** {vol}")
    st.write(f"**Detected Setup:** {setup}")

    st.markdown("### 🎯 Trade Plan")
    st.success(f"Entry: {entry}")
    st.error(f"Exit: {exit}")
    if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Chart", use_container_width=True)

    result = analyze_chart(image)

    st.markdown("### 🧠 Market Read")

    col1, col2, col3 = st.columns(3)
    col1.metric("Trend", result["trend"])
    col2.metric("Volatility", result["volatility"])
    col3.metric("Grade", result["grade"])

    st.markdown("### 🕯️ Candle Analysis")
    st.info(f"{result['candle']} — {result['meaning']}")

    st.markdown("### 🎯 Trade Plan")
    st.success(f"Entry: {result['entry']}")
    st.error(f"Exit: {result['exit']}")

    st.markdown("### 📊 Setup")
    st.write(result["setup"])

# -------------------------
# ⚡ MANUAL SCANNER
# -------------------------
st.subheader("⚡ Trade Scanner (Manual Inputs)")

col1, col2, col3 = st.columns(3)

price_move = col1.slider("Price Change %", -10.0, 10.0, 0.0)
range_pct = col2.slider("Candle Range %", 0.0, 10.0, 0.0)
volume_spike = col3.checkbox("Volume Spike")

def scan_logic(move, range_pct, volume):
    if move > 3 and range_pct > 2 and volume:
        return "🔥 Breakout Candidate"

    elif move > 2:
        return "📈 Momentum"

    elif move < -3:
        return "⚠️ Sell Pressure"

    else:
        return "😐 No Setup"

result = scan_logic(price_move, range_pct, volume_spike)

st.markdown("### 📊 Scanner Result")
st.info(result)

# -------------------------
# EXPORT
# -------------------------
if not df.empty:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📤 Export Trades", csv, "trades.csv", "text/csv")
