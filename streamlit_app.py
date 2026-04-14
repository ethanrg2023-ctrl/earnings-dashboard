import streamlit as st
import pandas as pd

st.set_page_config(page_title="Trading Tracker", layout="wide")

st.title("📊 Personal Trading Tracker")

# -------------------------
# SESSION STORAGE
# -------------------------
if "trades" not in st.session_state:
    st.session_state.trades = []


# -------------------------
# ADD TRADE FORM
# -------------------------
st.subheader("➕ Add Trade")

with st.form("trade_form"):
    ticker = st.text_input("Ticker (e.g. TSLA)")
    buy_price = st.number_input("Buy Price", min_value=0.0)
    sell_price = st.number_input("Sell Price", min_value=0.0)
    quantity = st.number_input("Quantity", min_value=1, step=1)
    notes = st.text_area("Notes")

    submitted = st.form_submit_button("Add Trade")

    if submitted:
        pnl = (sell_price - buy_price) * quantity
        pnl_pct = ((sell_price - buy_price) / buy_price) * 100 if buy_price > 0 else 0

        st.session_state.trades.append({
            "Ticker": ticker,
            "Buy Price": buy_price,
            "Sell Price": sell_price,
            "Quantity": quantity,
            "PnL $": pnl,
            "PnL %": pnl_pct,
            "Notes": notes
        })

        st.success("Trade added!")


# -------------------------
# DATAFRAME
# -------------------------
st.subheader("📋 Trade History")

df = pd.DataFrame(st.session_state.trades)

if df.empty:
    st.warning("No trades yet.")
else:
    st.dataframe(df, use_container_width=True)

    # -------------------------
    # PERFORMANCE METRICS
    # -------------------------
    st.subheader("📈 Performance Summary")

    total_pnl = df["PnL $"].sum()
    win_rate = (df["PnL $"] > 0).mean() * 100
    avg_win = df[df["PnL $"] > 0]["PnL $"].mean()
    avg_loss = df[df["PnL $"] < 0]["PnL $"].mean()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total PnL", f"${total_pnl:.2f}")
    col2.metric("Win Rate", f"{win_rate:.1f}%")
    col3.metric("Avg Win", f"${avg_win:.2f}" if pd.notna(avg_win) else "N/A")
    col4.metric("Avg Loss", f"${avg_loss:.2f}" if pd.notna(avg_loss) else "N/A")


# -------------------------
# RESET BUTTON
# -------------------------
st.subheader("⚠️ Reset")

if st.button("Clear All Trades"):
    st.session_state.trades = []
    st.experimental_rerun()
