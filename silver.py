import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import yfinance as yf
import plotly.graph_objs as go

# Constants
ALPHA_VANTAGE_KEY = 'R2320825J5JPXB20'
NEWS_API_KEY = '631261860bce4da7b7b6e34ff07513bb'
YOUR_TWELVE_DATA_API_KEY = 'de40701eaa3c4cdbb963c11ddf2862d7'

# Function to fetch silver price from Yahoo Finance
def get_silver_price_yfinance():
    data = yf.download('SI=F', period='1d', interval='15m')
    data = data[['Open', 'High', 'Low', 'Close']]
    return data

# Function to fetch news
def get_news():
    url = f'https://newsapi.org/v2/everything?q=silver+price&sortBy=publishedAt&apiKey={NEWS_API_KEY}'
    response = requests.get(url)
    articles = response.json().get("articles", [])[:5]
    return [(a['title'], a['url']) for a in articles]

# Technical Indicators
def calculate_indicators(df):
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    sma_20 = df['Close'].rolling(window=20).mean()
    df['SMA_20'] = sma_20

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    rolling_std = df['Close'].rolling(window=20).std()
    df['Upper_BB'] = sma_20 + 2 * rolling_std
    df['Lower_BB'] = sma_20 - 2 * rolling_std

    return df

# Streamlit UI
st.title("Silver Trading Dashboard")

# Price Section
st.subheader("Live Silver Price (XAG/USD - via Yahoo Finance)")
price_df = get_silver_price_yfinance()

if not price_df.empty:
    price_df = calculate_indicators(price_df)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=price_df.index, y=price_df['Close'], mode='lines', name='Close Price'))
    st.plotly_chart(fig)
else:
    st.warning("No price data available.")

# News Section
st.subheader("Latest News")
news = get_news()
for title, url in news:
    st.markdown(f"- [{title}]({url})")

# SMA Trend
st.subheader("Trend Analysis (SMA)")
if not price_df.empty:
    try:
        last_sma_5 = price_df['SMA_5'].iloc[-1].item()
        last_close = price_df['Close'].iloc[-1].item()

        if pd.isna(last_sma_5) or pd.isna(last_close):
            st.warning("Not enough data for SMA trend analysis.")
        else:
            trend = "Bullish" if last_close > last_sma_5 else "Bearish"
            st.info(f"Current trend is: {trend}")
    except (IndexError, ValueError):
        st.warning("Data not sufficient for trend analysis.")

# RSI Indicator
st.subheader("Relative Strength Index (RSI)")
if not price_df.empty:
    try:
        rsi_value = price_df['RSI'].iloc[-1].item()
        if pd.isna(rsi_value):
            st.warning("Not enough data for RSI analysis.")
        else:
            st.metric("RSI", f"{rsi_value:.2f}")
            if rsi_value > 70:
                st.warning("Overbought - Possible Sell Signal")
            elif rsi_value < 30:
                st.success("Oversold - Possible Buy Signal")
    except (IndexError, ValueError):
        st.warning("Data not sufficient for RSI analysis.")

# MACD Indicator
st.subheader("MACD (Moving Average Convergence Divergence)")
if not price_df.empty:
    try:
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=price_df.index, y=price_df['MACD'], mode='lines', name='MACD'))
        fig_macd.add_trace(go.Scatter(x=price_df.index, y=price_df['Signal'], mode='lines', name='Signal'))
        st.plotly_chart(fig_macd)
    except IndexError:
        st.warning("Data not sufficient for MACD analysis.")

# Bollinger Bands
st.subheader("Bollinger Bands")
if not price_df.empty:
    try:
        fig_bb = go.Figure()
        fig_bb.add_trace(go.Scatter(x=price_df.index, y=price_df['Close'], mode='lines', name='Close'))
        fig_bb.add_trace(go.Scatter(x=price_df.index, y=price_df['Upper_BB'], mode='lines', name='Upper Band'))
        fig_bb.add_trace(go.Scatter(x=price_df.index, y=price_df['Lower_BB'], mode='lines', name='Lower Band'))
        st.plotly_chart(fig_bb)
    except IndexError:
        st.warning("Data not sufficient for Bollinger Bands analysis.")

# Buy/Sell Signal (Simple)
st.subheader("Buy/Sell Signal")
if not price_df.empty:
    try:
        last_sma_5 = price_df['SMA_5'].iloc[-1].item()
        last_sma_20 = price_df['SMA_20'].iloc[-1].item()

        if pd.isna(last_sma_5) or pd.isna(last_sma_20):
            st.warning("Insufficient data for Buy/Sell signal.")
        else:
            if last_sma_5 > last_sma_20:
                st.success("Buy Signal (SMA5 > SMA20)")
            elif last_sma_5 < last_sma_20:
                st.error("Sell Signal (SMA5 < SMA20)")
    except (IndexError, ValueError):
        st.warning("Data not sufficient for Buy/Sell signal.")
