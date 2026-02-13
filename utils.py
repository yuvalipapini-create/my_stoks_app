“””
ProTrade Ultimate - Utility Functions
מערכת עזר לניתוח מניות וניהול נתונים
“””

import yfinance as yf
import pandas as pd
import ta
import feedparser
import streamlit as st
from datetime import datetime, timedelta
import requests

class StockAnalyzer:
“”“מחלקה לניתוח טכני של מניות”””

```
@staticmethod
def calculate_indicators(df):
    """מחשב את כל האינדיקטורים הטכניים"""
    if df is None or df.empty or len(df) < 200:
        return None
    
    try:
        # Moving Averages
        df['SMA20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['SMA50'] = ta.trend.sma_indicator(df['Close'], window=50)
        df['SMA200'] = ta.trend.sma_indicator(df['Close'], window=200)
        df['EMA12'] = ta.trend.ema_indicator(df['Close'], window=12)
        df['EMA26'] = ta.trend.ema_indicator(df['Close'], window=26)
        
        # RSI
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        
        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_diff'] = macd.macd_diff()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_high'] = bb.bollinger_hband()
        df['BB_mid'] = bb.bollinger_mavg()
        df['BB_low'] = bb.bollinger_lband()
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        
        # ATR (Average True Range)
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
        
        return df
    except Exception as e:
        st.error(f"שגיאה בחישוב אינדיקטורים: {str(e)}")
        return None

@staticmethod
def detect_signals(df):
    """מזהה אותות קנייה/מכירה"""
    if df is None or len(df) < 2:
        return None
    
    signals = []
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Golden Cross
    if prev['SMA50'] <= prev['SMA200'] and latest['SMA50'] > latest['SMA200']:
        signals.append(("🟢 Golden Cross", "אות קנייה חזק - SMA50 חצה מעל SMA200"))
    
    # Death Cross
    if prev['SMA50'] >= prev['SMA200'] and latest['SMA50'] < latest['SMA200']:
        signals.append(("🔴 Death Cross", "אות מכירה חזק - SMA50 חצה מתחת ל-SMA200"))
    
    # RSI Oversold/Overbought
    if latest['RSI'] < 30:
        signals.append(("🟢 RSI Oversold", f"RSI נמוך ({latest['RSI']:.1f}) - אזור קנייה פוטנציאלי"))
    elif latest['RSI'] > 70:
        signals.append(("🔴 RSI Overbought", f"RSI גבוה ({latest['RSI']:.1f}) - אזור מכירה פוטנציאלי"))
    
    # MACD Cross
    if prev['MACD'] <= prev['MACD_signal'] and latest['MACD'] > latest['MACD_signal']:
        signals.append(("🟢 MACD Cross Up", "MACD חצה מעל קו האות - מומנטום חיובי"))
    elif prev['MACD'] >= prev['MACD_signal'] and latest['MACD'] < latest['MACD_signal']:
        signals.append(("🔴 MACD Cross Down", "MACD חצה מתחת לקו האות - מומנטום שלילי"))
    
    # Bollinger Bands
    if latest['Close'] < latest['BB_low']:
        signals.append(("🟡 BB Breakout Low", "המחיר מתחת ל-Bollinger Band התחתון"))
    elif latest['Close'] > latest['BB_high']:
        signals.append(("🟡 BB Breakout High", "המחיר מעל ל-Bollinger Band העליון"))
    
    # Volume Surge
    if latest['Volume'] > latest['Volume_SMA'] * 2:
        signals.append(("📊 Volume Spike", "נפח מסחר חריג - פי 2 מהממוצע"))
    
    return signals if signals else [("⚪ No Signals", "אין אותות ברורים כרגע")]

@staticmethod
def calculate_support_resistance(df, window=20):
    """מחשב רמות תמיכה והתנגדות"""
    if df is None or len(df) < window:
        return None, None
    
    recent = df.tail(window)
    resistance = recent['High'].max()
    support = recent['Low'].min()
    
    return support, resistance
```

class MarketData:
“”“מחלקה לטיפול בנתוני שוק”””

