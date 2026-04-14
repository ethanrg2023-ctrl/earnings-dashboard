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
