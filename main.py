import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime

FMP_API_KEY = ''

def fetch_stock_prices(ticker):
    stock_data = yf.download(ticker, start='2010-01-01', end=datetime.today().strftime('%Y-%m-%d'))
    stock_data = stock_data['Adj Close']
    return stock_data

def fetch_fundamental_data(ticker):
    url = f'https://financialmodelingprep.com/api/v3/historical/key-metrics/{ticker}?limit=500&apikey={FMP_API_KEY}'
    response = requests.get(url)
    data = response.json()
    if 'historical' in data:
        df = pd.DataFrame(data['historical'])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = df[['peRatio', 'forwardPE', 'pegRatio']]
        return df
    else:
        return pd.DataFrame()

def prepare_data(ticker):
    prices = fetch_stock_prices(ticker)
    fundamentals = fetch_fundamental_data(ticker)
    prices.index = pd.to_datetime(prices.index)  
    fundamentals.index = pd.to_datetime(fundamentals.index) 
    data = pd.merge_asof(prices.sort_index(), fundamentals.sort_index(), left_index=True, right_index=True, direction='backward')
    data.dropna(inplace=True)
    return data

def generate_signals(data):
    data['pe_diff_pct'] = (data['forwardPE'] - data['peRatio']) / data['peRatio']
    data['signal'] = np.where(data['pe_diff_pct'] >= 0.20, 1, 0)
    return data

def backtest_strategy(data, holding_period=30):
    positions = []
    returns = []
    for i in range(len(data)):
        if data['signal'].iloc[i] == 1:
            entry_date = data.index[i]
            entry_price = data['Adj Close'].iloc[i]
            exit_index = i + holding_period
            if exit_index < len(data):
                exit_date = data.index[exit_index]
                exit_price = data['Adj Close'].iloc[exit_index]
                ret = (exit_price - entry_price) / entry_price
                positions.append({'Ticker': ticker, 'Entry Date': entry_date, 'Exit Date': exit_date, 'Return': ret})
                returns.append(ret)
    return positions, returns

def analyze_results(positions, returns):
    results_df = pd.DataFrame(positions)
    average_return = np.mean(returns)
    median_return = np.median(returns)
    win_rate = len([r for r in returns if r > 0]) / len(returns) if returns else 0
    print(f"Total Trades: {len(returns)}")
    print(f"Average Return: {average_return * 100:.2f}%")
    print(f"Median Return: {median_return * 100:.2f}%")
    print(f"Win Rate: {win_rate * 100:.2f}%")
    return results_df

stocks = ['ANF', 'GIL']
all_positions = []
all_returns = []

for ticker in stocks:
    print(f"\nProcessing {ticker}...")
    data = prepare_data(ticker)
    if data.empty:
        print(f"No data available for {ticker}. Skipping.")
        continue
    data = generate_signals(data)
    positions, returns = backtest_strategy(data)
    all_positions.extend(positions)
    all_returns.extend(returns)

print("\nAggregated Results:")
results_df = analyze_results(all_positions, all_returns)
