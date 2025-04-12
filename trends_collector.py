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

    def get_trends(self, keywords=['bitcoin', 'btc', 'crypto'], timeframe='now 1-d'):
        try:
            print(f"Searching for trends with keywords: {keywords}")
            
            # Build payload
            self.pytrends.build_payload(
                kw_list=keywords,
                timeframe=timeframe,
                geo=''
            )
            
            # Get interest over time
            trends_df = self.pytrends.interest_over_time()
            
            if not trends_df.empty:
                print(f"Found trends data for {len(trends_df)} time points")
                
                # Calculate combined interest
                trends_df['combined_interest'] = trends_df[keywords].mean(axis=1)
                
                # Calculate interest changes
                for keyword in keywords:
                    trends_df[f'{keyword}_change'] = trends_df[keyword].pct_change() * 100
                trends_df['combined_interest_change'] = trends_df['combined_interest'].pct_change() * 100
                
            else:
                print("No trends data found")
                
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
            print(f"Average combined interest: {trends['combined_interest'].mean():.2f}")
            print(f"Maximum combined interest: {trends['combined_interest'].max():.2f}")
            print(f"Minimum combined interest: {trends['combined_interest'].min():.2f}")
        else:
            print("\nNo trends data was collected")
        
        return trends 