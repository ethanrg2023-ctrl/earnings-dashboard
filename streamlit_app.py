import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Trading Dashboard", layout="wide")

WATCHLIST = ["CAR", "TSLA", "NVDA", "AAPL", "GOLD", "SILVER", "ASX", "BHP"]

st.title("📊 Earnings Momentum Dashboard")

def get_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="1d", interval="5m")

def get_earnings(ticker):
    stock = yf.Ticker(ticker)
    try:
        cal = stock.calendar
        eps_est = cal.loc["EPS Estimate"][0]
        eps_actual = cal.loc["Reported EPS"][0] if "Reported EPS" in cal.index else None
        return eps_est, eps_actual
    except:
        return None, None
def get_earnings(ticker):
    stock = yf.Ticker(ticker)

    # Better fallback approach
    try:
        info = stock.info

        eps_est = info.get("forwardEps", None)
        eps_actual = info.get("trailingEps", None)

        return eps_est, eps_actual
    except:
        return None, None
def price_change(hist):
    if len(hist) < 2:
        return 0
    return ((hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0]) * 100
def impact_score(move):
    score = 0

    if abs(move) > 5:
        score += 2
    elif abs(move) > 2:
        score += 1

    return score
rows = []
rows.append({
    "Ticker": ticker,
    "Move %": round(move, 2),
    "EPS Est": eps_est,
    "EPS Actual": eps_actual,
    "Impact Score": impact_score(move)
})
st.subheader("🚨 Opportunity Signals")

for row in rows:
    if row["Move %"] > 5 and row["EPS Est"] is not None:
        st.success(f"{row['Ticker']} - STRONG MOMENTUM MOVE")
    elif row["Move %"] < -3:
        st.error(f"{row['Ticker']} - SELL PRESSURE")


for ticker in WATCHLIST:
    hist = get_data(ticker)
    eps_est, eps_actual = get_earnings(ticker)
    move = price_change(hist)

    surprise = None
    if eps_actual and eps_est:
        surprise = eps_actual - eps_est

    rows.append({
        "Ticker": ticker,
        "Move %": round(move, 2),
        "EPS Est": eps_est,
        "EPS Actual": eps_actual,
        "Surprise": surprise
    })

df = pd.DataFrame(rows)

st.subheader("📋 Market Overview")
st.dataframe(df, use_container_width=True)

st.subheader("📈 Chart")
selected = st.selectbox("Choose stock", WATCHLIST)

hist = get_data(selected)

fig = go.Figure()
fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"]))

st.plotly_chart(fig, use_container_width=True)

st.markdown("### 🚨 Signals")
for row in rows:
    if row["Surprise"] and row["Move %"] > 3:
        st.success(f"{row['Ticker']} showing strong momentum")
    elif row["Move %"] < -3:
        st.error(f"{row['Ticker']} dropping hard")
