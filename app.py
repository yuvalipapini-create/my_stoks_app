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
        background: rgba(255,255,25…
