import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ta
import feedparser
from datetime import datetime

# --- הגדרת עמוד ---
st.set_page_config(page_title="ProTrade Terminal", layout="wide", page_icon="💹")

# --- עיצוב CSS (Dark Terminal Theme) ---
st.markdown("""
<style>
    /* רקע ראשי */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* העלמת תפריטים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* סרגל צד */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* כרטיסי מידע */
    div.css-1r6slb0 {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 15px;
    }
    
    /* כותרות ירוקות */
    h1, h2, h3 {
        color: #3fb950 !important; 
        font-family: 'Courier New', Courier, monospace;
        letter-spacing: -0.5px;
    }
    
    /* כרטיס חדשות */
    .news-card {
        background-color: #21262d;
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff; 
        padding: 15px;
        margin-bottom: 12px;
        border-radius: 6px;
        transition: transform 0.2s;
    }
    .news-card:hover {
        transform: translateX(5px);
        border-left-color: #3fb950;
    }
    .news-title {
        color: #ffffff;
        font-size: 16px;
        font-weight: 600;
        text-decoration: none;
        display: block;
        margin-bottom: 8px;
    }
    .news-meta {
        color: #8b949e;
        font-size: 12px;
        display: flex;
        justify-content: space-between;
    }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ---

@st.cache_data(ttl=300)
def get_google_news():
    """מושך חדשות דרך Google News RSS (לא נחסם)"""
    # כתובת מיוחדת שמסננת רק חדשות שוק ההון בעברית מישראל
    rss_url = "https://news.google.com/rss/search?q=שוק+ההון+בורסה&hl=he&gl=IL&ceid=IL:he"
    
    try:
        feed = feedparser.parse(rss_url)
        news_items = []
        for entry in feed.entries[:10]: # 10 כותרות אחרונות
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "source": entry.source.title if 'source' in entry else "Google News"
            })
        return news_items
    except Exception as e:
        return []

def get_market_data_safe(tickers):
    data = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            
            if len(hist) < 150: continue
            
            curr_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            sma150 = ta.trend.sma_indicator(hist['Close'], window=150).iloc[-1]
            rsi = ta.momentum.rsi(hist['Close'], window=14).iloc[-1]
            vol_curr = hist['Volume'].iloc[-1]
            vol_avg = hist['Volume'].tail(20).mean()
            
            # ניקוד
            score = 0
            if curr_price > sma150: score += 40
            if vol_curr > vol_avg: score += 20
            if 40 < rsi < 70: score += 20
            if curr_price > prev_price: score += 20
            
            atr = ta.volatility.average_true_range(hist['High'], hist['Low'], hist['Close']).iloc[-1]
            
            data.append({
                "Symbol": ticker,
                "Price": curr_price,
                "Change%": ((curr_price - prev_price)/prev_price)*100,
                "SMA150": sma150,
                "RSI": rsi,
                "Score": score,
                "StopLoss": curr_price - (atr * 2),
                "Target": curr_price + (atr * 3)
            })
        except:
            continue
    return pd.DataFrame(data)

# רשימת נכסים
TICKERS = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AMD', 'JPM', 'V', 'LLY', 'AVGO', 'WMT', 'XOM', 'MA', 'PG', 'COST', 'JNJ', 'HD', 'CVX']

# --- ממשק משתמש (Frontend) ---

with st.sidebar:
    st.header("⚡ ProTrade")
    st.markdown("---")
    page = st.radio("תפריט ראשי:", ["🏠 דשבורד", "📰 חדשות חמות", "🚀 סורק", "🔎 גרפים"])
    st.markdown("---")
    st.info("System Online 🟢")

# === עמוד 1: דשבורד ===
if page == "🏠 דשבורד":
    st.title("Market Overview")
    if st.button("רענן נתונים"):
        with st.spinner("טוען..."):
            df = get_market_data_safe(TICKERS)
            if not df.empty:
                c1, c2, c3 = st.columns(3)
                best = df.loc[df['Change%'].idxmax()]
                c1.metric("Top Gainer", best['Symbol'], f"{best['Change%']:.2f}%")
                c2.metric("Market Sentiment", "BULLISH" if df['Change%'].mean() > 0 else "BEARISH")
                c3.metric("Avg RSI", f"{df['RSI'].mean():.1f}")
                
                st.subheader("Market Heatmap")
                fig = px.treemap(df, path=[px.Constant("Market"), 'Symbol'], values='Price',
                                 color='Change%', color_continuous_scale=['#d32f2f', '#121212', '#388e3c'],
                                 color_continuous_midpoint=0)
                st.plotly_chart(fig, use_container_width=True)

# === עמוד 2: חדשות (המתוקן) ===
elif page == "📰 חדשות חמות":
    st.title("חדשות שוק ההון (ישראל)")
    st.caption("מופעל ע'י Google News Aggregator 🔴 בשידור חי")
    
    if st.button("טען חדשות עכשיו"):
        with st.spinner("מושך כותרות מכל האתרים הכלכליים..."):
            news = get_google_news()
            
            if news:
                # סידור ב-2 עמודות
                c1, c2 = st.columns(2)
                for i, item in enumerate(news):
                    with (c1 if i % 2 == 0 else c2):
                        st.markdown(f"""
                        <div class="news-card">
                            <a href="{item['link']}" target="_blank" class="news-title">
                                {item['title']}
                            </a>
                            <div class="news-meta">
                                <span>מקור: {item['source']}</span>
                                <span>{item['published'][:16]}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error("לא נמצאו כותרות. נסה שוב בעוד דקה.")

# === עמוד 3: סורק ===
elif page == "🚀 סורק":
    st.title("AI Opportunity Scanner")
    if st.button("הפעל סורק"):
        df = get_market_data_safe(TICKERS)
        opps = df[df['Score'] >= 60].sort_values(by='Score', ascending=False)
        if not opps.empty:
            st.success(f"נמצאו {len(opps)} הזדמנויות!")
            st.dataframe(opps[['Symbol', 'Price', 'Change%', 'RSI', 'StopLoss', 'Target']], use_container_width=True)

# === עמוד 4: גרפים ===
elif page == "🔎 גרפים":
    st.title("Advanced Charting")
    ticker = st.selectbox("בחר מניה:", TICKERS)
    if ticker:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        hist['SMA50'] = ta.trend.sma_indicator(hist['Close'], window=50)
        hist['SMA150'] = ta.trend.sma_indicator(hist['Close'], window=150)
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name='Price'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA150'], line=dict(color='#ffa726', width=1.5), name='SMA 150'))
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
