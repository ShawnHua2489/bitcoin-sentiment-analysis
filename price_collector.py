import ccxt
import pandas as pd
from datetime import datetime, timedelta
from config import *

class PriceCollector:
    def __init__(self):
        self.exchange = ccxt.binance()  # Using Binance as the exchange
        
    def get_historical_prices(self, symbol='BTC/USDT', timeframe='1h', limit=24):
        try:
            # Get OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calculate price changes
            df['price_change'] = df['close'].pct_change() * 100
            df['price_change_24h'] = (df['close'] - df['close'].shift(24)) / df['close'].shift(24) * 100
            
            return df
            
        except Exception as e:
            print(f"Error fetching price data: {str(e)}")
            return pd.DataFrame()
    
    def collect_bitcoin_prices(self):
        prices = self.get_historical_prices()
        
        if not prices.empty:
            # Save to CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            prices.to_csv(f'{DATA_DIR}/price_data_{timestamp}.csv', index=False)
        
        return prices 