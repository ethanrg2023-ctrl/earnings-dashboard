# =====================================================
# 📦 IMPORTS
# =====================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from PIL import Image
import yfinance as yf
from datetime import datetime

# =====================================================
# ⚙️ CONFIG
# =====================================================
st.set_page_config(page_title="Prop SMC Engine", layout="wide")
st.title("🏦 Prop Firm SMC Execution Engine")

# =====================================================
# 📊 DATA
# =====================================================
def get_ohlc(ticker, period="5d", interval="15m"):
    df = yf.download(ticker, period=period, interval=interval)
    return df.dropna()

# =====================================================
# 🧠 SMC ENGINE (BOS / CHoCH)
# =====================================================
def smc_engine(df):
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

    if len(structure) > 2:
        if structure[-1] == "BOS_UP" and structure[-2] == "BOS_DOWN":
            trend = "Reversal Bullish"
        elif structure[-1] == "BOS_DOWN" and structure[-2] == "BOS_UP":
            trend = "Reversal Bearish"

    return {"trend": trend, "structure": structure}

# =====================================================
# 🧱 SUPPORT / RESISTANCE
# =====================================================
def support_resistance(df):
    highs = df["High"].values
    lows = df["Low"].values

    res, sup = [], []

    for i in range(3, len(df)-3):
        if highs[i] == max(highs[i-3:i+3]):
            res.append(highs[i])
        if lows[i] == min(lows[i-3:i+3]):
            sup.append(lows[i])

    return {
        "resistance": sorted(set(res))[-5:],
        "support": sorted(set(sup))[:5]
    }

# =====================================================
# 🟦 FVG ENGINE
# =====================================================
def detect_fvg(df):
    highs = df["High"].values
    lows = df["Low"].values

    bull, bear = [], []

    for i in range(2, len(df)):
        if lows[i] > highs[i-2]:
            bull.append((highs[i-2], lows[i]))
        if highs[i] < lows[i-2]:
            bear.append((lows[i-2], highs[i]))

    return {
        "bullish_fvg": bull[-5:],
        "bearish_fvg": bear[-5:]
    }

# =====================================================
# 🎯 AUTO ENTRY ENGINE
# =====================================================
def auto_entry(df, smc, sr):
    last = df["Close"].iloc[-1]

    signal = "NO TRADE"
    entry = stop = target = None

    if smc["trend"] in ["Bullish", "Reversal Bullish"]:
        if sr["support"]:
            signal = "BUY"
            entry = last
            stop = sr["support"][-1]
            target = sr["resistance"][-1] if sr["resistance"] else last * 1.02

    elif smc["trend"] in ["Bearish", "Reversal Bearish"]:
        if sr["resistance"]:
            signal = "SELL"
            entry = last
            stop = sr["resistance"][-1]
            target = sr["support"][-1] if sr["support"] else last * 0.98

    return {
        "signal": signal,
        "entry": entry,
        "stop": stop,
        "target": target
    }

# =====================================================
# 🧠 WIN PROBABILITY MODEL (IMPORTANT)
# =====================================================
def win_probability(smc, sr, fvg, signal):
    score = 50  # base probability

    # Trend influence
    if smc["trend"] == "Bullish":
        score += 15
    elif smc["trend"] == "Bearish":
        score += 15
    elif "Reversal" in smc["trend"]:
        score += 20
    else:
        score -= 10

    # Structure strength
    if len(smc["structure"]) > 3:
        score += 10

    # Liquidity zones (SR)
    if sr["support"] and sr["resistance"]:
        score += 10

    # FVG inefficiency = institutional edge
    if fvg["bullish_fvg"] or fvg["bearish_fvg"]:
        score += 10

    # Signal alignment
    if signal in ["BUY", "SELL"]:
        score += 10
    else:
        score -= 20

    # Clamp probability
    score = max(5, min(95, score))

    return score

# =====================================================
# 🏷 GRADING ENGINE
# =====================================================
def grade_engine(prob):
    if prob >= 80:
        return "A+ Institutional"
    elif prob >= 70:
        return "A High Quality"
    elif prob >= 60:
        return "B Playable"
    elif prob >= 50:
        return "C Weak"
    else:
        return "F No Trade"

# =====================================================
# 📸 PHOTO ANALYSER
# =====================================================
def analyze_chart(image):
    img = np.array(image.convert("L"))
    h, w = img.shape

    left = img[:, :w//3].mean()
    right = img[:, 2*w//3:].mean()

    trend = "Uptrend" if right > left else "Downtrend"
    bias = "Bullish" if img[2*h//3:].mean() < img[:h//3].mean() else "Bearish"

    return {"visual_trend": trend, "bias": bias}

# =====================================================
# 📊 UI
# =====================================================
asset = st.text_input("Enter Asset (AAPL, TSLA, NVDA)")

if asset:
    df = get_ohlc(asset)

    smc = smc_engine(df)
    sr = support_resistance(df)
    fvg = detect_fvg(df)
    trade = auto_entry(df, smc, sr)

    prob = win_probability(smc, sr, fvg, trade["signal"])
    grade = grade_engine(prob)

    # ======================
    # DASHBOARD
    # ======================
    st.metric("Trend", smc["trend"])
    st.metric("Signal", trade["signal"])
    st.metric("Win Probability", f"{prob:.1f}%")
    st.metric("Grade", grade)

    st.write("Entry:", trade["entry"])
    st.write("Stop:", trade["stop"])
    st.write("Target:", trade["target"])

    # ======================
    # LEVELS
    # ======================
    st.markdown("### Support")
    st.write(sr["support"])

    st.markdown("### Resistance")
    st.write(sr["resistance"])

    st.markdown("### FVG")
    st.write(fvg)

# =====================================================
# 📸 IMAGE ANALYSIS
# =====================================================
st.markdown("### 📸 Chart Analyzer (Optional)")
uploaded = st.file_uploader("Upload Chart", type=["png", "jpg", "jpeg"])

if uploaded:
    img = Image.open(uploaded)
    result = analyze_chart(img)

    st.write("Visual Trend:", result["visual_trend"])
    st.write("Bias:", result["bias"])
