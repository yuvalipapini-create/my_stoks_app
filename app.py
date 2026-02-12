import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta
import feedparser

# --- הגדרת עמוד (חייב להיות ראשון) ---
st.set_page_config(page_title="Pro Breakout Terminal", layout="wide", page_icon="🚀")

# --- עיצוב CSS (Dark Mode + Ticker Fix) ---
st.markdown("""
<style>
    /* רקע שחור */
    .stApp { background-color: #080808; color: #e0e0e0; }
    
    /* הסתרת תפריטים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* --- תיקון הפס הרץ (Ticker) --- */
    .ticker-container {
        width: 100%;
        height: 50px;
        background-color: #000;
        border-bottom: 2px solid #00ff41;
        border-top: 1px solid #333;
        overflow: hidden;
        white-space: nowrap;
        position: relative;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .ticker-text {
        display: inline-block;
        font-family: 'Courier New', monospace;
        font-size: 18px;
        font-weight: bold;
        color: #00ff41;
        padding-top: 12px;
        animation: scroll-left 25s linear infinite; /* אנימציה רציפה */
    }
    @keyframes scroll-left {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    .ticker-container:hover .ticker-text {
        animation-play-state: paused; /* עוצר במעבר עכבר */
    }

    /* כרטיסיות */
    div[data-testid="metric-container"] {
        background-color: #111;
        border: 1px solid #333;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #00ff41;
    }
    
    /* טבלאות */
    .stDataFrame { border: 1px solid #333; }
    
    /* כפתורים */
    .stButton > button {
        background-color: #00ff41;
        color: black;
        font-weight: bold;
        border: none;
    }
    .stButton > button:hover { background-color: #00cc33; }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ליבה ---

@st.cache_data(ttl=600)
def get_google_news_us_hebrew():
    """חדשות כלכליות מארהב בעברית"""
    url = "https://news.google.com/rss/search?q=וול+סטריט+OR+נאסדק+OR+הפדרל+ריזרב&hl=he&gl=IL&ceid=IL:he"
    try:
        feed = feedparser.parse(url)
        return feed.entries[:5]
    except: return []

def get_ticker_string():
    """יוצר מחרוזת לטיקר"""
    # סמלים של מדדים וקריפטו
    symbols = ['^GSPC', '^IXIC', 'BTC-USD', 'ETH-USD', 'NVDA', 'TSLA', 'AAPL']
    display_map = {'^GSPC': 'S&P500', '^IXIC': 'NASDAQ', 'BTC-USD': 'BITCOIN'}
    
    text_parts = []
    try:
        data = yf.download(symbols, period="1d", progress=False)
        for sym in symbols:
            try:
                # טיפול במבנה הנתונים של yfinance (לפעמים רב-שכבתי)
                if len(symbols) > 1:
                    price = data['Close'][sym].iloc[-1]
                    prev = data['Open'][sym].iloc[0]
                else:
                    price = data['Close'].iloc[-1]
                    prev = data['Open'].iloc[0]
                
                change = ((price - prev) / prev) * 100
                arrow = "▲" if change >= 0 else "▼"
                name = display_map.get(sym, sym)
                text_parts.append(f"{name}: ${price:,.2f} ({arrow}{change:.2f}%)")
            except: continue
    except:
        return "LOADING MARKET DATA... PLEASE WAIT..."
        
    return "  |  ".join(text_parts) * 5 # שכפול לאורך

# --- הפונקציה החשובה: סורק הפריצות ---
def run_breakout_scanner():
    # רשימת 30 המניות הנזילות ביותר (אפשר להרחיב ל-500 אבל זה יקח זמן)
    tickers = [
        'NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AMD', 'JPM', 'V', 
        'LLY', 'AVGO', 'WMT', 'XOM', 'MA', 'PG', 'COST', 'JNJ', 'HD', 'CVX', 
        'BAC', 'KO', 'PEP', 'NFLX', 'INTC', 'CRM', 'ORCL', 'QCOM', 'LIN', 'ADBE'
    ]
    
    results = []
    
    # הורדה במכה אחת (הרבה יותר מהר)
    data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
    
    for t in tickers:
        try:
            df = data[t].dropna()
            if len(df) < 150: continue
            
            # 1. חישוב אינדיקטורים
            curr_price = df['Close'].iloc[-1]
            sma150 = ta.trend.sma_indicator(df['Close'], window=150).iloc[-1]
            sma50 = ta.trend.sma_indicator(df['Close'], window=50).iloc[-1]
            rsi = ta.momentum.rsi(df['Close'], window=14).iloc[-1]
            
            vol_curr = df['Volume'].iloc[-1]
            vol_avg = df['Volume'].tail(20).mean()
            
            # 2. בדיקת הקריטריונים שלך (Strict Criteria)
            
            # א. מגמה עולה: מחיר מעל ממוצע 150
            cond_trend = curr_price > sma150
            
            # ב. ווליום חזק: לפחות 20% מעל הממוצע (פריצה)
            cond_vol = vol_curr > (vol_avg * 1.2)
            
            # ג. RSI: לא קניית יתר קיצונית (מתחת ל-75) אבל חיובי (מעל 50)
            cond_rsi = 50 < rsi < 75
            
            # ד. קרוב לממוצע (לא ברח מדי) - עד 15% מעל ממוצע 50
            dist_from_sma50 = ((curr_price / sma50) - 1) * 100
            cond_near = dist_from_sma50 < 15
            
            # חישוב ציון התאמה
            score = 0
            if cond_trend: score += 1
            if cond_vol: score += 1
            if cond_rsi: score += 1
            if cond_near: score += 1
            
            # אם עומד ברוב התנאים - הוסף לרשימה
            if score >= 3:
                # חישוב יעדים
                atr = ta.volatility.average_true_range(df['High'], df['Low'], df['Close']).iloc[-1]
                stop = curr_price - (atr * 2)
                target = curr_price + (atr * 4)
                
                results.append({
                    "Symbol": t,
                    "Price": curr_price,
                    "Change": ((curr_price - df['Close'].iloc[-2])/df['Close'].iloc[-2])*100,
                    "Vol Ratio": vol_curr / vol_avg,
                    "RSI": rsi,
                    "Stop Loss": stop,
                    "Target": target,
                    "Reason": "Volume Breakout" if cond_vol else "Trend Following"
                })
        except: continue
        
    return pd.DataFrame(results)

# --- ממשק משתמש ---

# 1. טיקר עליון
ticker_html = get_ticker_string()
st.markdown(f"""
<div class="ticker-container">
    <div class="ticker-text">{ticker_html}</div>
</div>
""", unsafe_allow_html=True)

st.title("⚡ PRO BREAKOUT TERMINAL")

# טאבים
tab_scanner, tab_chart, tab_news = st.tabs(["🚀 סורק פריצות (Top 10)", "📊 ניתוח גרפי", "📰 חדשות ארה\"ב"])

# --- טאב 1: סורק הפריצות ---
with tab_scanner:
    st.header("איתור מניות לפריצה (Breakout Scanner)")
    st.markdown("""
    **קריטריונים לסריקה:**
    * ✅ מגמה עולה (מעל ממוצע 150)
    * ✅ ווליום חריג (כניסת כסף חכם)
    * ✅ פוטנציאל רווח (RSI לא בשמיים)
    """)
    
    if st.button("🔎 הרץ סריקת שוק עכשיו"):
        with st.spinner("סורק את השוק אחר הזדמנויות..."):
            df_scan = run_breakout_scanner()
            
            if not df_scan.empty:
                # מיון לפי יחס ווליום (הכי הרבה כסף נכנס)
                df_scan = df_scan.sort_values(by="Vol Ratio", ascending=False).head(10)
                
                st.success(f"נמצאו {len(df_scan)} מניות בפריצה!")
                
                st.dataframe(
                    df_scan.style.format({
                        "Price": "${:.2f}",
                        "Change": "{:+.2f}%",
                        "Vol Ratio": "{:.1f}x",
                        "RSI": "{:.0f}",
                        "Stop Loss": "${:.2f}",
                        "Target": "${:.2f}"
                    }).background_gradient(subset=['Vol Ratio'], cmap='Greens'),
                    use_container_width=True,
                    height=500
                )
            else:
                st.warning("לא נמצאו מניות העונות לקריטריונים המחמירים כרגע. השוק במצב המתנה.")

# --- טאב 2: גרפים ---
with tab_chart:
    st.header("ניתוח טכני")
    symbol = st.selectbox("בחר מניה:", ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'AMD', 'AMZN', 'GOOGL'])
    
    if symbol:
        stock = yf.Ticker(symbol)
        df = stock.history(period="1y")
        
        # אינדיקטורים לגרף
        df['SMA150'] = ta.trend.sma_indicator(df['Close'], window=150)
        df['SMA50'] = ta.trend.sma_indicator(df['Close'], window=50)
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA150'], line=dict(color='orange', width=2), name='SMA 150'))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='cyan', width=1), name='SMA 50'))
        
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# --- טאב 3: חדשות ---
with tab_news:
    st.header("עדכונים מוול-סטריט (עברית)")
    news = get_google_news_us_hebrew()
    if news:
        col1, col2 = st.columns(2)
        for i, item in enumerate(news):
            with (col1 if i%2==0 else col2):
                st.markdown(f"""
                <div style="background:#111; padding:15px; margin-bottom:10px; border-radius:5px; border-left:3px solid #00ff41;">
                    <a href="{item.link}" target="_blank" style="color:white; font-weight:bold; text-decoration:none;">{item.title}</a>
                    <div style="color:#666; font-size:12px; margin-top:5px;">{item.source} | {item.published[:16]}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("טוען חדשות...")
