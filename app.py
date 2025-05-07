import streamlit as st
import pandas as pd
import requests
import datetime

API_KEY = "07bb08a784544873933da48c47693995"

portfolio = [
    {"name": "IAM Gold", "symbol": "IAG"},
    {"name": "NVIDIA", "symbol": "NVDA"},
    {"name": "Rheinmetall", "symbol": "RHM.DE"},
    {"name": "Bitcoin", "symbol": "BTC/USD"}
]

def lade_daten(symbol):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&outputsize=100&apikey={API_KEY}"
        r = requests.get(url)
        if r.status_code != 200 or "values" not in r.json():
            return None
        df = pd.DataFrame(r.json()["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df = df.sort_index()
        df["close"] = pd.to_numeric(df["close"])
        return df
    except:
        return None

def get_rsi(data, window=14):
    delta = data.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def get_macd(data):
    short = data.ewm(span=12, adjust=False).mean()
    long = data.ewm(span=26, adjust=False).mean()
    macd = short - long
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def get_trend(data):
    recent = data[-3:]
    if recent.is_monotonic_increasing:
        return "aufwärts"
    elif recent.is_monotonic_decreasing:
        return "abwärts"
    else:
        return "seitwärts"

def entscheidung(rsi, macd, signal, trend):
    if rsi <= 30 and macd > signal and trend == "aufwärts":
        return "KAUFEN"
    elif rsi >= 70 and macd < signal and trend == "abwärts":
        return "VERKAUFEN"
    elif 40 <= rsi <= 60 and abs(macd - signal) < 0.2:
        return "BEOBACHTEN"
    else:
        return "HALTEN"

st.set_page_config(page_title="Tagesanalyse", layout="centered")
st.title("📊 Tagesaktuelle Aktien-Empfehlung")

heute = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
st.caption(f"Letzte Aktualisierung: {heute}")

data = []

for aktie in portfolio:
    df = lade_daten(aktie["symbol"])
    if df is None or df.empty:
        data.append([aktie["name"], "-", "-", "-", "Fehler"])
        continue

    close = df["close"]
    kurs = close.iloc[-1]
    rsi = get_rsi(close).iloc[-1]
    macd, signal = get_macd(close)
    macd_val, signal_val = macd.iloc[-1], signal.iloc[-1]
    trend = get_trend(close)
    handlung = entscheidung(rsi, macd_val, signal_val, trend)

    data.append([
        aktie["name"], f"{kurs:.1f}", f"{rsi:.1f}", trend, handlung
    ])

df_result = pd.DataFrame(data, columns=["Name", "Kurs", "RSI", "Trend", "Handlung"])

st.dataframe(df_result.style.applymap(
    lambda v: "background-color: lightgreen" if v == "KAUFEN" else
              "background-color: lightcoral" if v == "VERKAUFEN" else
              "background-color: khaki" if v == "BEOBACHTEN" else
              "background-color: lightgray" if v == "HALTEN" else "",
    subset=["Handlung"]
), use_container_width=True)

st.markdown("""
---
Diese Empfehlungen basieren auf RSI, MACD und Trenddaten (TwelveData).
""")
