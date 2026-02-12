import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- הגדרת העמוד (חובה בהתחלה) ---
st.set_page_config(page_title="Pro Stock Terminal", layout="wide", page_icon="📈")

# --- עיצוב CSS למראה יוקרתי (Dark Mode) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    h1, h2, h3 { color: #00e676 !important; }
    div[data-testid="metric-container"] {
        background-color: #1c1c1c; border: 1px solid #333; padding: 20px; border-radius: 10px;
    }
    .stButton > button {
        background-color: #29b6f6; color: white; font-weight: bold; border: none; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ---
def get_chart(ticker):
    data = yf.Ticker(ticker).history(period="2y")
    if data.empty: return None
    data['SMA150'] = data['Close'].rolling(150).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Price', line=dict(color='#00e676')))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA150'], name='SMA 150', line=dict(color='#ffab00', dash='dash')))
    fig.update_layout(title=f"{ticker} Technical Trend", template="plotly_dark", height=500, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
    return fig

def get_score(ticker):
    try:
        s = yf.Ticker(ticker)
        h = s.history(period="1y")
        if len(h) < 150: return None
        
        price = h['Close'].iloc[-1]
        sma = h['Close'].rolling(150).mean().iloc[-1]
        info = s.info
        pe = info.get('forwardPE', 0)
        
        score = 50
        if price > sma: score += 25
        if pe and pe < 30: score += 25
        
        rec = "STRONG BUY" if score >= 80 else "BUY" if score >= 60 else "HOLD"
        return {"Ticker": ticker, "Price": price, "SMA": sma, "Score": score, "Rec": rec}
    except: return None

# --- הממשק ---
st.title("⚡ STOCK PRO TERMINAL")
st.markdown("### מערכת ניתוח מניות בזמן אמת")

target_stocks = st.text_input("הזיני רשימת מניות (מופרד בפסיק):", "NVDA, AAPL, MSFT, TSLA, AMZN, GOOGL, META, PLTR")
tickers = [t.strip().upper() for t in target_stocks.split(',')]

if st.button("🚀 הרץ סריקה"):
    with st.spinner('מנתח ביג דאטה מהבורסה...'):
        results = []
        for t in tickers:
            res = get_score(t)
            if res: results.append(res)
        
        if results:
            df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
            
            # הצגת המנצחת
            best = df.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("🏆 Top Pick", best['Ticker'])
            c2.metric("Score", f"{best['Score']}/100")
            c3.metric("Action", best['Rec'])
            
            st.markdown("---")
            st.subheader(f"📊 גרף המניה המובילה: {best['Ticker']}")
            st.plotly_chart(get_chart(best['Ticker']), use_container_width=True)
            
            st.subheader("📋 טבלת דירוג מלאה")
            st.dataframe(df.style.format({"Price": "${:.2f}", "SMA": "${:.2f}"}), use_container_width=True)
        else:
            st.error("לא נמצאו נתונים. נסי שנית.")
