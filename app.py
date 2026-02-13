PRO TRADE ULTIMATE v2.0
מערכת מסחר וניתוח מתקדמת בזמן אמת
“””

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta

# Import custom utilities

from utils import (
StockAnalyzer, MarketData, NewsProvider, Portfolio,
convert_df_to_csv, get_color_for_value
)

# ═══════════════════════════════════════════════════════════

# PAGE CONFIG - חייב להיות ראשון

# ═══════════════════════════════════════════════════════════

st.set_page_config(
page_title=“ProTrade Ultimate v2.0”,
layout=“wide”,
page_icon=“📈”,
initial_sidebar_state=“expanded”
)

# ═══════════════════════════════════════════════════════════

# SESSION STATE INITIALIZATION

# ═══════════════════════════════════════════════════════════

if ‘portfolio’ not in st.session_state:
st.session_state.portfolio = {}
if ‘watchlist’ not in st.session_state:
st.session_state.watchlist = [‘NVDA’, ‘AAPL’, ‘TSLA’]
if ‘alerts’ not in st.session_state:
st.session_state.alerts = {}
if ‘theme’ not in st.session_state:
st.session_state.theme = ‘dark’

# ═══════════════════════════════════════════════════════════

# STYLES - Glassmorphism Premium Design

# ═══════════════════════════════════════════════════════════

