import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta
import feedparser
import time

# --- 1. הגדרת עמוד (חייב להיות ראשון) ---
st.set_page_config(page_title="ProTrade Ultimate", layout="wide", page_icon="🦁")

# --- 2. עיצוב Glassmorphism יוקרתי (CSS) ---
st.markdown("""
<style>
    /* פונטים ורקע */
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    .stApp {
        background: radial-gradient(circle at center, #1a1c29 0%, #0d0e12 100%);
        color: #ffffff;
        font-family: 'Assistant', sans-serif;
    }

    /* הסתרת תפריטים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* --- טיקר (פס רץ) --- */
    .ticker-wrap {
        width: 100%;
        background: rgba(0, 255, 136, 0.05);
        border-bottom: 1px solid rgba(0, 255, 136, 0.2);
        overflow: hidden;
        white-space: nowrap;
        padding: 10px 0;
        margin-bottom: 20px;
    }
    .ticker {
        display: inline-block;
        animation: marquee 45s linear infinite;
        font-size: 18px;
        font-weight: bold;
        color: #00ff88;
    }
    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* --- כרטיסיות זכוכית --- */
    div[data-testid="metric-container"], .card-box {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        transition: 0.3s;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #00ff88;
        transform: translateY(-3px);
    }

    /* כפתורים */
    .stButton > button {
        background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
        color: #000;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 12px;
        width: 100%;
        transition: 0.2s;
    }
    .stButton > button:hover {
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
        color: white;
    }
    
    /* טבלאות */
    .stDataFrame { border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- 3. פונקציות ליבה (Robust Backend) ---

def get_fallback_ticker():
    """מחזיר מחרוזת טיקר גם אם אין אינטרנט"""
    return "🍏 AAPL: $185.20 ▲ | 🤖 NVDA: $790.50 ▲ | 🚗 TSLA: $195.00 ▼ | ☁️ AMZN: $175.30 ▲ | 💻 MSFT: $410.00 ▲ | ₿ BTC: $62,000 ▲"

@st.cache_data(ttl=60) # מתעדכן כל דקה
def get_real_ticker():
    """מנסה להביא נתונים אמיתיים, אם נכשל חוזר לברירת מחדל"""
    try:
        tickers = ['^GSPC', '^IXIC', 'NVDA', 'AAPL', 'TSLA', 'BTC-USD']
        data = yf.download(tickers, period="1d", progress=False)
        text = ""
        for t in tickers:
            try:
                # טיפול דינמי במבנה הנתונים של yfinance
                if len(tickers) > 1:
                    price = data['Close'][t].iloc[-1]
                    prev = data['Open'][t].iloc[0]
                else:
                    price = data['Close'].iloc[-1]
                    prev = data['Open'].iloc[0]
                
                change = ((price - prev) / prev) * 100
                symbol = "▲" if change >= 0 else "▼"
                text += f"{t.replace('^','').replace('-USD','')}: ${price:,.0f} {symbol}{change:.1f}%   |   "
            except: continue
        return text if len(text) > 10 else get_fallback_ticker()
    except:
        return get_fallback_ticker()

def get_stock_details(symbol):
    """מביא נתונים למניה בודדת ללא Cache כדי לקבל עדכון מיידי"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="1y")
        
        if df.empty: return None

        # חישוב אינדיקטורים קריטיים
        df['SMA50'] = ta.trend.sma_indicator(df['Close'], window=50)
        df['SMA200'] = ta.trend.sma_indicator(df['Close'], window=200)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        
        return df
    except Exception as e:
        return None

def get_news():
    """חדשות מישראל"""
    try:
        # גוגל ניוז - הכי אמין
        rss = "https://news.google.com/rss/search?q=שוק+ההון+בורסה&hl=he&gl=IL&ceid=IL:he"
        feed = feedparser.parse(rss)
        return feed.entries[:5]
    except:
        return []

# --- 4. ממשק משתמש (UI) ---

# --- חלק עליון: טיקר ---
ticker_text = get_real_ticker()
st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker">{ticker_text} &nbsp;&nbsp;&nbsp; {ticker_text}</div>
</div>
""", unsafe_allow_html=True)

# כותרת
col_logo, col_title = st.columns([1, 5])
with col_title:
    st.title("PRO TRADE TERMINAL")
    st.caption("מערכת מסחר וניתוח בזמן אמת")

# --- גוף האפליקציה ---
tabs = st.tabs(["🔎 חדר מסחר (Charts)", "🚀 סורק פריצות (Scanner)", "📰 חדשות (News)"])

# === TAB 1: חדר מסחר ===
with tabs[0]:
    # בחירת מניה
    c_sel, c_info = st.columns([1, 3])
    with c_sel:
        st.subheader("בחר נכס")
        symbol = st.selectbox(
            "רשימת מעקב:",
            ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'INTC', 'BTC-USD'],
            index=0
        )
        if st.button("🔄 רענן נתונים"):
            st.rerun()

    # משיכת נתונים
    df = get_stock_details(symbol)

    if df is not None:
        curr = df['Close'].iloc[-1]
        change = ((curr - df['Open'].iloc[-1]) / df['Open'].iloc[-1]) * 100
        rsi = df['RSI'].iloc[-1]
        vol = df['Volume'].iloc[-1]

        # כרטיסי מידע
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("מחיר אחרון", f"${curr:,.2f}", f"{change:.2f}%")
        m2.metric("RSI (מומנטום)", f"{rsi:.1f}", "Overbought" if rsi>70 else "Oversold" if rsi<30 else "Neutral")
        m3.metric("SMA 200 (מגמה)", f"${df['SMA200'].iloc[-1]:.2f}", "Bullish" if curr > df['SMA200'].iloc[-1] else "Bearish")
        m4.metric("ווליום", f"{vol/1000000:.1f}M")

        # גרף
        st.markdown("---")
        fig = go.Figure()
        
        # נרות
        fig.add_trace(go.Candlestick(x=df.index,
                        open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'],
                        name='Price'))
        
        # ממוצעים
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#00ff88', width=1.5), name='SMA 50'))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='#ff0055', width=1.5), name='SMA 200'))

        fig.update_layout(
            template="plotly_dark",
            height=600,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_rangeslider_visible=False,
            title=f"Technical Chart: {symbol}"
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error(f"שגיאה במשיכת נתונים עבור {symbol}. ייתכן והבורסה סגורה או שיש עומס.")

# === TAB 2: סורק פריצות ===
with tabs[1]:
    st.header("⚡ סורק הזדמנויות (Top 10 Liquidity)")
    st.markdown("סורק זה בודק את המניות הגדולות ביותר כדי למנוע קריסות.")
    
    if st.button("🚀 הפעל סריקה"):
        with st.spinner("מנתח שוק..."):
            # רשימה מצומצמת אך איכותית כדי למנוע קריסות
            scan_tickers = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AMD', 'JPM', 'V']
            results = []
            
            # הורדה קבוצתית מהירה
            try:
                data = yf.download(scan_tickers, period="6mo", group_by='ticker', progress=False)
                
                for t in scan_tickers:
                    try:
                        stock_df = data[t].dropna()
                        if len(stock_df) < 50: continue
                        
                        curr_p = stock_df['Close'].iloc[-1]
                        sma50 = ta.trend.sma_indicator(stock_df['Close'], window=50).iloc[-1]
                        rsi_val = ta.momentum.rsi(stock_df['Close'], window=14).iloc[-1]
                        
                        # לוגיקה
                        status = "Neutral"
                        score = 0
                        if curr_p > sma50: score += 1
                        if rsi_val < 70 and rsi_val > 50: score += 1
                        
                        if score == 2: status = "Strong Buy"
                        elif score == 1: status = "Watchlist"
                        
                        results.append({
                            "Symbol": t,
                            "Price": curr_p,
                            "RSI": rsi_val,
                            "Status": status
                        })
                    except: continue
                
                if results:
                    res_df = pd.DataFrame(results).sort_values(by="RSI", ascending=False)
                    st.dataframe(
                        res_df.style.format({"Price": "${:.2f}", "RSI": "{:.1f}"})
                        .applymap(lambda v: 'color: #00ff88; font-weight: bold' if v == 'Strong Buy' else '', subset=['Status']),
                        use_container_width=True
                    )
                else:
                    st.warning("לא נמצאו נתונים.")
            except Exception as e:
                st.error(f"שגיאת תקשורת: {e}")

# === TAB 3: חדשות ===
with tabs[2]:
    st.header("חדשות חמות מישראל")
    if st.button("רענן חדשות"):
        news_items = get_news()
        if news_items:
            c1, c2 = st.columns(2)
            for i, item in enumerate(news_items):
                with (c1 if i % 2 == 0 else c2):
                    st.markdown(f"""
                    <div class="card-box" style="margin-bottom:10px;">
                        <a href="{item.link}" target="_blank" style="color:#00ff88; font-weight:bold; text-decoration:none;">
                            {item.title}
                        </a>
                        <div style="font-size:12px; color:#aaa; margin-top:5px;">{item.published}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("לא נמצאו חדשות זמינות.")
