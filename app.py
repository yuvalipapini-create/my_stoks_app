import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import feedparser
import time

# --- הגדרת עמוד ועיצוב ---
st.set_page_config(page_title="Pro Trader Terminal", layout="wide", page_icon="🏛️")

# CSS מותאם למראה של בית השקעות
st.markdown("""
<style>
    /* כללי */
    .stApp { background-color: #0e1117; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
    
    /* כותרות */
    h1, h2, h3 { color: #00e676 !important; font-weight: 600; text-shadow: 0 0 10px rgba(0, 230, 118, 0.2); }
    
    /* כרטיסי מידע */
    div[data-testid="metric-container"] {
        background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* טבלאות */
    .dataframe { font-size: 12px; }
    
    /* טאבים */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1c1c1c; border-radius: 5px; color: white; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #00e676; color: black; font-weight: bold; }
    
    /* כפתור */
    .stButton > button { background-color: #2962FF; color: white; border-radius: 5px; border: none; font-weight: bold; }
    .stButton > button:hover { background-color: #0039CB; }
</style>
""", unsafe_allow_html=True)

# --- פונקציות עזר (Data Fetching) ---

# 1. חדשות מישראל (RSS)
@st.cache_data(ttl=3600) # מתעדכן כל שעה
def get_hebrew_news():
    # כתובת RSS של ביזפורטל - שוק ההון
    rss_url = "https://www.bizportal.co.il/feed/rss/general"
    feed = feedparser.parse(rss_url)
    news_items = []
    for entry in feed.entries[:8]: # 8 כותרות אחרונות
        news_items.append({"title": entry.title, "link": entry.link, "published": entry.published})
    return news_items

# 2. רשימת S&P 500 (מסוננת למניות נזילות להדגמה)
@st.cache_data
def get_sp500_data():
    # לצורך ביצועים מהירים באפליקציה החינמית, נשתמש ברשימה ידנית של 50 המניות הגדולות והנזילות ביותר
    # במערכת אמיתית היינו מושכים את כל ה-500 מוויקיפדיה
    top_50_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B', 'LLY', 'V', 
        'UNH', 'XOM', 'JNJ', 'JPM', 'MA', 'PG', 'HD', 'MRK', 'CVX', 'ABBV', 
        'PEP', 'KO', 'AVGO', 'COST', 'MCD', 'TMO', 'CSCO', 'ACN', 'ABT', 'LIN',
        'DIS', 'WMT', 'AMD', 'NFLX', 'INTC', 'BA', 'CRM', 'NKE', 'PYPL', 'QCOM',
        'ORCL', 'IBM', 'TXN', 'HON', 'UPS', 'UNP', 'LOW', 'CAT', 'GS', 'MS'
    ]
    return top_50_tickers

# 3. אלגוריתם איתור הזדמנויות (Top 10)
def scan_for_opportunities(tickers):
    opportunities = []
    
    # בר התקדמות
    progress_text = "סורק את השוק אחר הזדמנויות פריצה..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, ticker in enumerate(tickers):
        try:
            stock = yf.Ticker(ticker)
            # אנו צריכים היסטוריה ארוכה לממוצע 150
            hist = stock.history(period="1y")
            
            if len(hist) < 150: continue
            
            current_close = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            sma150 = hist['Close'].rolling(150).mean().iloc[-1]
            avg_volume = hist['Volume'].tail(20).mean()
            current_volume = hist['Volume'].iloc[-1]
            
            # --- הלוגיקה של האלגוריתם ---
            
            # 1. מגמה ראשית: מעל ממוצע 150
            trend_up = current_close > sma150
            
            # 2. "קרוב לממוצע": המחיר לא ברח מדי (עד 15% מעל הממוצע) - הזדמנות כניסה
            dist_from_sma = (current_close / sma150) - 1
            near_support = 0 < dist_from_sma < 0.15 
            
            # 3. ווליום חזק: מעל הממוצע
            volume_spike = current_volume > avg_volume
            
            # 4. מומנטום יומי חיובי
            green_day = current_close > prev_close
            
            if trend_up and near_support and green_day:
                # חישוב ניהול סיכונים
                # סטופ לוס: הנמוך של 5 הימים האחרונים
                recent_low = hist['Low'].tail(5).min()
                stop_loss = recent_low * 0.99 # אחוז מתחת לנמוך
                
                # יעד רווח: יחס סיכון/סיכוי של 1:2
                risk = current_close - stop_loss
                target = current_close + (risk * 2)
                
                opportunities.append({
                    "Symbol": ticker,
                    "Price": current_close,
                    "Change %": ((current_close - prev_close)/prev_close)*100,
                    "SMA 150": sma150,
                    "Volume Ratio": current_volume / avg_volume,
                    "Entry": current_close,
                    "Stop Loss": stop_loss,
                    "Target": target
                })
        except:
            pass
            
        # עדכון בר
        my_bar.progress((i + 1) / len(tickers), text=progress_text)
        
    my_bar.empty()
    
    # מיון לפי עוצמת הווליום (הכי הרבה עניין)
    df = pd.DataFrame(opportunities)
    if not df.empty:
        df = df.sort_values(by="Volume Ratio", ascending=False).head(10) # 10 המובילות
    return df

# --- מבנה האתר ---

st.title("🏛️ INVESTMENT HOUSE | PRO TERMINAL")
st.markdown("מערכת ניהול השקעות וניתוח שוק בזמן אמת")

# יצירת טאבים
tab1, tab2, tab3, tab4 = st.tabs(["🔥 Top 10 Picks", "🌍 מפת שוק וסקטורים", "📊 ניתוח מניה", "📰 עדכוני חדשות"])

