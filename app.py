import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta
import feedparser
from datetime import datetime

# --- הגדרת עמוד ---
st.set_page_config(page_title="Wall St. Hebrew Terminal", layout="wide", page_icon="🇺🇸")

# --- עיצוב CSS מתקדם (Infinity Dark Mode) ---
st.markdown("""
<style>
    /* פונטים ורקע */
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');
    
    .stApp {
        background-color: #050505;
        color: #e0e0e0;
        font-family: 'Heebo', sans-serif; /* פונט עברי מודרני */
    }

    /* הסתרת תפריטים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- טיקר משודרג (איטי + עוצר במעבר עכבר) --- */
    .ticker-wrap {
        width: 100%;
        background-color: #111;
        overflow: hidden;
        white-space: nowrap;
        border-bottom: 1px solid #333;
        border-top: 1px solid #333;
        padding: 8px 0;
        margin-bottom: 20px;
    }
    .ticker {
        display: inline-block;
        animation: marquee 60s linear infinite; /* הואט ל-60 שניות */
        font-size: 1.1rem;
        font-weight: 400;
        color: #00ff88;
    }
    .ticker-wrap:hover .ticker {
        animation-play-state: paused; /* עוצר כשעוברים עם העכבר! */
        cursor: default;
    }
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* כרטיסי מידע */
    div[data-testid="metric-container"] {
        background-color: #0f0f0f;
        border: 1px solid #222;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: 0.3s;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #00ff88;
        transform: translateY(-2px);
    }

    /* כרטיסי חדשות */
    .news-card {
        background-color: #111;
        border-right: 4px solid #007bff; /* פס כחול מימין */
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 5px;
    }
    .news-title {
        color: #fff;
        font-size: 16px;
        font-weight: bold;
        text-decoration: none;
        display: block;
        margin-bottom: 5px;
    }
    .news-title:hover { color: #007bff; }
    .news-meta { color: #666; font-size: 12px; }

    /* כפתורים */
    .stButton > button {
        background: linear-gradient(90deg, #007bff, #0056b3);
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        width: 100%;
    }
    .stButton > button:hover { background: #004494; }
    
</style>
""", unsafe_allow_html=True)

# --- פונקציות ליבה ---

@st.cache_data(ttl=300)
def get_live_ticker_data():
    """מביא נתונים לטיקר"""
    tickers = ['^GSPC', '^IXIC', '^DJI', 'NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'META', 'AMD']
    display_names = {'^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^DJI': 'DOW JONES'}
    
    data_str = ""
    try:
        # משיכה מהירה
        df = yf.download(tickers, period="1d", interval="1d", group_by='ticker', progress=False)
        
        for t in tickers:
            try:
                name = display_names.get(t, t)
                if len(tickers) > 1:
                    price = df[t]['Close'].iloc[-1]
                    prev = df[t]['Open'].iloc[0] # משתמש בפתיחה כבסיס לשינוי יומי
                else:
                    price = df['Close'].iloc[-1]
                    prev = df['Open'].iloc[0]
                    
                change = ((price - prev) / prev) * 100
                symbol = "▲" if change >= 0 else "▼"
                color = "#00ff88" if change >= 0 else "#ff2a6d"
                
                # בניית המחרוזת עם צבעים (HTML בתוך המרקיו פחות נתמך, אז נשתמש בסימנים)
                data_str += f"{name}: ${price:,.2f} ({symbol}{change:.2f}%) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "
            except: continue
    except:
        data_str = "טוען נתוני שוק בזמן אמת..."
        
    return data_str * 5 # משכפל כדי שייראה רציף

@st.cache_data(ttl=600)
def get_us_economy_news_hebrew():
    """חדשות ארהב בעברית דרך גוגל"""
    # שאילתה חכמה: וול סטריט או פדרל ריזרב או כלכלת ארהב, מאתרים בישראל בעברית
    rss_url = "https://news.google.com/rss/search?q=וול+סטריט+OR+הפדרל+ריזרב+OR+כלכלת+ארהב+OR+נאסדק&hl=he&gl=IL&ceid=IL:he"
    
    try:
        feed = feedparser.parse(rss_url)
        news_items = []
        for entry in feed.entries[:8]:
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published[:16],
                "source": entry.source.title
            })
        return news_items
    except:
        return []

def get_stock_analysis(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if len(hist) < 150: return None
        
        hist['SMA50'] = ta.trend.sma_indicator(hist['Close'], window=50)
        hist['SMA200'] = ta.trend.sma_indicator(hist['Close'], window=200)
        hist['RSI'] = ta.momentum.rsi(hist['Close'], window=14)
        
        return hist
    except: return None

# --- טיקר עליון ---
ticker_text = get_live_ticker_data()
st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker">{ticker_text}</div>
</div>
""", unsafe_allow_html=True)

# --- כותרת ראשית ---
st.title("🇺🇸 US MARKETS | PRO TERMINAL")
st.markdown("מערכת ניתוח מניות וחדשות ארה'ב בזמן אמת")

# --- פריסת דף (Layout) ---
col_main, col_sidebar = st.columns([3, 1])

# --- צד שמאל (תפריט וחדשות) ---
with col_sidebar:
    st.header("חדשות ארה\"ב 📰")
    st.caption("עדכונים חיים מוול-סטריט (בעברית)")
    
    news = get_us_economy_news_hebrew()
    if news:
        for item in news:
            st.markdown(f"""
            <div class="news-card">
                <a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a>
                <div class="news-meta">
                    <span>{item['source']}</span> | <span>{item['published']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("טוען חדשות...")

# --- צד ימין (גרפים ונתונים) ---
with col_main:
    # בחירת מניה
    selected_ticker = st.selectbox("בחר מניה לניתוח:", 
                                  ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'INTC', 'COIN'],
                                  index=0)
    
    if selected_ticker:
        df = get_stock_analysis(selected_ticker)
        
        if df is not None:
            curr = df['Close'].iloc[-1]
            change = ((curr - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
            rsi = df['RSI'].iloc[-1]
            sma200 = df['SMA200'].iloc[-1]
            
            # כרטיסי מידע
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("מחיר אחרון", f"${curr:.2f}", f"{change:.2f}%")
            m2.metric("RSI (מומנטום)", f"{rsi:.1f}", "Overbought" if rsi>70 else "Oversold" if rsi<30 else "Neutral")
            m3.metric("מגמה ראשית (200)", "BULLISH" if curr > sma200 else "BEARISH", delta_color="normal")
            m4.metric("ווליום יומי", f"{df['Volume'].iloc[-1]/1000000:.1f}M")
            
            # גרף
            st.subheader(f"ניתוח טכני: {selected_ticker}")
            
            fig = go.Figure()
            
            # נרות
            fig.add_trace(go.Candlestick(x=df.index,
                            open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'],
                            name='Price'))
            
            # ממוצעים
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#00d4ff', width=1.5), name='SMA 50'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='#ff00d4', width=1.5), name='SMA 200'))
            
            fig.update_layout(
                template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=550,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", y=1, x=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # כפתור סריקה
            st.markdown("---")
            if st.button(f"🔍 הרץ סריקת עומק על {selected_ticker}"):
                st.success("האלגוריתם מזהה תבנית פריצה אפשרית (Demo Signal).")
