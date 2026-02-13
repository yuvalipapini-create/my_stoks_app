import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- הגדרת עמוד (חובה שורה ראשונה) ---
st.set_page_config(page_title="Pro Terminal", layout="wide", page_icon="📈")

# --- עיצוב CSS יוקרתי (Dark Mode Glassmorphism) ---
st.markdown("""
<style>
    /* רקע כללי */
    .stApp {
        background-color: #000000;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* הסתרת תפריטים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* טיקר (פס רץ) */
    .ticker-wrap {
        width: 100%;
        background: #111;
        border-bottom: 2px solid #00ff00;
        overflow: hidden;
        white-space: nowrap;
        padding: 10px 0;
        margin-bottom: 20px;
    }
    .ticker {
        display: inline-block;
        animation: marquee 30s linear infinite;
        font-size: 18px;
        color: #00ff00;
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* כרטיסיות מידע */
    div[data-testid="metric-container"] {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-left: 5px solid #00ff00;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    label[data-testid="stMetricLabel"] {
        color: #888;
    }
    
    /* כפתורים */
    .stButton > button {
        background-color: #004d00;
        color: #00ff00;
        border: 1px solid #00ff00;
        width: 100%;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background-color: #00ff00;
        color: black;
    }
</style>
""", unsafe_allow_html=True)

# --- פונקציות חישוב (ללא ספריות חיצוניות) ---

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=300)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        if df.empty: return None
        
        # חישוב אינדיקטורים ידני ובטוח
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        df['RSI'] = calculate_rsi(df['Close'])
        
        return df
    except:
        return None

# --- ממשק משתמש ---

# 1. פס רץ (סטטי כדי למנוע קריסות)
st.markdown("""
<div class="ticker-wrap">
    <div class="ticker">
    AAPL: $182.00 ▲  |  NVDA: $880.00 ▲  |  TSLA: $175.00 ▼  |  MSFT: $420.00 ▲  |  BTC: $67,500 ▲  |  AMZN: $178.00 ▲
    </div>
</div>
""", unsafe_allow_html=True)

st.title("PRO TRADER TERMINAL")

# 2. אזור שליטה
col_ctrl, col_main = st.columns([1, 3])

with col_ctrl:
    st.subheader("Control Panel")
    ticker_select = st.selectbox("Select Asset:", ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'BTC-USD'], index=0)
    if st.button("Analyze Ticker"):
        st.rerun()
    
    st.markdown("---")
    st.info("System Status: Online 🟢")

# 3. תצוגה ראשית
with col_main:
    # טעינת נתונים
    df = get_stock_data(ticker_select)
    
    if df is not None:
        # נתונים אחרונים
        curr = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        change_pct = ((curr - prev) / prev) * 100
        rsi_val = df['RSI'].iloc[-1]
        
        # שורת מדדים
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Price", f"${curr:.2f}", f"{change_pct:.2f}%")
        m2.metric("RSI (14)", f"{rsi_val:.1f}")
        m3.metric("SMA 50", f"${df['SMA50'].iloc[-1]:.2f}")
        m4.metric("Volume", f"{df['Volume'].iloc[-1]/1000000:.1f}M")
        
        # גרף מקצועי
        fig = go.Figure()
        
        # נרות
        fig.add_trace(go.Candlestick(x=df.index,
                        open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'],
                        name='Price'))
        
        # ממוצעים
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='cyan', width=1), name='SMA 50'))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='orange', width=1), name='SMA 200'))
        
        fig.update_layout(
            template="plotly_dark",
            height=600,
            xaxis_rangeslider_visible=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.error("Data fetch failed. Please try refreshing.")
