import robin_stocks.robinhood as rh
import datetime as dt
import pandas as pd
import ta

# Replace 'email' and 'password' with your actual Robinhood credentials
username = 'email'
password = 'password'

def login(days = 1):
    # Logging in
    time_logged_in = 60 * 60 * 24 * days
    rh.authentication.login(username, password, time_logged_in, 'internal', True, True)
    print("Login successful.")

def logout():
    # Logging out
    rh.authentication.logout()
    print("Logout successful.")

def open_market():
    current_time = dt.datetime.now().time()
    day_of_week = dt.date.today().weekday()

    market_open = dt.time(9, 30, 0)
    market_close = dt.time(15, 59, 0)

    weekday = 0 <= day_of_week <= 5

    market = weekday and market_open <= current_time <= market_close

    if not market:
        print("AFTER HOURS")

    return market

class Stock:
    def __init__(self, ticker):
        self.ticker = ticker
        self.sma_hour = 0
        self.run_time = 0
        self.price_sma_hour = 0

    def get_price(self):
        self.price = rh.stocks.get_latest_price(self.ticker)
        return [self.ticker, float(self.price[0])]

    def get_historical_prices(self, span):
        span_interval = {'day': '5minute', 'week': '10minute', 'month': 'hour', '3month': 'hour', 'year': 'day', '5year': 'week'}
        interval = span_interval[span]

        historical_data = rh.stocks.get_stock_historicals(self.ticker, interval, span, bounds='extended')

        df = pd.DataFrame(historical_data)
        date_times = pd.to_datetime(df.loc[:, 'begins_at'])
        close_prices = df.loc[:, 'close_price'].astype('float')

        df_price = pd.concat([close_prices, date_times], axis=1)
        df_price = df_price.rename(columns={'close_price': self.ticker})
        df_price = df_price.set_index('begins_at')

        # Calculate EMA for 20, 50, 100, and 200 periods
        df_price['ema_20'] = ta.trend.ema_indicator(df_price[self.ticker], window=20, fillna=True)
        df_price['ema_50'] = ta.trend.ema_indicator(df_price[self.ticker], window=50, fillna=True)
        df_price['ema_100'] = ta.trend.ema_indicator(df_price[self.ticker], window=100, fillna=True)
        df_price['ema_200'] = ta.trend.ema_indicator(df_price[self.ticker], window=200, fillna=True)

        return df_price

    def get_sma(self, df_prices, window=12):
        if df_prices.empty or len(df_prices) < window:
            return None  # Return None if there is not enough data for SMA calculation

        sma = df_prices[self.ticker].rolling(window, min_periods=window).mean()
        return round(float(sma.iloc[-1]), 4)

    def get_price_sma(self, span='day'):
        df_historical_prices = self.get_historical_prices(span)
        current_price = rh.stocks.get_latest_price(self.ticker, includeExtendedHours=True)[0]
        sma = self.get_sma(df_historical_prices)
        price_sma_ratio = round(float(current_price) / sma, 4)
        return price_sma_ratio

    def get_ema_diff(self, df_prices, ema_period):
        # Calculate the difference between the stock price and EMA for the specified period
        ema_diff = df_prices[self.ticker] - df_prices[f'ema_{ema_period}']
        return round(float(ema_diff.iloc[-1]), 4)

    def get_ema_diffs(self, span='day'):
        df_historical_prices = self.get_historical_prices(span)
        ema_20_diff = self.get_ema_diff(df_historical_prices, 20)
        ema_50_diff = self.get_ema_diff(df_historical_prices, 50)
        ema_100_diff = self.get_ema_diff(df_historical_prices, 100)
        ema_200_diff = self.get_ema_diff(df_historical_prices, 200)
        return ema_20_diff, ema_50_diff, ema_100_diff, ema_200_diff

    def get_macd(self, df_prices, window_slow=24, window_fast=52, window_signal=18):
        df_prices['macd'] = ta.trend.macd(df_prices[self.ticker], window_slow=window_slow, window_fast=window_fast, fillna=True)
        df_prices['signal'] = ta.trend.macd_signal(df_prices[self.ticker], window_slow=window_slow, window_fast=window_fast, window_sign=window_signal, fillna=True)

    def implement_macd_strategy(self, span='day'):
        df_historical_prices = self.get_historical_prices(span)
        self.get_macd(df_historical_prices)
        last_macd = df_historical_prices['macd'].iloc[-1]
        last_signal = df_historical_prices['signal'].iloc[-1]
        if last_macd > last_signal:
            decision = "Buy Signal"
        elif last_macd < last_signal:
            decision = "Sell Signal"
        else:
            decision = "No Signal"
        return f' - MACD: {last_macd}, Signal: {last_signal}, Decision: {decision},'
    
    def get_rsi(self, df_prices, window=14):
        if df_prices.empty or len(df_prices) < window:
            return None  # Return None if there is not enough data for RSI calculation

        close_prices = df_prices[self.ticker]
        rsi = ta.momentum.RSIIndicator(close_prices, window=window, fillna=True).rsi()

        return round(float(rsi.iloc[-1]), 4)

    def implement_rsi_strategy(self, span='day'):
        df_historical_prices = self.get_historical_prices(span)
        rsi_value = self.get_rsi(df_historical_prices)
        
        # Adjust the threshold values based on your strategy
        overbought_threshold = 70
        oversold_threshold = 30

        if rsi_value is not None:
            if rsi_value > overbought_threshold:
                decision = "Overbought Signal"
            elif rsi_value < oversold_threshold:
                decision = "Oversold Signal"
            else:
                decision = "No Signal"
            
            return f' - RSI: {rsi_value}, Decision: {decision}'
        else:
            return "Not enough data for RSI calculation."
        
if __name__ == "__main__":
    login()
    
    stocks = ['AAPL', 'NVDA']
    for stock in stocks:
        stock_info = Stock(stock)
        price = stock_info.get_price()
        df_historical_prices = stock_info.get_historical_prices(span="day")
        
        # Adjust the call to get_sma to pass the DataFrame
        sma_value = stock_info.get_sma(df_historical_prices)
        
        # Continue with the rest of your code...
        price_sma = stock_info.get_price_sma(span='day')
        macd_strategy_result = stock_info.implement_macd_strategy(span='day')
        ema_diffs = stock_info.get_ema_diffs(span='day')
        
        print(f'{stock_info.ticker}:')
        print(f' - Price: {price}')
        
        # Check if sma_value is not None before printing
        if sma_value is not None:
            print(f' - SMA: {sma_value}, Price/SMA: {price_sma}')
        else:
            print(f' - Not enough data for SMA calculation.')
        
        print(macd_strategy_result)
        print(f' - EMA Diffs: 20: {ema_diffs[0]}, 50: {ema_diffs[1]}, 100: {ema_diffs[2]}, 200: {ema_diffs[3]}')

        rsi_strategy_result = stock_info.implement_rsi_strategy(span='day')
        print(rsi_strategy_result)

    logout()
