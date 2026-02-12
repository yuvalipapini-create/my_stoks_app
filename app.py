import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta
import feedparser

# --- הגדרת עמוד (חייב להיות ראשון) ---
st.set_page_config(page_title="Terminal Pro", layout="wide", page_icon="📈")

# --- עיצוב CSS (Dark Mode קריא) ---
st.markdown("""
<style>
    /* רקע ופונטים */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* הסתרת תפריטים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* --- טיקר (פס רץ) --- */
    .ticker-container {
        width: 100%;
        background-color: #000000;
        border-bottom: 2px solid #00ff00;
        overflow: hidden;
        white-space: nowrap;
        padding: 10px 0;
        margin-bottom: 20px;
    }
    .ticker-text {
        display: inline-block;
        font-family: 'Courier New', monospace;
        font-size: 18px;
        color: #00ff00;
        animation: scroll 40s linear infinite;
    }
    @keyframes scroll {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    /* כרטיסי מידע */
    div[data-testid="metric-container"] {
        background-color: #1a1a1a;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 8px;
    }

    /* כפתורים */
    .stButton > button {
        background-color: #2da44e;
        color: white;
        border: none;
        width: 100%;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- פונקציות (Backend) ---

@st.cache_data(ttl=600)
def get_news_google():
    """חדשות מישראל על ארהב"""
    url = "https://news.google.com/rss/search?q=וול+סטריט+OR+מניות&hl=he&gl=IL&ceid=IL:he"
    try:
        feed = feedparser.parse(url)
        return feed.entries[:6]
    except:
        return []

def get_ticker_tape():
    """מייצר את הטקסט לפס הרץ"""
    # נתונים מדומים למהירות, במקרה וה-API נכשל
    default_text = "S&P 500: 5,000 ▲ | NASDAQ: 16,000 ▲ | AAPL: $180 ▲ | TSLA: $200 ▼ | NVDA: $800 ▲ | USD/ILS: 3.65 ₪"
    try:
        # נסיון למשיכה אמיתית
        tickers = ['^GSPC', '^IXIC', 'AAPL', 'NVDA', 'MSFT', 'TSLA']
        data = yf.download(tickers, period="1d", progress=False)
        text = ""
        if not data.empty:
            for t in tickers:
                try:
                    price = data['Close'][t].iloc[-1]
                    change = ((price - data['Open'][t].iloc[0]) / data['Open'][t].iloc[0]) * 100
                    symbol = "▲" if change >= 0 else "▼"
                    text += f"{t}: ${price:.0f} {symbol}{change:.1f}%  |  "
                except: continue
            return text if len(text) > 10 else default_text
    except:
        return default_text
    return default_text

def get_stock_data(symbol):
    """מושך נתונים למניה בודדת"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="1y")
        if len(df) < 50: return None
        
        # חישוב אינדיקטורים
        df['SMA50'] = ta.trend.sma_indicator(df['Close'], window=50)
        df['SMA200'] = ta.trend.sma_indicator(df['Close'], window=200)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        return df
    except:
        return None

# --- ממשק האפליקציה ---

# 1. טיקר עליון (רץ)
tape_text = get_ticker_tape()
st.markdown(f"""
<div class="ticker-container">
    <div class="ticker-text">{tape_text} &nbsp;&nbsp;&nbsp;&nbsp; {tape_text}</div>
</div>
""", unsafe_allow_html=True)

# 2. כותרת ראשית
st.title("🏛️ WALL STREET TERMINAL")

# 3. פריסה ראשית: צד ימין (גרפים), צד שמאל (חדשות)
col_main, col_sidebar = st.columns([3, 1])

# --- צד שמאל: חדשות ---
with col_sidebar:
    st.header("חדשות חמות 📰")
    news_items = get_news_google()
    if news_items:
        for item in news_items:
            st.markdown(f"**[{item.title}]({item.link})**")
            st.caption(f"{item.source.title} | {item.published[:16]}")
            st.markdown("---")
    else:
        st.write("אין חדשות זמינות כרגע.")

# --- צד ימין: גרפים וניתוח ---
with col_main:
    # תיבת בחירה ענקית וברורה
    st.subheader("🔎 בחר מניה לניתוח:")
    selected_stock = st.selectbox(
        "הקלד או בחר מהרשימה:",
        ['AAPL', 'NVDA', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'INTC', 'NFLX', 'COIN'],
        index=0 # ברירת מחדל: אפל
    )

    if selected_stock:
        with st.spinner(f'טוען נתונים עבור {selected_stock}...'):
            df = get_stock_data(selected_stock)
            
            if df is not None:
                # נתונים עדכניים
                last_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                change_pct = ((last_price - prev_price) / prev_price) * 100
                rsi_val = df['RSI'].iloc[-1]
                
                # כרטיסי מידע
                m1, m2, m3 = st.columns(3)
                m1.metric("מחיר אחרון", f"${last_price:.2f}", f"{change_pct:.2f}%")
                m2.metric("RSI (14)", f"{rsi_val:.1f}")
                m3.metric("ווליום", f"{df['Volume'].iloc[-1]/1000000:.1f}M")
                
                # גרף
                st.subheader(f"גרף טכני: {selected_stock}")
                
                fig = go.Figure()
                
                # נרות יפניים
                fig.add_trace(go.Candlestick(x=df.index,
                                open=df['Open'], high=df['High'],
                                low=df['Low'], close=df['Close'],
                                name='Price'))
                
                # ממוצעים נעים
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='cyan', width=1), name='SMA 50'))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='orange', width=2), name='SMA 200'))
                
                fig.update_layout(
                    template="plotly_dark",
                    height=500,
                    xaxis_rangeslider_visible=False,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.error("שגיאה בטעינת הנתונים. נסה מניה אחרת.")
