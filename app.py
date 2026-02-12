import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ta
import feedparser
from datetime import datetime

# --- הגדרת עמוד (חייב להיות ראשון) ---
st.set_page_config(page_title="InvstPro Dashboard", layout="wide", page_icon="📊")

# --- עיצוב מחדש (Custom CSS) ---
st.markdown("""
<style>
    /* שינוי רקע ופונטים */
    .stApp {
        background-color: #0e1117;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* העלמת התפריט של סטרים-ליט */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* עיצוב כרטיסיות (Cards) */
    .metric-card {
        background-color: #1c1c1e;
        border: 1px solid #2c2c2e;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* כותרות */
    h1, h2, h3 { color: #f5f5f7 !important; font-weight: 600; }
    
    /* סרגל צד */
    section[data-testid="stSidebar"] {
        background-color: #151517;
        border-right: 1px solid #2c2c2e;
    }
    
    /* כפתורים */
    .stButton > button {
        width: 100%;
        background-color: #2979ff;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px;
        font-weight: bold;
    }
    .stButton > button:hover { background-color: #2962ff; }
    
    /* טבלאות */
    [data-testid="stDataFrame"] { border: none; }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ליבה (Backend) ---

@st.cache_data(ttl=1800)
def get_hebrew_news():
    """שואב חדשות מביזפורטל"""
    try:
        feed = feedparser.parse("https://www.bizportal.co.il/feed/rss/general")
        return feed.entries[:8]
    except:
        return []

def get_market_data(tickers):
    """מושך נתונים בצורה בטוחה"""
    data = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if len(hist) < 150: continue
            
            # חישוב אינדיקטורים
            curr = hist['Close'].iloc[-1]
            sma150 = ta.trend.sma_indicator(hist['Close'], window=150).iloc[-1]
            rsi = ta.momentum.rsi(hist['Close'], window=14).iloc[-1]
            vol_avg = hist['Volume'].tail(20).mean()
            vol_curr = hist['Volume'].iloc[-1]
            
            # לוגיקת מסחר (האסטרטגיה שלך)
            score = 0
            if curr > sma150: score += 40               # מגמה עולה
            if vol_curr > vol_avg: score += 20          # פריצת ווליום
            if 40 < rsi < 70: score += 20               # מומנטום חיובי אך לא מוגזם
            if curr > hist['Close'].iloc[-5]: score += 20 # מומנטום שבועי
            
            # ניהול סיכונים
            atr = ta.volatility.average_true_range(hist['High'], hist['Low'], hist['Close']).iloc[-1]
            stop_loss = curr - (atr * 1.5)
            target = curr + (atr * 3)
            
            # מידע נוסף לסקטורים
            info = stock.info
            sector = info.get('sector', 'Other')
            mcap = info.get('marketCap', 0)

            data.append({
                "Symbol": ticker,
                "Price": curr,
                "Change": ((curr - hist['Close'].iloc[-2])/hist['Close'].iloc[-2])*100,
                "SMA150": sma150,
                "RSI": rsi,
                "VolRatio": vol_curr / vol_avg,
                "Score": score,
                "StopLoss": stop_loss,
                "Target": target,
                "Sector": sector,
                "MarketCap": mcap
            })
        except: continue
    return pd.DataFrame(data)

# רשימת נכסים (Top 30 Liquidity for speed)
TICKERS = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AMD', 'JPM', 'V', 'LLY', 'AVGO', 'WMT', 'XOM', 'MA', 'UNH', 'PG', 'COST', 'JNJ', 'MRK', 'HD', 'ABBV', 'CVX', 'BAC', 'KO', 'PEP', 'CRM', 'ORCL', 'NFLX', 'INTC']

# --- מבנה האפליקציה (Frontend) ---

# תפריט צד (Sidebar)
with st.sidebar:
    st.title("🚀 InvstPro")
    st.markdown("Professional Terminal")
    st.markdown("---")
    page = st.radio("ניווט במערכת:", ["🏠 דשבורד שוק", "⚡ סורק הזדמנויות", "🔎 ניתוח גרפי", "📰 חדשות ועדכונים"])
    st.markdown("---")
    st.info("System Status: Online 🟢")

# --- עמוד 1: דשבורד שוק (Heatmap & Sectors) ---
if page == "🏠 דשבורד שוק":
    st.title("תמונת מצב יומית (Market Overview)")
    
    if st.button("רענן נתוני שוק"):
        with st.spinner("מעבד נתונים ויזואליים..."):
            df = get_market_data(TICKERS)
            
            if not df.empty:
                # מדדים ראשיים
                col1, col2, col3 = st.columns(3)
                top_gainer = df.loc[df['Change'].idxmax()]
                top_loser = df.loc[df['Change'].idxmin()]
                
                col1.metric("המניה החזקה היום", top_gainer['Symbol'], f"{top_gainer['Change']:.2f}%")
                col2.metric("המניה החלשה היום", top_loser['Symbol'], f"{top_loser['Change']:.2f}%")
                col3.metric("ממוצע RSI שוק", f"{df['RSI'].mean():.1f}")
                
                # מפת חום (Treemap)
                st.subheader("מפת חום (S&P 500 Leaders)")
                fig = px.treemap(df, path=[px.Constant("Market"), 'Sector', 'Symbol'], values='MarketCap',
                                 color='Change', color_continuous_scale=['#ef5350', '#263238', '#66bb6a'],
                                 color_continuous_midpoint=0)
                fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                # ביצועי סקטורים
                st.subheader("ביצועים לפי סקטור")
                sector_perf = df.groupby('Sector')['Change'].mean().reset_index().sort_values('Change')
                fig2 = px.bar(sector_perf, x='Change', y='Sector', orientation='h', color='Change',
                              color_continuous_scale=['#ef5350', '#66bb6a'])
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)

# --- עמוד 2: סורק הזדמנויות (Top 10) ---
elif page == "⚡ סורק הזדמנויות":
    st.title("סורק הזדמנויות מסחר (AI Scanner)")
    st.markdown("""
    האלגוריתם מחפש מניות העונות לקריטריונים:
    1. מחיר מעל ממוצע 150 (מגמה עולה)
    2. ווליום חריג (כניסת כסף)
    3. RSI בטווח בריא (לא קניית יתר)
    """)
    
    if st.button("הפעל סריקה חכמה"):
        with st.spinner("האלגוריתם מנתח את השוק..."):
            df = get_market_data(TICKERS)
            
            # סינון המניות הטובות ביותר (ציון מעל 60)
            opportunities = df[df['Score'] >= 60].sort_values(by='Score', ascending=False)
            
            if not opportunities.empty:
                st.success(f"נמצאו {len(opportunities)} הזדמנויות פוטנציאליות!")
                
                # הצגת הטבלה
                st.dataframe(
                    opportunities[['Symbol', 'Price', 'Change', 'RSI', 'VolRatio', 'StopLoss', 'Target']],
                    column_config={
                        "Price": st.column_config.NumberColumn("מחיר כניסה", format="$%.2f"),
                        "Change": st.column_config.NumberColumn("שינוי יומי", format="%.2f%%"),
                        "RSI": st.column_config.NumberColumn("מומנטום (RSI)", format="%.1f"),
                        "VolRatio": st.column_config.NumberColumn("עוצמת ווליום", format="%.1fx"),
                        "StopLoss": st.column_config.NumberColumn("🔴 Stop Loss", format="$%.2f"),
                        "Target": st.column_config.NumberColumn("🟢 Take Profit", format="$%.2f"),
                    },
                    use_container_width=True,
                    height=500
                )
            else:
                st.warning("השוק חלש כרגע. לא נמצאו מניות שעומדות בכל הקריטריונים המחמירים.")

# --- עמוד 3: ניתוח גרפי ---
elif page == "🔎 ניתוח גרפי":
    st.title("ניתוח טכני מתקדם")
    ticker = st.selectbox("בחר מניה לניתוח:", TICKERS)
    
    if ticker:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        # ממוצעים
        hist['SMA50'] = ta.trend.sma_indicator(hist['Close'], window=50)
        hist['SMA150'] = ta.trend.sma_indicator(hist['Close'], window=150)
        
        # גרף נרות
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=hist.index,
                        open=hist['Open'], high=hist['High'],
                        low=hist['Low'], close=hist['Close'], name='Price'))
        
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], line=dict(color='#29b6f6', width=1.5), name='SMA 50'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA150'], line=dict(color='#ffab00', width=1.5), name='SMA 150'))
        
        fig.update_layout(template="plotly_dark", height=600, title=f"{ticker} Technical Chart", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# --- עמוד 4: חדשות ---
elif page == "📰 חדשות ועדכונים":
    st.title("חדשות כלכליות (ישראל והעולם)")
    
    if st.button("רענן פיד חדשות"):
        news_items = get_hebrew_news()
        
        col1, col2 = st.columns(2)
        
        for i, item in enumerate(news_items):
            with (col1 if i % 2 == 0 else col2):
                st.markdown(f"""
                <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-right: 5px solid #2979ff;">
                    <div style="font-size: 1.1em; font-weight: bold; margin-bottom: 5px;">
                        <a href="{item.link}" target="_blank" style="text-decoration: none; color: white;">{item.title}</a>
                    </div>
                    <div style="font-size: 0.8em; color: #888;">{item.published}</div>
                </div>
                """, unsafe_allow_html=True)