def get_css():
return “””
<style>
@import url(‘https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap’);


    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 20% 50%, rgba(26, 28, 41, 1) 0%, rgba(13, 14, 18, 1) 100%);
        color: #ffffff;
    }
    
    /* הסתרת אלמנטים מיותרים */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Ticker Bar */
    .ticker-wrap {
        width: 100%;
        background: linear-gradient(90deg, rgba(0,255,136,0.05) 0%, rgba(0,204,255,0.05) 100%);
        border-bottom: 1px solid rgba(0,255,136,0.2);
        overflow: hidden;
        padding: 12px 0;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    .ticker {
        display: inline-block;
        animation: scroll 60s linear infinite;
        font-size: 16px;
        font-weight: 600;
        white-space: nowrap;
    }
    
    @keyframes scroll {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    /* Glass Cards */
    div[data-testid="metric-container"], 
    div[data-testid="stMetric"],
    .card-glass {
        background: rgba(255, 255, 255, 0.04) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    div[data-testid="metric-container"]:hover {
        border-color: rgba(0,255,136,0.5) !important;
        transform: translateY(-4px) !important;
        box-shadow: 0 12px 40px rgba(0,255,136,0.2) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%) !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        transition: all 0.3s !important;
        box-shadow: 0 4px 15px rgba(0,255,136,0.3) !important;
    }
    
    .stButton > button:hover {
        box-shadow: 0 6px 25px rgba(0,255,136,0.5) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,0.02);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        color: #ffffff;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
        color: #000000;
    }
    
    /* DataFrames */
    .dataframe {
        background: rgba(255,255,255,0.03) !important;
        border-radius: 8px !important;
    }
    
    /* Custom Alert Box */
    .alert-box {
        background: rgba(255, 200, 0, 0.1);
        border-left: 4px solid #ffc800;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Signal Cards */
    .signal-card {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 15px;
        margin: 8px 0;
        border-left: 4px solid;
        transition: 0.3s;
    }
    
    .signal-card:hover {
        background: rgba(255,255,255,0.08);
        transform: translateX(5px);
    }
    
    .signal-buy { border-left-color: #00ff88; }
    .signal-sell { border-left-color: #ff0055; }
    .signal-neutral { border-left-color: #ffc800; }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(0,255,136,0.5);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0,255,136,0.7);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-weight: 700 !important;
        background: linear-gradient(135deg, #00ff88 0%, #00ccff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(13, 14, 18, 0.95) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
    }
    
    /* Info boxes */
    .stAlert {
        background: rgba(0, 255, 136, 0.1) !important;
        border: 1px solid rgba(0, 255, 136, 0.3) !important;
        border-radius: 12px !important;
    }
</style>
"""


st.markdown(get_css(), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════

# TICKER BAR

# ═══════════════════════════════════════════════════════════

ticker_html = MarketData.get_ticker_data()
st.markdown(f”””

<div class="ticker-wrap">
    <div class="ticker">{ticker_html}</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════

# SIDEBAR - Navigation & Settings

# ═══════════════════════════════════════════════════════════

with st.sidebar:
st.image(“https://img.icons8.com/fluency/96/000000/stock-market.png”, width=80)
st.title(“ProTrade v2.0”)
st.markdown(”—”)


# Quick Stats
st.subheader("📊 Quick Stats")
try:
    sp500 = yf.Ticker("^GSPC")
    sp_data = sp500.history(period="1d")
    if not sp_data.empty:
        sp_price = sp_data['Close'].iloc[-1]
        sp_change = ((sp_data['Close'].iloc[-1] - sp_data['Open'].iloc[0]) / sp_data['Open'].iloc[0]) * 100
        st.metric("S&P 500", f"${sp_price:,.0f}", f"{sp_change:.2f}%")
except:
    st.metric("S&P 500", "Loading...")

st.markdown("---")

# Watchlist Management
st.subheader("⭐ Watchlist")
new_symbol = st.text_input("Add Symbol:", placeholder="AAPL").upper()
if st.button("➕ Add to Watchlist") and new_symbol:
    if new_symbol not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_symbol)
        st.success(f"✅ {new_symbol} added!")
        st.rerun()

# Display watchlist
if st.session_state.watchlist:
    for idx, sym in enumerate(st.session_state.watchlist):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"🔹 {sym}")
        with col2:
            if st.button("❌", key=f"remove_{sym}"):
                st.session_state.watchlist.remove(sym)
                st.rerun()

st.markdown("---")

# Market Status
st.subheader("🕐 Market Status")
now = datetime.now()
market_open = now.replace(hour=9, minute=30, second=0)
market_close = now.replace(hour=16, minute=0, second=0)

if market_open <= now <= market_close and now.weekday() < 5:
    st.success("🟢 Market OPEN")
else:
    st.error("🔴 Market CLOSED")

st.caption(f"🕐 {now.strftime('%H:%M:%S')}")


# ═══════════════════════════════════════════════════════════

# MAIN HEADER

# ═══════════════════════════════════════════════════════════

col1, col2 = st.columns([4, 1])
with col1:
st.title(“📈 PRO TRADE TERMINAL”)
st.caption(“Advanced Trading & Analysis Platform | Real-time Market Data”)
with col2:
if st.button(“🔄 Refresh All”, use_container_width=True):
st.cache_data.clear()
st.rerun()

# ═══════════════════════════════════════════════════════════

# TAB NAVIGATION

# ═══════════════════════════════════════════════════════════

tabs = st.tabs([
“📊 Trading Terminal”,
“🔍 Market Scanner”,
“💼 Portfolio Tracker”,
“📰 News & Insights”,
“🎯 Screener Pro”,
“📚 Market Overview”
])

# ═══════════════════════════════════════════════════════════

# TAB 1: TRADING TERMINAL

# ═══════════════════════════════════════════════════════════

with tabs[0]:
col_select, col_info = st.columns([1, 2])


with col_select:
    st.subheader("🎯 Select Asset")
    
    # Category selection
    category = st.selectbox("Category:", list(MarketData.POPULAR_STOCKS.keys()))
    symbol = st.selectbox("Symbol:", MarketData.POPULAR_STOCKS[category])
    
    # Time range
    period = st.select_slider(
        "Time Range:",
        options=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'],
        value='1y'
    )

# Fetch data
with st.spinner(f"⏳ Loading {symbol} data..."):
    df = MarketData.get_stock_data(symbol, period=period)
    stock_info = MarketData.get_stock_info(symbol)

if df is not None and not df.empty:
    # Current metrics
    current_price = df['Close'].iloc[-1]
    open_price = df['Open'].iloc[-1]
    high_price = df['High'].iloc[-1]
    low_price = df['Low'].iloc[-1]
    volume = df['Volume'].iloc[-1]
    
    change = current_price - open_price
    change_pct = (change / open_price) * 100
    
    # Key Metrics Row
    st.markdown("### 📈 Key Metrics")
    m1, m2, m3, m4, m5 = st.columns(5)
    
    m1.metric("Price", f"${current_price:,.2f}", f"{change_pct:+.2f}%")
    m2.metric("High", f"${high_price:,.2f}")
    m3.metric("Low", f"${low_price:,.2f}")
    m4.metric("Volume", f"{volume/1_000_000:.1f}M")
    m5.metric("RSI", f"{df['RSI'].iloc[-1]:.1f}")
    
    # Technical Indicators Row
    st.markdown("### 🔧 Technical Indicators")
    t1, t2, t3, t4 = st.columns(4)
    
    t1.metric("SMA 50", f"${df['SMA50'].iloc[-1]:,.2f}", 
             "Bullish ✅" if current_price > df['SMA50'].iloc[-1] else "Bearish ⚠️")
    t2.metric("SMA 200", f"${df['SMA200'].iloc[-1]:,.2f}",
             "Bullish ✅" if current_price > df['SMA200'].iloc[-1] else "Bearish ⚠️")
    t3.metric("MACD", f"{df['MACD'].iloc[-1]:.2f}")
    t4.metric("ATR", f"${df['ATR'].iloc[-1]:.2f}")
    
    # Stock Info
    if stock_info:
        st.markdown("### ℹ️ Company Information")
        i1, i2, i3, i4 = st.columns(4)
        i1.metric("Market Cap", f"${stock_info['marketCap']/1e9:.1f}B" if stock_info['marketCap'] > 0 else "N/A")
        i2.metric("P/E Ratio", f"{stock_info['pe_ratio']:.2f}" if stock_info['pe_ratio'] else "N/A")
        i3.metric("52W High", f"${stock_info['52w_high']:,.2f}" if stock_info['52w_high'] > 0 else "N/A")
        i4.metric("52W Low", f"${stock_info['52w_low']:,.2f}" if stock_info['52w_low'] > 0 else "N/A")
        
        st.caption(f"**Sector:** {stock_info['sector']} | **Industry:** {stock_info['industry']}")
    
    st.markdown("---")
    
    # Trading Signals
    signals = StockAnalyzer.detect_signals(df)
    if signals:
        st.markdown("### 🎯 Trading Signals")
        sig_cols = st.columns(2)
        for idx, (signal_type, description) in enumerate(signals):
            with sig_cols[idx % 2]:
                signal_class = "signal-buy" if "🟢" in signal_type else "signal-sell" if "🔴" in signal_type else "signal-neutral"
                st.markdown(f"""
                <div class="signal-card {signal_class}">
                    <strong>{signal_type}</strong><br>
                    <small>{description}</small>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Chart Options
    chart_col1, chart_col2 = st.columns([3, 1])
    with chart_col2:
        st.subheader("Chart Settings")
        show_sma = st.checkbox("SMA 50/200", value=True)
        show_bb = st.checkbox("Bollinger Bands", value=False)
        show_volume = st.checkbox("Volume", value=True)
        show_rsi = st.checkbox("RSI", value=False)
    
    # Create Interactive Chart
    with chart_col1:
        st.subheader(f"📊 {symbol} Technical Chart")
    
    # Determine number of rows
    rows = 1
    row_heights = [0.7]
    if show_volume:
        rows += 1
        row_heights.append(0.15)
    if show_rsi:
        rows += 1
        row_heights.append(0.15)
    
    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=(f'{symbol} Price', 'Volume' if show_volume else '', 'RSI' if show_rsi else '')
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff0055'
        ),
        row=1, col=1
    )
    
    # SMAs
    if show_sma:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], 
                                line=dict(color='#00ccff', width=1.5),
                                name='SMA 50'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'],
                                line=dict(color='#ff0055', width=1.5),
                                name='SMA 200'), row=1, col=1)
    
    # Bollinger Bands
    if show_bb:
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_high'],
                                line=dict(color='rgba(255,255,255,0.2)', width=1, dash='dash'),
                                name='BB Upper'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_low'],
                                line=dict(color='rgba(255,255,255,0.2)', width=1, dash='dash'),
                                fill='tonexty', fillcolor='rgba(255,255,255,0.05)',
                                name='BB Lower'), row=1, col=1)
    
    # Volume
    current_row = 2
    if show_volume:
        colors = ['#00ff88' if row['Close'] >= row['Open'] else '#ff0055' 
                 for _, row in df.iterrows()]
        fig.add_trace(
            go.Bar(x=df.index, y=df['Volume'], name='Volume',
                  marker_color=colors, opacity=0.7),
            row=current_row, col=1
        )
        current_row += 1
    
    # RSI
    if show_rsi:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#ffc800', width=2),
                      name='RSI'),
            row=current_row, col=1
        )
        # RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=current_row, col=1)
    
    # Layout
    fig.update_layout(
        template='plotly_dark',
        height=700,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Export Options
    st.markdown("---")
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        csv_data = convert_df_to_csv(df)
        st.download_button(
            label="📥 Download Data (CSV)",
            data=csv_data,
            file_name=f"{symbol}_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    with export_col2:
        st.info(f"📅 Last Updated: {df.index[-1].strftime('%Y-%m-%d %H:%M')}")

else:
    st.error(f"❌ Unable to load data for {symbol}. Please try another symbol.")


# ═══════════════════════════════════════════════════════════

# TAB 2: MARKET SCANNER

# ═══════════════════════════════════════════════════════════

with tabs[1]:
st.header(“🔍 Smart Market Scanner”)
st.caption(“Scan markets for high-probability trading opportunities”)


scan_col1, scan_col2 = st.columns([2, 1])

with scan_col2:
    st.subheader("⚙️ Scanner Settings")
    scan_category = st.selectbox("Scan Category:", list(MarketData.POPULAR_STOCKS.keys()), key='scan_cat')
    
    rsi_min = st.slider("Min RSI:", 0, 100, 30)
    rsi_max = st.slider("Max RSI:", 0, 100, 70)
    
    min_volume = st.number_input("Min Volume (M):", min_value=0.0, value=1.0, step=0.5)
    
    scan_button = st.button("🚀 Run Scanner", use_container_width=True)

with scan_col1:
    if scan_button:
        scan_symbols = MarketData.POPULAR_STOCKS[scan_category]
        
        with st.spinner(f"🔎 Scanning {len(scan_symbols)} symbols..."):
            results = []
            progress_bar = st.progress(0)
            
            # Download all at once for speed
            try:
                data = yf.download(scan_symbols, period="3mo", group_by='ticker', progress=False, threads=True)
                
                for idx, symbol in enumerate(scan_symbols):
                    try:
                        # Extract data for this symbol
                        if len(scan_symbols) == 1:
                            stock_df = data.copy()
                        else:
                            stock_df = data[symbol].dropna()
                        
                        if len(stock_df) < 50:
                            continue
                        
                        # Calculate indicators
                        stock_df = StockAnalyzer.calculate_indicators(stock_df)
                        if stock_df is None:
                            continue
                        
                        latest = stock_df.iloc[-1]
                        
                        # Apply filters
                        if not (rsi_min <= latest['RSI'] <= rsi_max):
                            continue
                        if latest['Volume'] < min_volume * 1_000_000:
                            continue
                        
                        # Calculate score
                        score = 0
                        reasons = []
                        
                        # Price above SMAs
                        if latest['Close'] > latest['SMA50']:
                            score += 1
                            reasons.append("Above SMA50")
                        if latest['Close'] > latest['SMA200']:
                            score += 1
                            reasons.append("Above SMA200")
                        
                        # RSI conditions
                        if 40 < latest['RSI'] < 60:
                            score += 1
                            reasons.append("RSI Neutral")
                        elif latest['RSI'] < 35:
                            score += 1
                            reasons.append("RSI Oversold")
                        
                        # MACD positive
                        if latest['MACD'] > latest['MACD_signal']:
                            score += 1
                            reasons.append("MACD Bullish")
                        
                        # Volume spike
                        if latest['Volume'] > latest['Volume_SMA'] * 1.5:
                            score += 1
                            reasons.append("High Volume")
                        
                        # Determine rating
                        if score >= 4:
                            rating = "🟢 Strong Buy"
                        elif score >= 3:
                            rating = "🟡 Buy"
                        elif score >= 2:
                            rating = "🔵 Watch"
                        else:
                            rating = "⚪ Neutral"
                        
                        results.append({
                            'Symbol': symbol,
                            'Price': latest['Close'],
                            'Change %': ((latest['Close'] - latest['Open']) / latest['Open'] * 100),
                            'RSI': latest['RSI'],
                            'Volume': latest['Volume'] / 1_000_000,
                            'Score': score,
                            'Rating': rating,
                            'Signals': ', '.join(reasons[:3])
                        })
                    
                    except Exception as e:
                        continue
                    
                    progress_bar.progress((idx + 1) / len(scan_symbols))
                
                progress_bar.empty()
                
                if results:
                    results_df = pd.DataFrame(results).sort_values('Score', ascending=False)
                    
                    st.success(f"✅ Found {len(results)} opportunities!")
                    
                    # Display results
                    st.dataframe(
                        results_df.style.format({
                            'Price': '${:.2f}',
                            'Change %': '{:+.2f}%',
                            'RSI': '{:.1f}',
                            'Volume': '{:.1f}M'
                        }).applymap(
                            lambda v: 'color: #00ff88; font-weight: bold' if 'Strong Buy' in str(v) 
                            else 'color: #ffc800; font-weight: bold' if 'Buy' in str(v)
                            else '', subset=['Rating']
                        ),
                        use_container_width=True,
                        height=500
                    )
                    
                    # Export
                    scan_csv = convert_df_to_csv(results_df)
                    st.download_button(
                        "📥 Export Results",
                        scan_csv,
                        f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        "text/csv"
                    )
                else:
                    st.warning("⚠️ No stocks matched your criteria. Try adjusting the filters.")
            
            except Exception as e:
                st.error(f"❌ Scanner error: {str(e)}")


# ═══════════════════════════════════════════════════════════

# TAB 3: PORTFOLIO TRACKER

# ═══════════════════════════════════════════════════════════

with tabs[2]:
st.header(“💼 Portfolio Tracker”)


port_col1, port_col2 = st.columns([2, 1])

with port_col2:
    st.subheader("➕ Add Position")
    
    add_symbol = st.text_input("Symbol:", key='port_symbol').upper()
    add_shares = st.number_input("Shares:", min_value=0.0, value=1.0, step=0.1)
    add_cost = st.number_input("Avg Cost ($):", min_value=0.0, value=100.0, step=0.01)
    
    if st.button("Add to Portfolio") and add_symbol:
        st.session_state.portfolio[add_symbol] = {
            'shares': add_shares,
            'avg_cost': add_cost
        }
        st.success(f"✅ Added {add_shares} shares of {add_symbol}")
        st.rerun()

with port_col1:
    if st.session_state.portfolio:
        with st.spinner("📊 Calculating portfolio value..."):
            portfolio_data = Portfolio.calculate_portfolio_value(st.session_state.portfolio)
        
        # Summary metrics
        st.subheader("📈 Portfolio Summary")
        p1, p2, p3, p4 = st.columns(4)
        
        p1.metric("Total Value", f"${portfolio_data['total_value']:,.2f}")
        p2.metric("Total Cost", f"${portfolio_data['total_cost']:,.2f}")
        p3.metric("Profit/Loss", f"${portfolio_data['total_profit']:,.2f}",
                 f"{portfolio_data['total_return']:.2f}%")
        p4.metric("Holdings", len(st.session_state.portfolio))
        
        # Holdings table
        st.markdown("---")
        st.subheader("📋 Holdings Details")
        
        holdings_df = pd.DataFrame(portfolio_data['holdings'])
        if not holdings_df.empty:
            st.dataframe(
                holdings_df.style.format({
                    'Shares': '{:.2f}',
                    'Avg Cost': '${:.2f}',
                    'Current Price': '${:.2f}',
                    'Value': '${:.2f}',
                    'Profit/Loss': '${:.2f}',
                    'Return %': '{:+.2f}%'
                }).applymap(
                    lambda v: f'color: {get_color_for_value(v)}' if isinstance(v, (int, float)) and v != 0 
                    else '', subset=['Profit/Loss', 'Return %']
                ),
                use_container_width=True
            )
            
            # Remove positions
            st.markdown("---")
            remove_symbol = st.selectbox("Remove Position:", list(st.session_state.portfolio.keys()))
            if st.button("🗑️ Remove"):
                del st.session_state.portfolio[remove_symbol]
                st.success(f"Removed {remove_symbol}")
                st.rerun()
    else:
        st.info("📝 Your portfolio is empty. Add your first position using the form on the right.")


# ═══════════════════════════════════════════════════════════

# TAB 4: NEWS & INSIGHTS

# ═══════════════════════════════════════════════════════════

with tabs[3]:
st.header(“📰 Market News & Insights”)


news_tabs = st.tabs(["🌍 Global Markets", "🇮🇱 Israel Markets"])

with news_tabs[0]:
    if st.button("🔄 Refresh Global News"):
        st.cache_data.clear()
        st.rerun()
    
    news_items = NewsProvider.get_market_news()
    
    if news_items:
        news_cols = st.columns(2)
        for idx, item in enumerate(news_items):
            with news_cols[idx % 2]:
                st.markdown(f"""
                <div class="card-glass" style="margin-bottom: 15px; padding: 15px;">
                    <div style="color: #00ff88; font-size: 12px; margin-bottom: 5px;">
                        {item['source']}
                    </div>
                    <a href="{item['link']}" target="_blank" 
                       style="color: #ffffff; font-weight: 600; text-decoration: none; font-size: 15px;">
                        {item['title']}
                    </a>
                    <div style="color: #888; font-size: 11px; margin-top: 8px;">
                        {item['published']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Unable to load news. Please check your connection.")

with news_tabs[1]:
    if st.button("🔄 Refresh Israel News"):
        st.cache_data.clear()
        st.rerun()
    
    il_news = NewsProvider.get_israel_news()
    
    if il_news:
        news_cols = st.columns(2)
        for idx, item in enumerate(il_news):
            with news_cols[idx % 2]:
                st.markdown(f"""
                <div class="card-glass" style="margin-bottom: 15px; padding: 15px;">
                    <a href="{item.link}" target="_blank" 
                       style="color: #ffffff; font-weight: 600; text-decoration: none; font-size: 15px;">
                        {item.title}
                    </a>
                    <div style="color: #888; font-size: 11px; margin-top: 8px;">
                        {item.get('published', 'N/A')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Unable to load Israeli news.")


# ═══════════════════════════════════════════════════════════

# TAB 5: SCREENER PRO

# ═══════════════════════════════════════════════════════════

with tabs[4]:
st.header(“🎯 Advanced Stock Screener”)
st.caption(“Filter stocks by multiple technical and fundamental criteria”)


# Screener settings
screen_col1, screen_col2, screen_col3 = st.columns(3)

with screen_col1:
    st.subheader("📊 Technical Filters")
    screen_rsi_low = st.slider("RSI Lower Bound:", 0, 50, 20, key='screen_rsi_low')
    screen_rsi_high = st.slider("RSI Upper Bound:", 50, 100, 80, key='screen_rsi_high')
    price_above_sma200 = st.checkbox("Price > SMA200", value=False)

with screen_col2:
    st.subheader("💰 Price Filters")
    min_price = st.number_input("Min Price ($):", min_value=0.0, value=10.0, step=1.0)
    max_price = st.number_input("Max Price ($):", min_value=0.0, value=1000.0, step=10.0)

with screen_col3:
    st.subheader("📈 Volume Filters")
    min_vol_m = st.number_input("Min Daily Volume (M):", min_value=0.0, value=0.5, step=0.1)
    volume_spike = st.checkbox("Volume Spike (>150% avg)", value=False)

# Categories to screen
categories_to_screen = st.multiselect(
    "Select Categories to Screen:",
    list(MarketData.POPULAR_STOCKS.keys()),
    default=['Tech Giants']
)

if st.button("🔍 Run Advanced Screener", use_container_width=True):
    all_symbols = []
    for cat in categories_to_screen:
        all_symbols.extend(MarketData.POPULAR_STOCKS[cat])
    
    all_symbols = list(set(all_symbols))  # Remove duplicates
    
    with st.spinner(f"🔎 Screening {len(all_symbols)} stocks..."):
        screener_results = []
        progress = st.progress(0)
        
        try:
            data = yf.download(all_symbols, period="6mo", group_by='ticker', progress=False, threads=True)
            
            for idx, sym in enumerate(all_symbols):
                try:
                    if len(all_symbols) == 1:
                        sym_df = data.copy()
                    else:
                        sym_df = data[sym].dropna()
                    
                    if len(sym_df) < 50:
                        continue
                    
                    sym_df = StockAnalyzer.calculate_indicators(sym_df)
                    if sym_df is None:
                        continue
                    
                    latest = sym_df.iloc[-1]
                    
                    # Apply all filters
                    if not (screen_rsi_low <= latest['RSI'] <= screen_rsi_high):
                        continue
                    if not (min_price <= latest['Close'] <= max_price):
                        continue
                    if latest['Volume'] < min_vol_m * 1_000_000:
                        continue
                    if price_above_sma200 and latest['Close'] < latest['SMA200']:
                        continue
                    if volume_spike and latest['Volume'] < latest['Volume_SMA'] * 1.5:
                        continue
                    
                    # Passed all filters
                    screener_results.append({
                        'Symbol': sym,
                        'Price': latest['Close'],
                        'RSI': latest['RSI'],
                        'Volume (M)': latest['Volume'] / 1_000_000,
                        'SMA200': latest['SMA200'],
                        'Distance from SMA200 (%)': ((latest['Close'] - latest['SMA200']) / latest['SMA200'] * 100)
                    })
                
                except:
                    continue
                
                progress.progress((idx + 1) / len(all_symbols))
            
            progress.empty()
            
            if screener_results:
                results_df = pd.DataFrame(screener_results)
                st.success(f"✅ {len(results_df)} stocks passed all filters!")
                
                st.dataframe(
                    results_df.style.format({
                        'Price': '${:.2f}',
                        'RSI': '{:.1f}',
                        'Volume (M)': '{:.1f}M',
                        'SMA200': '${:.2f}',
                        'Distance from SMA200 (%)': '{:+.2f}%'
                    }),
                    use_container_width=True
                )
                
                csv = convert_df_to_csv(results_df)
                st.download_button(
                    "📥 Download Screener Results",
                    csv,
                    f"screener_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    "text/csv"
                )
            else:
                st.warning("⚠️ No stocks matched all criteria. Try relaxing some filters.")
        
        except Exception as e:
            st.error(f"❌ Screener error: {str(e)}")


# ═══════════════════════════════════════════════════════════

# TAB 6: MARKET OVERVIEW

# ═══════════════════════════════════════════════════════════

with tabs[5]:
st.header(“📚 Market Overview & Heatmap”)


# Major Indices
st.subheader("📊 Major Indices")

indices = {
    'S&P 500': '^GSPC',
    'Dow Jones': '^DJI',
    'NASDAQ': '^IXIC',
    'Russell 2000': '^RUT'
}

idx_cols = st.columns(4)
for idx, (name, ticker) in enumerate(indices.items()):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            change = ((data['Close'].iloc[-1] - data['Open'].iloc[0]) / data['Open'].iloc[0]) * 100
            idx_cols[idx].metric(name, f"{price:,.0f}", f"{change:+.2f}%")
    except:
        idx_cols[idx].metric(name, "N/A")

st.markdown("---")

# Sector Performance
st.subheader("🏭 Sector Performance (Top Stocks)")

sector_perf = []
for category, symbols in MarketData.POPULAR_STOCKS.items():
    if category in ['Indices', 'Crypto']:
        continue
    
    try:
        # Sample 3 stocks from each sector
        sample_symbols = symbols[:3]
        sector_data = yf.download(sample_symbols, period="1d", progress=False, threads=True)
        
        if not sector_data.empty:
            avg_change = 0
            count = 0
            for sym in sample_symbols:
                try:
                    if len(sample_symbols) > 1:
                        close = sector_data['Close'][sym].iloc[-1]
                        open_p = sector_data['Open'][sym].iloc[0]
                    else:
                        close = sector_data['Close'].iloc[-1]
                        open_p = sector_data['Open'].iloc[0]
                    
                    change = ((close - open_p) / open_p) * 100
                    avg_change += change
                    count += 1
                except:
                    continue
            
            if count > 0:
                avg_change /= count
                sector_perf.append({
                    'Sector': category,
                    'Avg Change %': avg_change
                })
    except:
        continue

if sector_perf:
    sector_df = pd.DataFrame(sector_perf).sort_values('Avg Change %', ascending=False)
    
    # Create bar chart
    fig_sector = go.Figure()
    
    colors = ['#00ff88' if x > 0 else '#ff0055' for x in sector_df['Avg Change %']]
    
    fig_sector.add_trace(go.Bar(
        x=sector_df['Sector'],
        y=sector_df['Avg Change %'],
        marker_color=colors,
        text=sector_df['Avg Change %'].apply(lambda x: f'{x:+.2f}%'),
        textposition='outside'
    ))
    
    fig_sector.update_layout(
        template='plotly_dark',
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title='Sector Performance Today',
        yaxis_title='Change %',
        showlegend=False
    )
    
    st.plotly_chart(fig_sector, use_container_width=True)


# ═══════════════════════════════════════════════════════════

# FOOTER

# ═══════════════════════════════════════════════════════════

st.markdown(”—”)
st.markdown(”””

<div style='text-align: center; color: #888; padding: 20px;'>
    <strong>ProTrade Ultimate v2.0</strong> | Advanced Trading Platform<br>
    ⚠️ <em>Disclaimer: This tool is for educational purposes only. Not financial advice.</em><br>
    Data provided by Yahoo Finance
</div>
""", unsafe_allow_html=True)

