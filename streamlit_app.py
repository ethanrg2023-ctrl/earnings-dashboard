import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Trading Dashboard", layout="wide")

WATCHLIST = ["CAR", "TSLA", "NVDA", "AAPL", "GC=F", "SI=F", "^AXJO", "BHP.AX"]

st.title("📊 Earnings Momentum Dashboard")


# -------------------------
# CACHE DATA (IMPORTANT)
# -------------------------
@st.cache_data(ttl=300)
def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d", interval="5m")
        return hist
    except:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_earnings(ticker):
    try:
        stock = yf.Ticker(ticker)
        cal = stock.calendar
        if cal is None or cal.empty:
            return None, None

        eps_est = None
        eps_actual = None

        if "EPS Estimate" in cal.index:
            eps_est = cal.loc["EPS Estimate"][0]

        if "Reported EPS" in cal.index:
            eps_actual = cal.loc["Reported EPS"][0]

        return eps_est, eps_actual

    except:
        return None, None


# -------------------------
# HELPERS
# -------------------------
def price_change(hist):
    if hist is None or hist.empty or len(hist) < 2:
        return 0

    start = hist["Close"].iloc[0]
    end = hist["Close"].iloc[-1]

    if start == 0:
        return 0

    return ((end - start) / start) * 100


def impact_score(move):
    if abs(move) > 5:
        return 2
    elif abs(move) > 2:
        return 1
    return 0


# -------------------------
# BUILD DATA (ONLY ONCE)
# -------------------------
rows = []

for ticker in WATCHLIST:
    hist = get_data(ticker)
    eps_est, eps_actual = get_earnings(ticker)
    move = price_change(hist)

    surprise = None
    if eps_est is not None and eps_actual is not None:
        surprise = eps_actual - eps_est

    rows.append({
        "Ticker": ticker,
        "Move %": round(move, 2),
        "EPS Est": eps_est,
        "EPS Actual": eps_actual,
        "Surprise": surprise,
        "Impact Score": impact_score(move)
    })


df = pd.DataFrame(rows)


# -------------------------
# SIGNALS
# -------------------------
st.subheader("🚨 Opportunity Signals")

for row in rows:
    if row["Move %"] > 5:
        st.success(f"{row['Ticker']} - STRONG MOMENTUM MOVE")
    elif row["Move %"] < -3:
        st.error(f"{row['Ticker']} - SELL PRESSURE")


# -------------------------
# TABLE
# -------------------------
st.subheader("📋 Market Overview")
st.dataframe(df, use_container_width=True)


# -------------------------
# CHART
# -------------------------
st.subheader("📈 Chart")
selected = st.selectbox("Choose stock", WATCHLIST)

hist = get_data(selected)

if hist is not None and not hist.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Close"))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data available for this ticker")


# -------------------------
# FINAL SIGNALS
# -------------------------
st.markdown("### 🚨 Earnings + Momentum Signals")

for row in rows:
    if row["Surprise"] is not None and row["Move %"] > 2:
        st.success(f"{row['Ticker']} - Earnings surprise + momentum")
