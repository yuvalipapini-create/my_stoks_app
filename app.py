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
        font-family: 'Roboto', sans-serif;
    }
    
    /* העלמת תפריטים מיותרים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* סרגל צד */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* כרטיסי מידע (Cards) */
    div.css-1r6slb0 {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    /* כותרות ירוקות (Terminal Style) */
    h1, h2, h3 {
        color: #2ea043 !important; /* GitHub Green */
        font-family: 'Courier New', Courier, monospace;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    /* כפתורים */
    .stButton > button {
        background-color: #238636;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: 0.2s;
    }
    .stButton > button:hover {
        background-color: #2ea043;
    }
    
    /* כרטיס חדשות */
    .news-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #1f6feb; /* Blue accent */
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 4px;
    }
    .news-title {
        color: #58a6ff;
        font-size: 16px;
        font-weight: bold;
        text-decoration: none;
    }
    .news-date {
        color: #8b949e;
        font-size: 12px;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ---

@st.cache_data(ttl=600)
def get_aggregated_news():
    """מושך חדשות ממספר מקורות כדי להבטיח תוצאות"""
    news_items = []
    
    # רשימת מקורות (RSS)
    sources = [
        {"name": "Globes", "url": "https://www.globes.co.il/webservice/rss/rssfeeder.asmx?folderid=2971"}, # שוק ההון
        {"name": "Bizportal", "url": "https://www.bizportal.co.il/feed/rss/general"},
        {"name": "TheMarker", "url": "https://www.themarker.com/cmlink/1.144"}
    ]
    
    for source in sources:
        try:
            feed = feedparser.parse(source["url"])
            # לוקחים רק 3 כותרות מכל מקור כדי לגוון
            for entry in feed.entries[:3]:
                news_items.append({
                    "source": source["name"],
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.published if 'published' in entry else datetime.now().strftime("%Y-%m-%d")
                })
        except:
            continue
            
    return news_items

def get_market_data_safe(tickers):
    data = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            # אופטימיזציה: משיכת שנה אחורה
            hist = stock.history(period="1y")
            
            if len(hist) < 150: continue
            
            # חישובים
            curr_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            
            # SMA
            sma150 = ta.trend.sma_indicator(hist['Close'], window=150).iloc[-1]
            
            # RSI
            rsi = ta.momentum.rsi(hist['Close'], window=14).iloc[-1]
            
            # Volume
            vol_curr = hist['Volume'].iloc[-1]
            vol_avg = hist['Volume'].tail(20).mean()
            
            # Score Algorithm
            score = 0
            if curr_price > sma150: score += 40
            if vol_curr > vol_avg: score += 20
            if 40 < rsi < 70: score += 20
            if curr_price > prev_price: score += 20
            
            # ATR for Stop Loss
            atr = ta.volatility.average_true_range(hist['High'], hist['Low'], hist['Close']).iloc[-1]
            
            info = stock.info
            
            data.append({
                "Symbol": ticker,
                "Price": curr_price,
                "Change%": ((curr_price - prev_price)/prev_price)*100,
                "SMA150": sma150,
                "RSI": rsi,
                "VolRatio": vol_curr / vol_avg,
                "Score": score,
                "StopLoss": curr_price - (atr * 2),
                "Target": curr_price + (atr * 3),
                "Sector": info.get('sector', 'N/A'),
                "MarketCap": info.get('marketCap', 0)
            })
        except:
            continue # דלג על מניה בעייתית
            
    return pd.DataFrame(data)

# רשימת נכסים (Top 25 Liquidity)
TICKERS = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AMD', 'JPM', 'V', 'LLY', 'AVGO', 'WMT', 'XOM', 'MA', 'PG', 'COST', 'JNJ', 'HD', 'CVX', 'BAC', 'KO', 'PEP', 'NFLX', 'INTC']

# --- ממשק משתמש (Frontend) ---

with st.sidebar:
    st.header("⚡ ProTrade")
    st.markdown("---")
    page = st.radio("תפריט ראשי:", ["🏠 דשבורד", "🚀 סורק", "🔎 גרפים", "📰 חדשות"])
    st.markdown("---")
    st.caption("Live Data by Yahoo Finance")

# === עמוד 1: דשבורד ===
if page == "🏠 דשבורד":
    st.title("Market Overview")
    
    if st.button("רענן נתונים"):
        with st.spinner("טוען נתוני שוק..."):
            df = get_market_data_safe(TICKERS)
            if not df.empty:
                # מדדים
                c1, c2, c3 = st.columns(3)
                best = df.loc[df['Change%'].idxmax()]
                worst = df.loc[df['Change%'].idxmin()]
                
                c1.metric("Top Gainer", best['Symbol'], f"{best['Change%']:.2f}%")
                c2.metric("Top Loser", worst['Symbol'], f"{worst['Change%']:.2f}%")
                c3.metric("Avg RSI", f"{df['RSI'].mean():.1f}")
                
                # מפת חום
                st.subheader("Market Heatmap")
                fig = px.treemap(df, path=[px.Constant("Market"), 'Sector', 'Symbol'], values='MarketCap',
                                 color='Change%', color_continuous_scale=['#d32f2f', '#212121', '#388e3c'],
                                 color_continuous_midpoint=0)
                fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=500)
                st.plotly_chart(fig, use_container_width=True)

# === עמוד 2: סורק הזדמנויות ===
elif page == "🚀 סורק":
    st.title("AI Opportunity Scanner")
    st.info("הסורק מחפש מניות במגמה עולה (SMA150) עם מומנטום חיובי ויעד רווח מחושב.")
    
    if st.button("הפעל סורק"):
        with st.spinner("מנתח הזדמנויות..."):
            df = get_market_data_safe(TICKERS)
            # סינון: רק מניות עם ציון גבוה
            opportunities = df[df['Score'] >= 60].sort_values(by='Score', ascending=False)
            
            if not opportunities.empty:
                st.success(f"נמצאו {len(opportunities)} הזדמנויות!")
                st.dataframe(
                    opportunities[['Symbol', 'Price', 'Change%', 'RSI', 'StopLoss', 'Target']],
                    column_config={
                        "Price": st.column_config.NumberColumn("מחיר", format="$%.2f"),
                        "Change%": st.column_config.NumberColumn("שינוי", format="%.2f%%"),
                        "RSI": st.column_config.ProgressColumn("מומנטום", min_value=0, max_value=100, format="%d"),
                        "StopLoss": st.column_config.NumberColumn("🔴 Stop", format="$%.2f"),
                        "Target": st.column_config.NumberColumn("🟢 Target", format="$%.2f"),
                    },
                    use_container_width=True,
                    height=500
                )
            else:
                st.warning("לא נמצאו מניות העונות לקריטריונים המחמירים.")

# === עמוד 3: גרפים ===
elif page == "🔎 גרפים":
    st.title("Advanced Charting")
    ticker = st.selectbox("בחר מניה:", TICKERS)
    
    if ticker:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        hist['SMA50'] = ta.trend.sma_indicator(hist['Close'], window=50)
        hist['SMA150'] = ta.trend.sma_indicator(hist['Close'], window=150)
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=hist.index,
                        open=hist['Open'], high=hist['High'],
                        low=hist['Low'], close=hist['Close'], name='Price'))
        
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], line=dict(color='#29b6f6', width=1.5), name='SMA 50'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA150'], line=dict(color='#ffab00', width=1.5), name='SMA 150'))
        
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# === עמוד 4: חדשות ===
elif page == "📰 חדשות":
    st.title("חדשות שוק ההון (ישראל)")
    
    if st.button("טען חדשות"):
        with st.spinner("מושך כותרות..."):
            news = get_aggregated_news()
            
            if news:
                col1, col2 = st.columns(2)
                for i, item in enumerate(news):
                    with (col1 if i % 2 == 0 else col2):
                        st.markdown(f"""
                        <div class="news-card">
                            <div style="font-size: 10px; color: #8b949e; text-transform: uppercase;">{item['source']}</div>
                            <a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a>
                            <div class="news-date">{item['published']}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error("לא ניתן למשוך חדשות כרגע (ייתכן חסימת רשת).")
