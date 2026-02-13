import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import feedparser
from datetime import datetime, timedelta

# --- הגדרת עמוד (Page Config) ---
st.set_page_config(
    page_title="AlphaTrade Pro",
    layout="wide",
    page_icon="💎",
    initial_sidebar_state="collapsed"
)

# --- עיצוב מתקדם (Custom CSS) ---
# עיצוב בסגנון Glassmorphism מודרני
st.markdown("""
<style>
    /* רקע כללי עם גרדיאנט עדין */
    .stApp {
        background: linear-gradient(to bottom right, #0f172a, #1e1b4b);
        color: #e2e8f0;
    }
    
    /* כותרות זוהרות */
    h1, h2, h3 {
        color: #38bdf8 !important;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 700;
        text-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
    }
    
    /* כרטיסיות זכוכית */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border-color: #38bdf8;
    }
    
    /* טאבים מעוצבים */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        color: #94a3b8;
        padding: 10px 20px;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(56, 189, 248, 0.1);
        color: #38bdf8;
        border-color: #38bdf8;
        font-weight: bold;
    }
    
    /* כפתורים */
    .stButton > button {
        background: linear-gradient(90deg, #3b82f6, #2563eb);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: bold;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }
    .stButton > button:hover {
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ליבה (Robust Functions) ---

@st.cache_data(ttl=1800) # מטמון לחצי שעה
def get_news():
    """שואב חדשות מביזפורטל עם הגנה מקריסות"""
    try:
        rss_url = "https://www.bizportal.co.il/feed/rss/general"
        feed = feedparser.parse(rss_url)
        return [{"title": e.title, "link": e.link, "date": e.published[:16]} for e in feed.entries[:6]]
    except:
        return []

def calculate_rsi(data, window=14):
    """חישוב מדד RSI לזיהוי קניית/מכירת יתר"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_market_data_safe(tickers):
    """מושך נתונים בצורה בטוחה שלא תקריס את האפליקציה"""
    data = []
    
    # שימוש ב-download של yfinance שהוא מהיר פי 100 מלולאה
    try:
        df_history = yf.download(tickers, period="6mo", group_by='ticker', progress=False, threads=True)
    except Exception as e:
        st.error(f"שגיאת תקשורת עם הבורסה: {e}")
        return pd.DataFrame()

    for ticker in tickers:
        try:
            # חילוץ נתונים לכל מניה מהדאטה הגדול
            if len(tickers) > 1:
                hist = df_history[ticker]
            else:
                hist = df_history
            
            # ניקוי שורות ריקות
            hist = hist.dropna()
            
            if len(hist) < 150: continue

            # חישובים
            curr_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            sma150 = hist['Close'].rolling(150).mean().iloc[-1]
            sma50 = hist['Close'].rolling(50).mean().iloc[-1]
            volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].tail(20).mean()
            
            # בדיקת RSI
            rsi = calculate_rsi(hist).iloc[-1]

            # לוגיקת האיתות (האלגוריתם שלך)
            score = 0
            if curr_price > sma150: score += 30      # מגמה ראשית
            if curr_price > sma50: score += 20       # מגמה משנית
            if volume > avg_volume * 1.2: score += 20 # פריצת ווליום
            if 30 < rsi < 70: score += 15            # RSI בריא
            if curr_price > prev_price: score += 15  # מומנטום חיובי

            # משיכת סקטור (בצורה שלא תקרוס)
            try:
                info = yf.Ticker(ticker).info
                sector = info.get('sector', 'General')
                mcap = info.get('marketCap', 0)
            except:
                sector = 'General'
                mcap = 0

            data.append({
                "Symbol": ticker,
                "Price": curr_price,
                "Change%": ((curr_price - prev_price) / prev_price) * 100,
                "SMA150": sma150,
                "Dist_SMA": ((curr_price / sma150) - 1) * 100,
                "Volume_Ratio": volume / avg_volume,
                "RSI": rsi,
                "Score": score,
                "Sector": sector,
                "MarketCap": mcap
            })
        except:
            continue
            
    return pd.DataFrame(data)

# רשימת מניות קבועה (S&P 50 Top Liquidity) לביצועים מהירים
TICKERS = [
    'NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AMD', 'NFLX', 'INTC',
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'V', 'MA', 'AXP', 'PYPL',
    'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PFE', 'JNJ', 'LLY', 'MRK', 'ABBV',
    'KO', 'PEP', 'MCD', 'SBUX', 'WMT', 'COST', 'TGT', 'HD', 'LOW', 'NKE',
    'BA', 'CAT', 'DE', 'GE', 'HON', 'MMM', 'UPS', 'FDX', 'UNP', 'LMT'
]

# --- ממשק האפליקציה ---

st.title("💎 AlphaTrade | Elite Terminal")
st.markdown("### פלטפורמת ניתוח שוק מבוססת אלגוריתמים")

# תפריט ראשי
tabs = st.tabs(["🚀 Top Picks (AI)", "🌍 Market Heatmap", "📈 Pro Charts", "📰 News Feed"])

