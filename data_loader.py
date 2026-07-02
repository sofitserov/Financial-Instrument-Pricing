import pandas as pd
import numpy as np
import yfinance as yf
from statsmodels.tsa.stattools import coint

def get_data(ticker, start, end):
    raw = yf.download(ticker, start=start, end=end)
    close = raw['Close']
    return close.values.flatten().astype(float)

def get_sp500_tickers():
    import io, urllib.request
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read()
    table = pd.read_html(io.BytesIO(html))[0]
    tickers = table['Symbol'].tolist()
    return [t.replace('.', '-') for t in tickers]  # yfinance uses '-' not '.'

def find_cointegrated_pairs(close_df, candidate_pairs, pvalue_threshold=0.05):
    # Engle-Granger cointegration test: checks whether a linear combination of
    # two price series is stationary (i.e. the spread has a stable mean to revert to).
    # hedge_ratio (beta) is estimated via OLS: A = alpha + beta * B.
    from statsmodels.stats.multitest import multipletests

    candidates = []
    for a, b in candidate_pairs:
        if a not in close_df.columns or b not in close_df.columns:
            continue
        series = close_df[[a, b]].dropna()
        if len(series) < 30:
            continue
        _, pvalue, _ = coint(series[a], series[b])
        beta = np.polyfit(series[b], series[a], 1)[0]
        # beta can be negative (A and B move opposite each other, e.g. an
        # airline vs. an oil major) -- that's still a valid hedge, just with
        # both legs on the same side instead of opposite sides. Only reject
        # near-zero beta, where the "hedge" is too weak to be a real pair.
        if abs(beta) < 0.05:
            continue
        candidates.append((a, b, beta, pvalue))

    if not candidates:
        return []

    # Testing every candidate pair at a flat p<0.05 threshold produces false
    # "cointegrated" pairs by chance alone (~5% of all tests run, regardless of
    # whether any real relationship exists). Benjamini-Hochberg controls the
    # false discovery rate across the whole batch instead of trusting each
    # p-value in isolation.
    raw_pvalues = [c[3] for c in candidates]
    passed, _, _, _ = multipletests(raw_pvalues, alpha=pvalue_threshold, method='fdr_bh')

    results = [c for c, keep in zip(candidates, passed) if keep]
    return sorted(results, key=lambda x: x[3])  # sort by p-value ascending

def get_data2(tickers, start, end, top_n=15):
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