# --- TAB 1: עשרת הגדולים ---
with tab1:
    st.header("⚡ מניות לפריצה וטרייד יומי")
    st.markdown("האלגוריתם סורק מניות במגמה עולה שנמצאות בנקודת כניסה נוחה (קרוב לממוצע 150) עם ווליום חריג.")
    
    if st.button("🚀 הרץ סריקת הזדמנויות (Top 10)"):
        tickers = get_sp500_data()
        df_ops = scan_for_opportunities(tickers)
        
        if not df_ops.empty:
            st.success(f"נמצאו {len(df_ops)} מניות העונות לקריטריונים!")
            
            # הצגת הטבלה בעיצוב מיוחד
            st.dataframe(
                df_ops.style.format({
                    "Price": "${:.2f}", 
                    "SMA 150": "${:.2f}",
                    "Change %": "{:+.2f}%",
                    "Volume Ratio": "{:.2f}x",
                    "Entry": "${:.2f}",
                    "Stop Loss": "${:.2f}",
                    "Target": "${:.2f}"
                }).background_gradient(subset=['Volume Ratio'], cmap='Greens'),
                use_container_width=True,
                height=400
            )
            
            st.info("💡 **Entry:** מחיר כניסה מומלץ | **Stop Loss:** שבירה של נמוך שבועי | **Target:** יעד רווח ביחס סיכון 1:2")
        else:
            st.warning("לא נמצאו מניות העונות לכל הקריטריונים הקשוחים כרגע. השוק אולי במצב המתנה.")

# --- TAB 2: מפת חום וסקטורים ---
with tab2:
    st.header("🗺️ תמונת מצב יומית (S&P 500 Heatmap)")
    
    if st.button("טען נתוני שוק"):
        with st.spinner("מעבד נתונים ויזואליים..."):
            tickers = get_sp500_data()
            market_data = []
            
            for t in tickers:
                try:
                    s = yf.Ticker(t)
                    info = s.info
                    hist = s.history(period="2d")
                    if len(hist) > 1:
                        change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                        market_data.append({
                            "Ticker": t,
                            "Sector": info.get('sector', 'Unknown'),
                            "Market Cap": info.get('marketCap', 0),
                            "Change": change
                        })
                except: pass
            
            df_mkt = pd.DataFrame(market_data)
            
            # 1. גרף השוואת סקטורים
            st.subheader("📊 ביצועי סקטורים היום")
            sector_perf = df_mkt.groupby("Sector")['Change'].mean().reset_index().sort_values("Change")
            
            fig_sec = px.bar(sector_perf, x='Change', y='Sector', orientation='h', 
                             color='Change', color_continuous_scale=['red', 'black', 'green'],
                             title="ממוצע שינוי יומי לפי סקטור")
            fig_sec.update_layout(template="plotly_dark")
            st.plotly_chart(fig_sec, use_container_width=True)
            
            # 2. Treemap (מפת חום)
            st.subheader("🔥 מפת חום לפי שווי שוק")
            fig_tree = px.treemap(df_mkt, path=[px.Constant("S&P 500"), 'Sector', 'Ticker'], values='Market Cap',
                                  color='Change', color_continuous_scale=['red', 'black', 'green'],
                                  color_continuous_midpoint=0)
            fig_tree.update_layout(template="plotly_dark", margin=dict(t=50, l=25, r=25, b=25))
            st.plotly_chart(fig_tree, use_container_width=True)

# --- TAB 3: ניתוח מניה ספציפי ---
with tab3:
    st.header("🔎 חדר ניתוח (Deep Dive)")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        ticker = st.text_input("הכנס סימול (למשל NVDA):", "NVDA").upper()
        if st.button("נתח מניה"):
            st.session_state['analyzed_ticker'] = ticker
            
    if 'analyzed_ticker' in st.session_state:
        t = st.session_state['analyzed_ticker']
        stock = yf.Ticker(t)
        hist = stock.history(period="2y")
        info = stock.info
        
        # כרטיסי מידע
        c1, c2, c3, c4 = st.columns(4)
        current_price = hist['Close'].iloc[-1]
        c1.metric("מחיר", f"${current_price:.2f}")
        c2.metric("P/E Ratio", info.get('forwardPE', 'N/A'))
        c3.metric("52W High", f"${info.get('fiftyTwoWeekHigh', 0)}")
        c4.metric("Analyst Target", f"${info.get('targetMeanPrice', 'N/A')}")
        
        # גרף טכני
        hist['SMA50'] = hist['Close'].rolling(50).mean()
        hist['SMA150'] = hist['Close'].rolling(150).mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='Price', line=dict(color='#00e676')))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name='SMA 50', line=dict(color='#29b6f6', width=1)))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA150'], name='SMA 150', line=dict(color='#ffab00', width=2, dash='dash')))
        
        fig.update_layout(title=f"{t} - מגמה ורמות תמיכה", template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 4: חדשות ---
with tab4:
    st.header("📰 חדר חדשות - כלכלה גלובלית")
    
    if st.button("רענן חדשות"):
        news = get_hebrew_news()
        for item in news:
            st.markdown(f"""
            <div style="background-color: #262626; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-right: 5px solid #00e676;">
                <h4 style="margin:0;"><a href="{item['link']}" target="_blank" style="text-decoration:none; color:white;">{item['title']}</a></h4>
                <p style="color:#888; font-size:12px; margin-top:5px;">{item['published']}</p>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #555;'>Developed for Investment Analysis | Data by Yahoo Finance</div>", unsafe_allow_html=True)
