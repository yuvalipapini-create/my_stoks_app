import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
import feedparser
import datetime

# --- הגדרת עמוד (חייב להיות ראשון) ---
st.set_page_config(page_title="Terminal X", layout="wide", page_icon="⚡")

# --- עיצוב CSS אולטימטיבי (Bloomberg Terminal Style) ---
st.markdown("""
<style>
    /* ייבוא פונטים דיגיטליים */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');

    /* גוף האתר */
    .stApp {
        background-color: #000000;
        color: #00ff00;
        font-family: 'Roboto Mono', monospace;
    }

    /* הסתרת אלמנטים מיותרים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* כרטיסי מידע (Metrics) */
    div[data-testid="metric-container"] {
        background-color: #111;
        border: 1px solid #333;
        border-radius: 0px; /* פינות חדות */
        padding: 15px;
        color: #00ff00;
        border-left: 3px solid #00ff00;
    }
    label[data-testid="stMetricLabel"] {
        color: #888 !important;
    }
    
    /* כפתורים */
    .stButton > button {
        background-color: #003300;
        color: #00ff00;
        border: 1px solid #00ff00;
        border-radius: 0px;
        font-family: 'Roboto Mono', monospace;
        text-transform: uppercase;
        font-weight: bold;
        transition: 0.2s;
    }
    .stButton > button:hover {
        background-color: #00ff00;
        color: black;
        box-shadow: 0 0 10px #00ff00;
    }

    /* טיקר (פס רץ) */
    .ticker-wrap {
        width: 100%;
        background-color: #0a0a0a;
        border-bottom: 2px solid #333;
        overflow: hidden;
        white-space: nowrap;
        padding: 8px 0;
    }
    .ticker {
        display: inline-block;
        animation: marquee 30s linear infinite;
        color: #00ff00;
        font-weight: bold;
        font-size: 14px;
    }
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* טבלאות */
    .stDataFrame { border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ליבה וחישובים (Backend) ---

@st.cache_data(ttl=300)
def get_bulk_data():
    """מוריד נתונים לכל המניות במכה אחת לביצועים מקסימליים"""
    tickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'JPM', 'V', 'LLY', 'AVGO', 'NFLX', 'INTC', 'BTC-USD']
    try:
        # הורדה קבוצתית
        data = yf.download(tickers, period="6mo", group_by='ticker', progress=False)
        return data, tickers
    except:
        return None, []

def calculate_advanced_technicals(df):
    """מחשב אינדיקטורים מתקדמים בעזרת ספריית TA"""
    try:
        # RSI
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        
        # Bollinger Bands
        indicator_bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_High'] = indicator_bb.bollinger_hband()
        df['BB_Low'] = indicator_bb.bollinger_lband()
        
        # MACD
        indicator_macd = ta.trend.MACD(close=df['Close'])
        df['MACD'] = indicator_macd.macd()
        df['MACD_Signal'] = indicator_macd.macd_signal()
        
        # SMA / EMA
        df['SMA200'] = ta.trend.sma_indicator(df['Close'], window=200)
        df['EMA50'] = ta.trend.ema_indicator(df['Close'], window=50)
        
        return df
    except:
        return df

def get_news_rss():
    """חדשות בזמן אמת"""
    try:
        # גוגל ניוז ספציפי לכלכלה
        url = "https://news.google.com/rss/search?q=שוק+ההון+וול+סטריט&hl=he&gl=IL&ceid=IL:he"
        feed = feedparser.parse(url)
        return feed.entries[:8]
    except: return []

# --- ממשק משתמש (UI Layout) ---

# 1. טיקר עליון (Static Fallback for Speed)
st.markdown("""
<div class="ticker-wrap">
    <div class="ticker">
    AAPL: $182.30 ▲ | NVDA: $880.10 ▲ | TSLA: $175.50 ▼ | BTC: $67,000 ▲ | SPX: 5,100 ▲ | NASDAQ: 16,300 ▲ | GOLD: $2,150 ▲
    </div>
</div>
""", unsafe_allow_html=True)

st.title("TERMINAL X | QUANT ANALYSIS")

# טאבים ראשיים
tab_dash, tab_scanner, tab_news = st.tabs(["📊 DEEP DIVE", "⚡ SIGNAL SCANNER", "📰 LIVE WIRE"])

# --- TAB 1: ניתוח עומק ---
with tab_dash:
    col_input, col_kpi = st.columns([1, 4])
    
    with col_input:
        st.subheader("ASSET SELECTOR")
        ticker = st.selectbox("SYMBOL", ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'BTC-USD'], index=0)
        
        if st.button("ANALYZE"):
            st.rerun()

    # משיכת נתונים למניה בודדת
    stock_df = yf.Ticker(ticker).history(period="1y")
    
    if not stock_df.empty:
        stock_df = calculate_advanced_technicals(stock_df)
        
        # נתונים אחרונים
        curr = stock_df['Close'].iloc[-1]
        prev = stock_df['Close'].iloc[-2]
        chg = ((curr - prev) / prev) * 100
        rsi = stock_df['RSI'].iloc[-1]
        
        # KPI ROW
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("LAST PRICE", f"${curr:.2f}", f"{chg:.2f}%")
        k2.metric("RSI (14)", f"{rsi:.1f}")
        k3.metric("VOLUME", f"{stock_df['Volume'].iloc[-1]/1M:.1f}M")
        
        # לוגיקה פשוטה לאיתות
        signal = "NEUTRAL"
        if rsi < 30: signal = "OVERSOLD (BUY)"
        elif rsi > 70: signal = "OVERBOUGHT (SELL)"
        elif curr > stock_df['BB_High'].iloc[-1]: signal = "BREAKOUT UP"
        
        k4.metric("ALGO SIGNAL", signal)
        
        # גרף משולב (Candlestick + Bollinger + Volume)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, subplot_titles=(f'{ticker} PRICE ACTION', 'VOLUME'), 
                            row_width=[0.2, 0.7])

        # מחיר ונרות
        fig.add_trace(go.Candlestick(x=stock_df.index,
                                     open=stock_df['Open'], high=stock_df['High'],
                                     low=stock_df['Low'], close=stock_df['Close'], name="OHLC"), row=1, col=1)
        
        # Bollinger Bands
        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['BB_High'], line=dict(color='gray', width=1, dash='dot'), name='BB Upper'), row=1, col=1)
        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['BB_Low'], line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(255,255,255,0.05)', name='BB Lower'), row=1, col=1)
        
        # ממוצע נע
        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['EMA50'], line=dict(color='#00ff00', width=1.5), name='EMA 50'), row=1, col=1)

        # ווליום
        colors = ['#00ff00' if row['Open'] - row['Close'] >= 0 else '#ff0000' for index, row in stock_df.iterrows()]
        fig.add_trace(go.Bar(x=stock_df.index, y=stock_df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#000",
            plot_bgcolor="#000",
            height=600,
            xaxis_rangeslider_visible=False,
            margin=dict(l=5, r=5, t=30, b=5)
        )
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: סורק מתקדם ---
with tab_scanner:
    st.header("⚡ REAL-TIME MOMENTUM SCANNER")
    
    if st.button("RUN SYSTEM SCAN"):
        with st.spinner("SCANNING MARKET DATA..."):
            data, tickers = get_bulk_data()
            results = []
            
            if data is not None:
                for t in tickers:
                    try:
                        # חילוץ דאטה למניה בודדת מתוך ה-Bulk
                        df = data[t].dropna()
                        if len(df) < 50: continue
                        
                        # חישוב מהיר
                        curr = df['Close'].iloc[-1]
                        rsi = ta.momentum.rsi(df['Close'], window=14).iloc[-1]
                        sma50 = ta.trend.sma_indicator(df['Close'], window=50).iloc[-1]
                        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].tail(20).mean()
                        
                        # לוגיקה חכמה
                        score = 0
                        if curr > sma50: score += 1      # מגמה חיובית
                        if vol_ratio > 1.2: score += 1   # כניסת כסף
                        if 40 < rsi < 70: score += 1     # RSI בריא
                        
                        status = "WAIT"
                        if score == 3: status = "STRONG BUY"
                        elif score == 2: status = "BUY"
                        
                        results.append({
                            "TICKER": t,
                            "PRICE": curr,
                            "RSI": rsi,
                            "VOL RATIO": vol_ratio,
                            "STATUS": status
                        })
                    except: continue
                
                # הצגת התוצאות
                if results:
                    scan_df = pd.DataFrame(results).sort_values(by="VOL RATIO", ascending=False)
                    st.dataframe(
                        scan_df.style.format({"PRICE": "${:.2f}", "RSI": "{:.1f}", "VOL RATIO": "{:.2f}x"})
                        .applymap(lambda x: 'color: #00ff00; font-weight: bold' if x == 'STRONG BUY' else '', subset=['STATUS']),
                        use_container_width=True,
                        height=600
                    )
                else:
                    st.warning("NO DATA FOUND")

# --- TAB 3: חדשות ---
with tab_news:
    st.header("INTELLIGENCE FEED")
    news = get_news_rss()
    
    c1, c2 = st.columns(2)
    for i, item in enumerate(news):
        with (c1 if i%2==0 else c2):
            st.markdown(f"""
            <div style="border: 1px solid #333; padding: 10px; margin-bottom: 10px; border-left: 2px solid #00ff00;">
                <a href="{item.link}" target="_blank" style="color: #00ff00; text-decoration: none; font-weight: bold;">{item.title}</a>
                <div style="color: #666; font-size: 12px; margin-top: 5px;">{item.published}</div>
            </div>
            """, unsafe_allow_html=True)
