import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
# from twitter_collector import TwitterCollector
from reddit_collector import RedditCollector
from price_collector import PriceCollector
# from news_collector import NewsCollector
from trends_collector import TrendsCollector
from config import *

def create_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

def analyze_sentiment_correlation(reddit_df, trends_df, price_df):
    """Analyze correlation between various sentiment indicators and price movements"""
    # Get sentiment data from Reddit
    reddit_sentiment = reddit_df.groupby(pd.Grouper(key='created_at', freq='1H'))['title_sentiment_polarity'].mean()
    
    # Align all data
    price_df.set_index('timestamp', inplace=True)
    trends_df.index = pd.to_datetime(trends_df.index)
    
    # Create combined DataFrame
    combined_data = pd.concat([
        price_df['price_change'],
        reddit_sentiment,
        trends_df['bitcoin_combined_interest'],
        trends_df['trump_combined_interest']
    ], axis=1, join='inner')
    combined_data.columns = ['price_change', 'sentiment', 'bitcoin_interest', 'trump_interest']
    
    # Calculate correlation
    correlation = combined_data.corr()
    
    # Plot correlation heatmap
    plt.figure(figsize=(10, 6))
    sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0)
    plt.title('Correlation between Bitcoin Price, Reddit Sentiment, and Search Interest')
    plt.savefig(f'{RESULTS_DIR}/correlation_heatmap_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    
    # Plot time series
    plt.figure(figsize=(12, 6))
    plt.plot(combined_data.index, combined_data['sentiment'], label='Reddit Sentiment')
    plt.plot(combined_data.index, combined_data['bitcoin_interest'], label='Bitcoin Search Interest')
    plt.plot(combined_data.index, combined_data['trump_interest'], label='Trump Search Interest')
    plt.plot(combined_data.index, combined_data['price_change'], label='Price Change (%)')
    plt.title('Bitcoin Indicators Over Time')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'{RESULTS_DIR}/indicators_timeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    
    # Print correlation analysis
    print("\nCorrelation Analysis:")
    print(f"Correlation between Bitcoin price and Trump search interest: {correlation.loc['price_change', 'trump_interest']:.3f}")
    print(f"Correlation between Bitcoin search interest and Trump search interest: {correlation.loc['bitcoin_interest', 'trump_interest']:.3f}")
    
    return correlation

def main():
    create_directories()
    
    # Collect data
    print("\nCollecting Reddit data...")
    reddit_collector = RedditCollector()
    reddit_df = reddit_collector.collect_bitcoin_posts()
    
    print("\nCollecting Google Trends data...")
    trends_collector = TrendsCollector()
    trends_df = trends_collector.collect_bitcoin_trends()
    
    print("\nCollecting price data...")
    price_collector = PriceCollector()
    price_df = price_collector.collect_bitcoin_prices()
    
    # Analyze correlation
    if not reddit_df.empty and not trends_df.empty and not price_df.empty:
        print("\nAnalyzing sentiment correlation...")
        correlation = analyze_sentiment_correlation(reddit_df, trends_df, price_df)
        print("\nCorrelation Analysis Results:")
        print(correlation)
        
        # Print summary statistics
        print("\nSummary Statistics:")
        print(f"Total Reddit Posts Analyzed: {len(reddit_df)}")
        print(f"Average Reddit Post Sentiment: {reddit_df['title_sentiment_polarity'].mean():.3f}")
        print(f"Average Search Interest: {trends_df['bitcoin_combined_interest'].mean():.2f}")
    else:
        print("Error: Not enough data collected for analysis")

if __name__ == "__main__":
    main() 