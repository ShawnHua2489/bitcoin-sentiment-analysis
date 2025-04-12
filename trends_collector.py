from pytrends.request import TrendReq
import pandas as pd
from datetime import datetime, timedelta
import os
from config import *

class TrendsCollector:
    def __init__(self):
        try:
            # Initialize pytrends
            self.pytrends = TrendReq(hl='en-US', tz=360)
            print("Successfully connected to Google Trends")
        except Exception as e:
            print(f"Error connecting to Google Trends: {str(e)}")
            raise

    def get_trends(self, bitcoin_keywords=['bitcoin', 'btc', 'crypto'], 
                  trump_keywords=['donald trump', 'trump', 'president trump'],
                  timeframe='now 1-d'):
        try:
            print(f"Searching for trends with Bitcoin keywords: {bitcoin_keywords}")
            print(f"Searching for trends with Trump keywords: {trump_keywords}")
            
            # Build payload for Bitcoin keywords
            self.pytrends.build_payload(
                kw_list=bitcoin_keywords,
                timeframe=timeframe,
                geo=''
            )
            
            # Get interest over time for Bitcoin
            bitcoin_trends = self.pytrends.interest_over_time()
            
            # Build payload for Trump keywords
            self.pytrends.build_payload(
                kw_list=trump_keywords,
                timeframe=timeframe,
                geo=''
            )
            
            # Get interest over time for Trump
            trump_trends = self.pytrends.interest_over_time()
            
            if not bitcoin_trends.empty and not trump_trends.empty:
                print(f"Found trends data for {len(bitcoin_trends)} time points")
                
                # Calculate combined Bitcoin interest
                bitcoin_trends['bitcoin_combined_interest'] = bitcoin_trends[bitcoin_keywords].mean(axis=1)
                
                # Calculate combined Trump interest
                trump_trends['trump_combined_interest'] = trump_trends[trump_keywords].mean(axis=1)
                
                # Combine the dataframes
                trends_df = pd.concat([
                    bitcoin_trends['bitcoin_combined_interest'],
                    trump_trends['trump_combined_interest']
                ], axis=1)
                
                # Print sample data
                print("\nSample Search Interest Data:")
                print("Time\t\tBitcoin\tTrump")
                for i in range(min(5, len(trends_df))):
                    row = trends_df.iloc[i]
                    print(f"{row.name}\t{row['bitcoin_combined_interest']:.1f}\t{row['trump_combined_interest']:.1f}")
                
                # Calculate interest changes
                trends_df['bitcoin_interest_change'] = trends_df['bitcoin_combined_interest'].pct_change() * 100
                trends_df['trump_interest_change'] = trends_df['trump_combined_interest'].pct_change() * 100
                
            else:
                print("No trends data found")
                trends_df = pd.DataFrame()
                
        except Exception as e:
            print(f"Error collecting trends data: {str(e)}")
            trends_df = pd.DataFrame()
            
        return trends_df

    def collect_bitcoin_trends(self):
        trends = self.get_trends()
        
        if not trends.empty:
            # Save to CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(DATA_DIR, f'trends_data_{timestamp}.csv')
            trends.to_csv(file_path)
            print(f"\nTrends data saved to: {file_path}")
            
            # Print summary statistics
            print("\nTrends Summary:")
            print(f"Average combined interest: {trends['bitcoin_combined_interest'].mean():.2f}")
            print(f"Maximum combined interest: {trends['bitcoin_combined_interest'].max():.2f}")
            print(f"Minimum combined interest: {trends['bitcoin_combined_interest'].min():.2f}")
        else:
            print("\nNo trends data was collected")
        
        return trends 