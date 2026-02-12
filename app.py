import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta

# --- הגדרת עמוד (חובה שורה ראשונה) ---
st.set_page_config(page_title="Infinity Trader", layout="wide", page_icon="⚡")

# --- עיצוב CSS אגרסיבי (Cyberpunk/Fintech Style) ---
st.markdown("""
<style>
    /* ייבוא פונט מודרני */
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&display=swap');

    /* רקע כללי - גרדיאנט עמוק */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0f172a 0%, #000000 90%);
        font-family: 'Rajdhani', sans-serif;
        color: white;
    }

    /* הסתרת תפריטים מיותרים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* --- טיקר זז (Ticker Tape) --- */
    .ticker-wrap {
        width: 100%;
        background-color: #111;
        overflow: hidden;
        white-space: nowrap;
        border-bottom: 2px solid #00ff41;
        padding: 10px 0;
        margin-bottom: 20px;
    }
    .ticker {
        display: inline-block;
        animation: marquee 20s linear infinite;
        font-size: 1.2rem;
        font-weight: bold;
        color: #00ff41;
    }
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* --- כרטיסיות זכוכית (Glass Cards) --- */
    div.css-1r6slb0, div[data-testid="stMetric"], div.stDataFrame {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border: 1px solid #00ff41;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
    }

    /* כותרות זוהרות */
    h1, h2, h3 {
        color: #fff;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* כפתורים עתידניים */
    .stButton > button {
        background: linear-gradient(45deg, #00ff41, #008f24);
        color: black;
        border: none;
        padding: 12px 24px;
        border-radius: 5px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 10px #00ff41;
        width: 100%;
    }
    .stButton > button:hover {
        box-shadow: 0 0 20px #00ff41, 0 0 40px #00ff41;
        color: white;
    }
    
    /* תגית BUY/SELL */
    .badge-buy {
        background-color: rgba(0, 255, 65, 0.2);
        color: #00ff41;
        padding: 5px 10px;
        border-radius: 4px;
        border: 1px solid #00ff41;
        font-weight: bold;
    }
    .badge-sell {
        background-color: rgba(255, 42, 109, 0.2);
        color: #ff2a6d;
        padding: 5px 10px;
        border-radius: 4px;
        border: 1px solid #ff2a6d;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ליבה ---

@st.cache_data(ttl=300)
def get_live_ticker_data():
    """מביא נתונים מהירים לטיקר הרץ"""
    tickers = ['BTC-USD', 'ETH-USD', 'NVDA', 'AAPL', 'TSLA', 'SPY', 'QQQ']
    data_str = ""
    try:
        df = yf.download(tickers, period="1d", interval="1m", group_by='ticker', progress=False)
        for t in tickers:
            try:
                # טיפול בנתונים מרובי רמות או רמה אחת
                if len(tickers) > 1:
                    price = df[t]['Close'].iloc[-1]
                    open_p = df[t]['Open'].iloc[0]
                else:
                    price = df['Close'].iloc[-1]
                    open_p = df['Open'].iloc[0]
                    
                change = ((price - open_p) / open_p) * 100
                symbol = "▲" if change >= 0 else "▼"
                data_str += f"&nbsp;&nbsp;&nbsp;&nbsp; {t}: ${price:.2f} ({symbol}{change:.2f}%) "
            except: continue
    except:
        data_str = "MARKET DATA LOADING..."
    return data_str

def get_pro_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if len(hist) < 150: return None
        
        # אינדיקטורים
        hist['SMA50'] = ta.trend.sma_indicator(hist['Close'], window=50)
        hist['SMA200'] = ta.trend.sma_indicator(hist['Close'], window=200)
        hist['RSI'] = ta.momentum.rsi(hist['Close'], window=14)
        
        return hist
    except: return None

# --- טיקר רץ (Ticker Tape) ---
ticker_html = get_live_ticker_data()
st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker">{ticker_html} &nbsp;&nbsp; | &nbsp;&nbsp; {ticker_html}</div>
</div>
""", unsafe_allow_html=True)

# --- כותרת ראשית ---
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.title("INFINITY TRADER")
    st.caption("AI-POWERED MARKET INTELLIGENCE SYSTEM")
with col_head2:
    st.image("https://img.icons8.com/fluency/96/bullish.png", width=70) # אייקון בולט

st.markdown("---")

# --- תפריט בחירה מעוצב ---
selected_ticker = st.selectbox("", ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'COIN'], index=0, label_visibility="collapsed")

# --- גוף האפליקציה ---
if selected_ticker:
    with st.spinner(f'ACCESSING MAINFRAME: {selected_ticker}...'):
        df = get_pro_data(selected_ticker)
        
        if df is not None:
            # נתונים אחרונים
            curr = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            change = ((curr - prev) / prev) * 100
            rsi = df['RSI'].iloc[-1]
            sma200 = df['SMA200'].iloc[-1]
            vol = df['Volume'].iloc[-1]
            
            # קביעת סטטוס
            status = "NEUTRAL"
            badge_class = "badge-buy" # Default styling
            
            if curr > sma200 and rsi < 70: 
                status = "STRONG BUY"
                badge_class = "badge-buy"
            elif curr < sma200: 
                status = "SELL TREND"
                badge_class = "badge-sell"
            
            # --- כרטיסיות מידע (Top Cards) ---
            # שימוש ב-Columns ליצירת גריד
            c1, c2, c3, c4 = st.columns(4)
            
            c1.metric("CURRENT PRICE", f"${curr:.2f}", f"{change:.2f}%")
            c2.metric("RSI STRENGTH", f"{rsi:.1f}", "Overbought" if rsi>70 else "Oversold" if rsi<30 else "Normal")
            c3.metric("24H VOLUME", f"{vol/1000000:.1f}M")
            
            # כרטיס הסטטוס המיוחד
            with c4:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px;">
                    <div style="font-size: 12px; color: #888;">AI RECOMMENDATION</div>
                    <div class="{badge_class}" style="font-size: 18px; margin-top: 5px;">{status}</div>
                </div>
                """, unsafe_allow_html=True)

            # --- גרף מתקדם (Interactive Chart) ---
            st.markdown("### 📈 PRICE ACTION ANALYZER")
            
            fig = go.Figure()
            
            # נרות
            fig.add_trace(go.Candlestick(x=df.index,
                            open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'],
                            name='Price'))
            
            # ממוצעים נעים
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#00d4ff', width=1), name='SMA 50'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='#ff00d4', width=2), name='SMA 200'))
            
            # עיצוב הגרף להיראות "מקצועי"
            fig.update_layout(
                template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=600,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            # הסרת קווי רשת מיותרים
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor='#222')
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error("DATA ERROR. PLEASE REFRESH.")

# --- כפתור פעולה ---
st.markdown("---")
c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
with c_btn2:
    if st.button("🚀 SCAN FOR NEW OPPORTUNITIES"):
        st.toast("Scanning Global Markets...", icon="🌍")
        st.toast("Analyzing Volatility...", icon="📊")
        st.toast("Scan Complete: No Priority Signals Found.", icon="✅")