# --- TAB 1: המניות החמות (AI Picks) ---
with tabs[0]:
    st.markdown("#### ⚡ איתותי קנייה מערכתיים (Top Opportunities)")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("האלגוריתם מחפש שילוב של מגמה עולה (SMA150), פריצת ווליום ומומנטום חיובי.")
    with col2:
        run_scan = st.button("🔄 הרץ סריקה בזמן אמת")

    if run_scan:
        with st.spinner("🤖 ה-AI סורק את השוק, מנתח ווליום ואינדיקטורים..."):
            df = get_market_data_safe(TICKERS)
            
            if not df.empty:
                # סינון המניות הטובות ביותר
                best_picks = df[df['Score'] >= 70].sort_values(by='Score', ascending=False).head(10)
                
                # הצגת המדדים המרכזיים
                top_stock = best_picks.iloc[0]
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Top Pick", top_stock['Symbol'], f"{top_stock['Change%']:.2f}%")
                m2.metric("Signal Score", int(top_stock['Score']))
                m3.metric("RSI Status", f"{int(top_stock['RSI'])}")
                m4.metric("Volume Spike", f"{top_stock['Volume_Ratio']:.1f}x")

                # טבלה מעוצבת ומקצועית
                st.dataframe(
                    best_picks[['Symbol', 'Price', 'Change%', 'RSI', 'Volume_Ratio', 'Dist_SMA', 'Score']],
                    column_config={
                        "Price": st.column_config.NumberColumn("מחיר ($)", format="$%.2f"),
                        "Change%": st.column_config.NumberColumn("שינוי יומי", format="%.2f%%"),
                        "RSI": st.column_config.ProgressColumn("RSI Momentum", min_value=0, max_value=100, format="%d"),
                        "Volume_Ratio": st.column_config.NumberColumn("יחס ווליום", format="%.1fx"),
                        "Dist_SMA": st.column_config.NumberColumn("מרחק מממוצע 150", format="%.1f%%"),
                        "Score": st.column_config.ProgressColumn("ציון AI", min_value=0, max_value=100, format="%d"),
                    },
                    use_container_width=True,
                    height=450
                )
            else:
                st.error("לא התקבלו נתונים. נסה שוב בעוד מספר שניות.")

# --- TAB 2: מפת חום (Heatmap) ---
with tabs[1]:
    st.markdown("#### 🗺️ מיפוי סקטורים חכם")
    if st.button("טען מפת שוק"):
        with st.spinner("בונה ויזואליזציה..."):
            df_heat = get_market_data_safe(TICKERS)
            if not df_heat.empty:
                # Treemap מתקדם
                fig = px.treemap(
                    df_heat, 
                    path=[px.Constant("S&P 50 Top Liquidity"), 'Sector', 'Symbol'], 
                    values='MarketCap',
                    color='Change%',
                    color_continuous_scale=['#ff4d4d', '#1e1e1e', '#00e676'], # אדום-שחור-ירוק
                    color_continuous_midpoint=0,
                    hover_data=['Price', 'RSI']
                )
                fig.update_layout(
                    margin=dict(t=30, l=10, r=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white')
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("אין מספיק נתונים ליצירת המפה כרגע.")

# --- TAB 3: גרפים לניתוח (Charts) ---
with tabs[2]:
    st.markdown("#### 🔎 חדר ניתוח טכני")
    selected_ticker = st.selectbox("בחר מניה לניתוח עומק:", TICKERS)
    
    if selected_ticker:
        stock = yf.Ticker(selected_ticker)
        hist = stock.history(period="1y")
        
        # חישוב אינדיקטורים לגרף
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA150'] = hist['Close'].rolling(window=150).mean()
        
        # גרף נרות יפניים (Candlestick) - הסטנדרט המקצועי
        fig = go.Figure()
        
        # הוספת הנרות
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'], high=hist['High'],
            low=hist['Low'], close=hist['Close'],
            name='Price'
        ))
        
        # הוספת ממוצעים
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], line=dict(color='#29b6f6', width=1.5), name='SMA 50'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA150'], line=dict(color='#ffab00', width=1.5, dash='dash'), name='SMA 150'))
        
        # עיצוב הגרף
        fig.update_layout(
            title=f"{selected_ticker} - Technical Analysis",
            template="plotly_dark",
            height=600,
            xaxis_rangeslider_visible=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Gauge Meter (RSI) - בונוס
        curr_rsi = calculate_rsi(hist).iloc[-1]
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = curr_rsi,
            title = {'text': "RSI Momentum"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "#38bdf8"},
                'steps': [
                    {'range': [0, 30], 'color': "rgba(0, 230, 118, 0.3)"}, # אזור קנייה
                    {'range': [30, 70], 'color': "rgba(255, 255, 255, 0.1)"},
                    {'range': [70, 100], 'color': "rgba(255, 23, 68, 0.3)"} # אזור מכירה
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': curr_rsi
                }
            }
        ))
        fig_gauge.update_layout(height=300, margin=dict(t=50,b=10,l=30,r=30), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
        st.plotly_chart(fig_gauge, use_container_width=True)

# --- TAB 4: חדשות (News) ---
with tabs[3]:
    st.markdown("#### 📰 עדכונים בזמן אמת (Bizportal)")
    if st.button("רענן פיד חדשות"):
        news_items = get_news()
        if news_items:
            for item in news_items:
                st.markdown(f"""
                <div style="
                    background: rgba(255,255,255,0.05); 
                    padding: 15px; 
                    border-radius: 10px; 
                    border-right: 4px solid #38bdf8; 
                    margin-bottom: 12px;">
                    <a href="{item['link']}" target="_blank" style="text-decoration: none; color: white; font-weight: bold; font-size: 1.1em;">
                        {item['title']}
                    </a>
                    <div style="color: #94a3b8; font-size: 0.85em; margin-top: 5px;">📅 {item['date']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("לא נמצאו חדשות חדשות כרגע.")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.8em;'>Built with ❤️ for Professional Traders</div>", unsafe_allow_html=True)

