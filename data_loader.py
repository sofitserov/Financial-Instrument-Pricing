import pandas as pd
import numpy as np
import yfinance as yf

def get_data(ticker, start, end):
    raw = yf.download(ticker, start=start, end=end)
    close = raw['Close']
    return close.values.flatten().astype(float)

def get_data2(tickers, start, end):
    # Fetch full OHLCV data instead of defaulting to a single column
    raw = yf.download(tickers, start=start, end=end)
    
    # Extract structural components needed for technical indicator bands
    close_df = raw['Close']
    high_df  = raw['High']
    open_df  = raw['Open']
    low_df   = raw['Low']
    
    # Calculate Rate of Change metrics exactly as before
    roc63  = close_df.pct_change(63)
    roc126 = close_df.pct_change(126)
    roc252 = close_df.pct_change(252)
    
    rank63  = roc63.rank(axis=1, ascending=False)
    rank126 = roc126.rank(axis=1, ascending=False)
    rank252 = roc252.rank(axis=1, ascending=False)
    top_n = 15

    strong = (
        (rank63  <= top_n) &
        (rank126 <= top_n) &
        (rank252 <= top_n)
    )
    
    # Generate the universe list per timestamp
    daily_universe = {date: strong.columns[strong.loc[date]].tolist() for date in strong.index}
    
    return {
        "open": open_df,
        "high": high_df,
        "low": low_df,
        "close": close_df,
        "daily_universe": daily_universe
    }