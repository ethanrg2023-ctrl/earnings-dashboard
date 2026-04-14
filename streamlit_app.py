# =====================================================
# 📦 IMPORTS
# =====================================================
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from PIL import Image

# =====================================================
# ⚙️ CONFIG
# =====================================================
st.set_page_config(page_title="SMC Engine PRO", layout="wide")
st.title("🏦 Institutional SMC Execution Engine (Stable Version)")

# =====================================================
# 🧠 SAFE DATA LOADER (NO CRASHES)
# =====================================================
def get_ohlc(ticker, period="5d", interval="15m"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)

        if df is None or df.empty:
            return pd.DataFrame()

        required = {"Open", "High", "Low", "Close"}
        if not required.issubset(df.columns):
            return pd.DataFrame()

        df = df.dropna()
        return df

    except Exception:
        return pd.DataFrame()

# =====================================================
# 🧠 SMC ENGINE (BOS / CHoCH SAFE)
# =====================================================
def smc_engine(df):
    if df.empty or len(df) < 5:
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
# 🧱 SUPPORT / RESISTANCE (NO EMPTY CRASH)
# =====================================================
def support_resistance(df):
    if df.empty or len(df) < 10:
        return {"support": [], "resistance": []}

    highs = df["High"].values
    lows = df["Low"].values

    res = []
    sup = []

    window = 3

    for i in range(window, len(df) - window):
        local_high = highs[i-window:i+window]
        local_low = lows[i-window:i+window]

        if highs[i] == np.max(local_high):
            res.append(float(highs[i]))

        if lows[i] == np.min(local_low):
            sup.append(float(lows[i]))

    res = sorted(list(set(res)))
    sup = sorted(list(set(sup)))

    return {
        "resistance": res[-5:] if res else [],
        "support": sup[:5] if sup else []
    }

# =====================================================
# 🟦 FVG ENGINE (SAFE)
# =====================================================
def detect_fvg(df):
    if df.empty or len(df) < 3:
        return {"bullish_fvg": [], "bearish_fvg": []}

    highs = df["High"].values
    lows = df["Low"].values

    bull, bear = [], []

    for i in range(2, len(df)):
        try:
            if lows[i] > highs[i-2]:
                bull.append((float(highs[i-2]), float(lows[i])))

            if highs[i] < lows[i-2]:
                bear.append((float(lows[i-2]), float(highs[i])))
        except:
            continue

    return {
        "bullish_fvg": bull[-5:],
        "bearish_fvg": bear[-5:]
    }

# =====================================================
# 🎯 AUTO ENTRY ENGINE (SAFE)
# =====================================================
def auto_entry(df, smc, sr):
    if df.empty:
        return {"signal": "NO DATA", "entry": None, "stop": None, "target": None}

    last = df["Close"].iloc[-1]

    signal = "NO TRADE"
    entry = stop = target = None

    if smc["trend"] in ["Bullish", "Reversal Bullish"] and sr["support"]:
        signal = "BUY"
        entry = float(last)
        stop = float(sr["support"][-1])
        target = float(sr["resistance"][-1]) if sr["resistance"] else float(last * 1.02)

    elif smc["trend"] in ["Bearish", "Reversal Bearish"] and sr["resistance"]:
        signal = "SELL"
        entry = float(last)
        stop = float(sr["resistance"][-1])
        target = float(sr["support"][-1]) if sr["support"] else float(last * 0.98)

    return {
        "signal": signal,
        "entry": entry,
        "stop": stop,
        "target": target
    }

# =====================================================
# 🧠 WIN PROBABILITY (SAFE)
# =====================================================
def win_probability(smc, sr, fvg, signal):
    score = 50

    if smc["trend"] == "Bullish":
        score += 15
    elif smc["trend"] == "Bearish":
        score += 15
    elif "Reversal" in smc["trend"]:
        score += 20
    else:
        score -= 10

    if sr["support"] and sr["resistance"]:
        score += 10

    if fvg["bullish_fvg"] or fvg["bearish_fvg"]:
        score += 10

    if signal in ["BUY", "SELL"]:
        score += 10
    else:
        score -= 20

    return max(5, min(95, score))

# =====================================================
# 🏷 GRADING ENGINE
# =====================================================
def grade(prob):
    if prob >= 80:
        return "A+ Institutional"
    elif prob >= 70:
        return "A Quality"
    elif prob >= 60:
        return "B Setup"
    elif prob >= 50:
        return "C Weak"
    else:
        return "F No Trade"

# =====================================================
# 📸 IMAGE ANALYSER (SAFE)
# =====================================================
def analyze_chart(image):
    img = np.array(image.convert("L"))

    if img.size == 0:
        return {"trend": "No Data", "bias": "None"}

    h, w = img.shape

    left = img[:, :max(1, w//3)].mean()
    right = img[:, 2*max(1, w//3):].mean()

    trend = "Uptrend" if right > left else "Downtrend"
    bias = "Bullish" if img[2*h//3:].mean() < img[:h//3].mean() else "Bearish"

    return {"visual_trend": trend, "bias": bias}

# =====================================================
# 📊 UI
# =====================================================
asset = st.text_input("Enter Asset (AAPL, TSLA, NVDA)")

if asset:
    df = get_ohlc(asset)

    if df.empty:
        st.error("No data found. Try another ticker.")
        st.stop()

    smc = smc_engine(df)
    sr = support_resistance(df)
    fvg = detect_fvg(df)
    trade = auto_entry(df, smc, sr)

    prob = win_probability(smc, sr, fvg, trade["signal"])
    grade = grade(prob)

    st.metric("Trend", smc["trend"])
    st.metric("Signal", trade["signal"])
    st.metric("Win Probability", f"{prob:.1f}%")
    st.metric("Grade", grade)

    st.write("Entry:", trade["entry"])
    st.write("Stop:", trade["stop"])
    st.write("Target:", trade["target"])

    st.markdown("### Support")
    st.write(sr["support"])

    st.markdown("### Resistance")
    st.write(sr["resistance"])

    st.markdown("### FVG")
    st.write(fvg)

# =====================================================
# 📸 IMAGE ANALYSIS
# =====================================================
st.markdown("### 📸 Chart Analyzer")

uploaded = st.file_uploader("Upload Chart", type=["png", "jpg", "jpeg"])

if uploaded:
    img = Image.open(uploaded)
    result = analyze_chart(img)

    st.write("Visual Trend:", result["visual_trend"])
    st.write("Bias:", result["bias"])
