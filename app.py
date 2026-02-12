import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta
import feedparser

# --- 1. הגדרת עמוד (חייב להיות ראשון) ---
st.set_page_config(page_title="FutureTrade AI", layout="wide", page_icon="💎")

# --- 2. עיצוב חדשני (Glassmorphism & Neon) ---
st.markdown("""
<style>
    /* ייבוא פונט טכנולוגי */
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;600&display=swap');

    /* רקע ראשי - גרדיאנט עמוק */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #ffffff;
        font-family: 'Exo 2', sans-serif;
    }

    /* הסתרת תפריטים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* --- טיקר (פס רץ) איטי ואלגנטי --- */
    .ticker-container {
        width: 100%;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        overflow: hidden;
        white-space: nowrap;
        padding: 12px 0;
        margin-bottom: 25px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    }
    .ticker-text {
        display: inline-block;
        font-size: 16px;
        color: #00d2ff; /* טורקיז ניאון */
        letter-spacing: 1px;
        animation: scroll 60s linear infinite; /* איטי מאוד */
    }
    .ticker-container:hover .ticker-text {
        animation-play-state: paused; /* עוצר כשעוברים עם העכבר */
        cursor: help;
    }
    @keyframes scroll {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* --- כרטיסיות זכוכית (Glass Cards) --- */
    div[data-testid="metric-container"], .news-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 20px rgba(0, 210, 255, 0.3);
        border: 1px solid rgba(0, 210, 255, 0.5);
    }

    /* --- כותרות --- */
    h1, h2, h3 {
        color: #ffffff !important;
        text-shadow: 0 0 10px rgba(0, 210, 255, 0.7);
        font-weight: 600;
        letter-spacing: 1px;
    }

    /* --- כפתורים זוהרים --- */
    .stButton > button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3);
        width: 100%;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 25px rgba(0, 210, 255, 0.6);
    }

    /* טאבים */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 10px;
        color: #aaa;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. פונקציות ליבה (Backend) ---

@st.cache_data(ttl=600)
def get_market_sentiment():
    """מייצר את הטיקר"""
    tickers = ['^GSPC', '^IXIC', 'BTC-USD', 'ETH-USD', 'NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL']
    display = {'^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', 'BTC-USD': 'BITCOIN', 'ETH-USD': 'ETHEREUM'}
    
    text = ""
    try:
        data = yf.download(tickers, period="1d", progress=False)
        for t in tickers:
            try:
                # טיפול במבנה נתונים
                if len(tickers) > 1:
                    price = data['Close'][t].iloc[-1]
                    prev = data['Open'][t].iloc[0]
                else:
                    price = data['Close'].iloc[-1]
                    prev = data['Open'].iloc[0]
                    
                change = ((price - prev) / prev) * 100
                symbol = "▲" if change >= 0 else "▼"
                name = display.get(t, t)
                text += f"{name}: ${price:,.2f} ({symbol}{change:.2f}%) &nbsp;&nbsp; | &nbsp;&nbsp; "
            except: continue
    except:
        return "Market Data Loading... Please Wait..."
        
    return text * 5

@st.cache_data(ttl=900)
def get_news_hebrew():
    url = "https://news.google.com/rss/search?q=וול+סטריט+OR+טכנולוגיה+OR+בינה+מלאכותית&hl=he&gl=IL&ceid=IL:he"
    try:
        feed = feedparser.parse(url)
        return feed.entries[:6]
    except: return []

def run_scanner():
    # רשימת מניות טכנולוגיה מובילות
    tickers = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AMD', 'NFLX', 'INTC', 'CRM', 'ORCL', 'QCOM', 'ADBE']
    results = []
    
    data = yf.download(tickers, period="6mo", group_by='ticker', progress=False)
    
    for t in tickers:
        try:
            df = data[t].dropna()
            if len(df) < 50: continue
            
            curr = df['Close'].iloc[-1]
            sma50 = ta.trend.sma_indicator(df['Close'], window=50).iloc[-1]
            rsi = ta.momentum.rsi(df['Close'], window=14).iloc[-1]
            vol_curr = df['Volume'].iloc[-1]
            vol_avg = df['Volume'].tail(20).mean()
            
            # לוגיקת סורק פשוטה ויעילה
            score = 0
            if curr > sma50: score += 1
            if rsi < 70 and rsi > 40: score += 1
            if vol_curr > vol_avg: score += 1
            
            if score >= 2: # מציג מניות עם פוטנציאל
                results.append({
                    "Symbol": t,
                    "Price": curr,
                    "RSI": rsi,
                    "Vol Ratio": vol_curr / vol_avg,
                    "Status": "Strong Buy" if score == 3 else "Buy"
                })
        except: continue
    
    return pd.DataFrame(results)

# --- 4. ממשק המשתמש (UI) ---

# טיקר עליון
ticker_txt = get_market_sentiment()
st.markdown(f"""
<div class="ticker-container">
    <div class="ticker-text">{ticker_txt}</div>
</div>
""", unsafe_allow_html=True)

# כותרת ראשית
c1, c2 = st.columns([1, 5])
with c1:
    st.image("https://cdn-icons-png.flaticon.com/512/3233/3233499.png", width=80)
with c2:
    st.title("FUTURE TRADE | AI TERMINAL")
    st.markdown("מערכת מסחר אלגוריתמית מתקדמת")

# טאבים מעוצבים
tabs = st.tabs(["💎 סורק AI", "📈 גרפים וניתוח", "📰 חדשות ועדכונים"])

# --- טאב 1: סורק ---
with tabs[0]:
    st.header("סורק הזדמנויות חכם")
    st.markdown("מאתר מניות במומנטום חיובי עם אישור ווליום.")
    
    if st.button("🚀 הפעל סריקת שוק"):
        with st.spinner("מנתח ביג דאטה..."):
            df = run_scanner()
            if not df.empty:
                df = df.sort_values(by="Vol Ratio", ascending=False)
                st.dataframe(
                    df.style.format({"Price": "${:.2f}", "RSI": "{:.1f}", "Vol Ratio": "{:.2f}x"})
                    .background_gradient(subset=['RSI'], cmap='magma'),
                    use_container_width=True,
                    height=500
                )
            else:
                st.warning("לא נמצאו איתותים חזקים כרגע.")

# --- טאב 2: גרפים ---
with tabs[1]:
    col_sel, col_chart = st.columns([1, 3])
    
    with col_sel:
        st.subheader("בחר נכס")
        symbol = st.selectbox("", ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'BTC-USD', 'ETH-USD'], label_visibility="collapsed")
        
        # נתונים מהירים בצד
        if symbol:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1y")
            curr = hist['Close'].iloc[-1]
            change = ((curr - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100
            
            st.markdown("---")
            st.metric("מחיר אחרון", f"${curr:,.2f}", f"{change:.2f}%")
            st.metric("גבוה יומי", f"${hist['High'].iloc[-1]:,.2f}")
            st.metric("נמוך יומי", f"${hist['Low'].iloc[-1]:,.2f}")

    with col_chart:
        if symbol:
            st.subheader(f"ניתוח טכני: {symbol}")
            
            # גרף מתקדם
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name='Price'))
            
            fig.update_layout(
                template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=600,
                xaxis_rangeslider_visible=False,
                margin=dict(l=0, r=0, t=20, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

# --- טאב 3: חדשות ---
with tabs[2]:
    st.header("עדכונים חיים מהשווקים")
    news = get_news_hebrew()
    
    if news:
        col1, col2 = st.columns(2)
        for i, item in enumerate(news):
            with (col1 if i % 2 == 0 else col2):
                st.markdown(f"""
                <div class="news-card">
                    <a href="{item.link}" target="_blank" style="text-decoration:none; color:#00d2ff; font-weight:bold; font-size:18px;">
                        {item.title}
                    </a>
                    <div style="margin-top:10px; color:#aaa; font-size:12px;">
                        {item.source.title} | {item.published[:16]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