```
POPULAR_STOCKS = {
    'Tech Giants': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'AMD', 'INTC'],
    'EV & Auto': ['TSLA', 'F', 'GM', 'RIVN', 'LCID'],
    'Finance': ['JPM', 'BAC', 'GS', 'MS', 'WFC', 'V', 'MA'],
    'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO'],
    'Crypto': ['BTC-USD', 'ETH-USD', 'BNB-USD'],
    'Indices': ['^GSPC', '^DJI', '^IXIC', '^RUT']
}

@staticmethod
@st.cache_data(ttl=300)
def get_stock_data(symbol, period="1y"):
    """מביא נתוני מניה עם cache של 5 דקות"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        
        if df.empty or len(df) < 50:
            return None
        
        # הוסף אינדיקטורים
        df = StockAnalyzer.calculate_indicators(df)
        return df
        
    except Exception as e:
        st.error(f"שגיאה בטעינת {symbol}: {str(e)}")
        return None

@staticmethod
@st.cache_data(ttl=60)
def get_ticker_data():
    """מביא נתונים לפס הרץ"""
    try:
        tickers = ['^GSPC', '^IXIC', 'NVDA', 'AAPL', 'TSLA', 'BTC-USD', 'MSFT', 'AMZN']
        data = yf.download(tickers, period="1d", progress=False, threads=True)
        
        ticker_items = []
        for t in tickers:
            try:
                if len(tickers) > 1:
                    close = data['Close'][t].iloc[-1]
                    open_price = data['Open'][t].iloc[0]
                else:
                    close = data['Close'].iloc[-1]
                    open_price = data['Open'].iloc[0]
                
                change = ((close - open_price) / open_price) * 100
                symbol = "▲" if change >= 0 else "▼"
                color = "#00ff88" if change >= 0 else "#ff0055"
                
                display_name = t.replace('^', '').replace('-USD', '')
                ticker_items.append(f'<span style="color:{color}">{display_name}: ${close:,.0f} {symbol}{abs(change):.1f}%</span>')
            except:
                continue
        
        return " &nbsp;&nbsp;|&nbsp;&nbsp; ".join(ticker_items)
    except:
        return '🔴 לא ניתן לטעון נתוני שוק'

@staticmethod
@st.cache_data(ttl=600)
def get_stock_info(symbol):
    """מביא מידע בסיסי על המניה"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return {
            'name': info.get('longName', symbol),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'marketCap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend': info.get('dividendYield', 0),
            'beta': info.get('beta', 0),
            '52w_high': info.get('fiftyTwoWeekHigh', 0),
            '52w_low': info.get('fiftyTwoWeekLow', 0)
        }
    except:
        return None
```

class NewsProvider:
“”“מחלקה לטיפול בחדשות”””

```
@staticmethod
@st.cache_data(ttl=600)
def get_market_news():
    """מביא חדשות שוק"""
    sources = [
        ("https://news.google.com/rss/search?q=stock+market&hl=en&gl=US&ceid=US:en", "Global Market"),
        ("https://news.google.com/rss/search?q=nasdaq+nyse&hl=en&gl=US&ceid=US:en", "US Markets"),
    ]
    
    all_news = []
    for url, source in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                all_news.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.get('published', 'N/A'),
                    'source': source
                })
        except:
            continue
    
    return all_news[:10]

@staticmethod
@st.cache_data(ttl=600)
def get_israel_news():
    """חדשות מישראל"""
    try:
        url = "https://news.google.com/rss/search?q=בורסה+תל+אביב&hl=he&gl=IL&ceid=IL:he"
        feed = feedparser.parse(url)
        return feed.entries[:8]
    except:
        return []
```

class Portfolio:
“”“מחלקה לניהול תיק השקעות”””

```
@staticmethod
def calculate_portfolio_value(holdings):
    """מחשב ערך תיק"""
    total_value = 0
    total_cost = 0
    details = []
    
    for symbol, data in holdings.items():
        try:
            stock = yf.Ticker(symbol)
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            
            shares = data['shares']
            avg_cost = data['avg_cost']
            
            current_value = shares * current_price
            cost_basis = shares * avg_cost
            profit = current_value - cost_basis
            profit_pct = (profit / cost_basis) * 100
            
            total_value += current_value
            total_cost += cost_basis
            
            details.append({
                'Symbol': symbol,
                'Shares': shares,
                'Avg Cost': avg_cost,
                'Current Price': current_price,
                'Value': current_value,
                'Profit/Loss': profit,
                'Return %': profit_pct
            })
        except:
            continue
    
    return {
        'total_value': total_value,
        'total_cost': total_cost,
        'total_profit': total_value - total_cost,
        'total_return': ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
        'holdings': details
    }
```

def convert_df_to_csv(df):
“”“המרת DataFrame ל-CSV להורדה”””
return df.to_csv(index=True).encode(‘utf-8-sig’)

def get_color_for_value(value):
“”“מחזיר צבע בהתאם לערך חיובי/שלילי”””
if value > 0:
return “#00ff88”
elif value < 0:
return “#ff0055”
return “#ffffff”
