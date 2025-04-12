import ccxt
import pandas as pd
from datetime import datetime, timedelta
import os
from config import *

class PriceCollector:
    def __init__(self):
        self.exchange = ccxt.binance()  # Using Binance as the exchange
        
    def get_historical_prices(self, symbol='BTC/USDT', timeframe='1h', start_date=None):
        try:
            if start_date is None:
                start_date = datetime(2025, 1, 1)
            
            print(f"\nFetching Bitcoin price data from {start_date} to present...")
            
            # Convert start_date to milliseconds timestamp
            since = int(start_date.timestamp() * 1000)
            
            # Get OHLCV data
            ohlcv = []
            while True:
                # Fetch data in chunks of 1000 candles
                chunk = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                if not chunk:
                    break
                
                ohlcv.extend(chunk)
                since = chunk[-1][0] + 1  # Next timestamp after the last candle
                
                # If we've reached the present, stop
                if since > int(datetime.now().timestamp() * 1000):
                    break
                
                print(f"Fetched {len(chunk)} candles up to {datetime.fromtimestamp(since/1000)}")
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calculate price changes
            df['price_change'] = df['close'].pct_change() * 100
            
            return df
            
        except Exception as e:
            print(f"Error fetching price data: {str(e)}")
            return pd.DataFrame()
    
    def collect_bitcoin_prices(self, start_date=None):
        print("\nFetching fresh Bitcoin price data...")
        prices = self.get_historical_prices(start_date=start_date)
        
        if not prices.empty:
            # Save to CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(DATA_DIR, f'price_data_{start_date.date()}_to_{datetime.now().date()}_{timestamp}.csv')
            prices.to_csv(file_path, index=False)
            print(f"Successfully collected {len(prices)} hours of price data")
            print(f"Data saved to: {file_path}")
            
            # Print sample data
            print("\nSample of price data:")
            print(prices[['timestamp', 'close', 'price_change']].head())
            print("\n...")
            print(prices[['timestamp', 'close', 'price_change']].tail())
            
            # Print summary statistics
            print("\nPrice Data Summary:")
            print(f"Date range: {prices['timestamp'].min()} to {prices['timestamp'].max()}")
            print(f"Total hours of data: {len(prices)}")
            print(f"Average price: ${prices['close'].mean():.2f}")
            print(f"Maximum price: ${prices['close'].max():.2f}")
            print(f"Minimum price: ${prices['close'].min():.2f}")
        else:
            print("Error: No price data was collected")
        
        return prices 