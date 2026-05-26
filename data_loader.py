import yfinance as yf

def get_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    return data['Close'].values.flatten().astype(float)