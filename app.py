import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta

# --- הגדרת עמוד (חובה בהתחלה) ---
st.set_page_config(page_title="Pro Terminal", layout="wide", page_icon="📈")

# --- עיצוב CSS יוקרתי (Bloomberg Style) ---
st.markdown("""
<style>
    /* רקע שחור עמוק */
    .stApp { background-color: #000000; color: #e0e0e0; font-family: 'Roboto', sans-serif; }
    
    /* כותרות ניאון */
    h1, h2, h3 { color: #00ff88 !important; text-transform: uppercase; letter-spacing: 1px; }
    
    /* הסתרת אלמנטים של סטרים-ליט */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* כרטיסי מידע (Metrics) */
    div[data-testid="metric-container"] {
        background-color: #111111;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #00ff88;
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.1);
    }
    
    /* כפתורים */
    .stButton > button {
        background-color: #00ff88;
        color: black;
        font-weight: bold;
        border: none;
        border-radius: 0px;
        padding: 10px 20px;
        text-transform: uppercase;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #00cc6a;
        box-shadow: 0 0 15px #00ff88;
        color: black;
    }

    /* טבלאות */
    .stDataFrame { border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ליבה ---

@st.cache_data(ttl=600) # זיכרון מטמון ל-10 דקות לשיפור מהירות
def get_data(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if len(df) < 100: return None
        return df
    except: return None

def calculate_metrics(df):
    # חישוב אינדיקטורים טכניים
    close = df['Close']
    df['SMA150'] = ta.trend.sma_indicator(close, window=150)
    df['RSI'] = ta.momentum.rsi(close, window=14)
    return df

# --- רשימת מעקב (Watchlist) ---
TICKERS = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'JPM', 'PLTR', 'COIN', 'NFLX']

# --- כותרת ראשית ---
col_logo, col_title = st.columns([1, 5])
with col_title:
    st.title("PRO TRADER TERMINAL")
    st.markdown("SYSTEM STATUS: **ONLINE** | DATA: **REAL-TIME**")

st.markdown("---")

# --- אזור בחירה ---
selected_ticker = st.selectbox("SEARCH ASSET:", TICKERS, index=0)

# --- טעינת נתונים ---
if selected_ticker:
    with st.spinner(f'ANALYZING {selected_ticker}...'):
        df = get_data(selected_ticker)
        
        if df is not None:
            df = calculate_metrics(df)
            last_price = df['Close'].iloc[-1].item() # תיקון המרת נתונים
            prev_price = df['Close'].iloc[-2].item()
            change_pct = ((last_price - prev_price) / prev_price) * 100
            rsi = df['RSI'].iloc[-1].item()
            sma150 = df['SMA150'].iloc[-1].item()
            
            # --- דשבורד עליון (Top Metrics) ---
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("CURRENT PRICE", f"${last_price:.2f}", f"{change_pct:.2f}%")
            m2.metric("RSI INDICATOR", f"{rsi:.1f}", "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral")
            m3.metric("TREND (SMA 150)", f"${sma150:.2f}", "BULLISH" if last_price > sma150 else "BEARISH")
            
            # המלצת אלגוריתם פשוטה
            signal = "WAIT"
            if last_price > sma150 and rsi < 70: signal = "BUY"
            elif last_price < sma150: signal = "SELL"
            
            m4.metric("AI SIGNAL", signal)

            # --- גרף נרות יפניים (Candlestick) ---
            st.markdown("### TECHNICAL CHART")
            fig = go.Figure()
            
            # נרות
            fig.add_trace(go.Candlestick(x=df.index,
                            open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'],
                            name='Price'))
            
            # ממוצע נע
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA150'], line=dict(color='#ff9900', width=2), name='SMA 150'))

            fig.update_layout(
                template="plotly_dark",
                plot_bgcolor="#000000",
                paper_bgcolor="#000000",
                height=500,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.error("DATA UNAVAILABLE FOR THIS ASSET")

# --- סריקת הזדמנויות (Top Picks) ---
st.markdown("---")
st.header("⚡ MARKET SCANNERS (TOP OPPORTUNITIES)")

if st.button("RUN ALGO SCANNER"):
    scanner_results = []
    progress = st.progress(0)
    
    for i, t in enumerate(TICKERS):
        d = get_data(t)
        if d is not None:
            d = calculate_metrics(d)
            lp = d['Close'].iloc[-1].item()
            s150 = d['SMA150'].iloc[-1].item()
            r = d['RSI'].iloc[-1].item()
            
            # לוגיקה: מעל ממוצע 150 + RSI לא גבוה מדי
            if lp > s150 and r < 70:
                scanner_results.append({
                    "Ticker": t,
                    "Price": lp,
                    "RSI": r,
                    "Dist from SMA": ((lp/s150)-1)*100
                })
        progress.progress((i + 1) / len(TICKERS))
        
    if scanner_results:
        st.success(f"FOUND {len(scanner_results)} OPPORTUNITIES")
        res_df = pd.DataFrame(scanner_results)
        
        # עיצוב הטבלה
        st.dataframe(
            res_df.style.format({"Price": "${:.2f}", "RSI": "{:.1f}", "Dist from SMA": "{:.1f}%"}),
            use_container_width=True
        )
    else:
        st.warning("NO PERFECT SETUPS FOUND RIGHT NOW")
