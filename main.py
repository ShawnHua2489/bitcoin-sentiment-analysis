import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from twitter_collector import TwitterCollector
from reddit_collector import RedditCollector
from price_collector import PriceCollector
from config import *

def create_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

def analyze_sentiment_correlation(tweets_df, reddit_df, price_df):
    """Analyze correlation between social media sentiment and price movements"""
    # Get sentiment data from both sources
    tweets_sentiment = tweets_df.groupby(pd.Grouper(key='created_at', freq='1H'))['sentiment_polarity'].mean()
    reddit_sentiment = reddit_df.groupby(pd.Grouper(key='created_at', freq='1H'))['title_sentiment_polarity'].mean()
    
    # Combine sentiment data
    combined_sentiment = pd.concat([tweets_sentiment, reddit_sentiment]).groupby(level=0).mean()
    
    # Align price and sentiment data
    price_df.set_index('timestamp', inplace=True)
    combined_data = pd.concat([price_df['price_change'], combined_sentiment], axis=1, join='inner')
    combined_data.columns = ['price_change', 'sentiment']
    
    # Calculate correlation
    correlation = combined_data.corr()
    
    # Plot correlation
    plt.figure(figsize=(10, 6))
    sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0)
    plt.title('Correlation between Bitcoin Price Changes and Social Media Sentiment')
    plt.savefig(f'{RESULTS_DIR}/correlation_heatmap_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    
    # Plot sentiment over time
    plt.figure(figsize=(12, 6))
    plt.plot(combined_data.index, combined_data['sentiment'], label='Combined Sentiment')
    plt.plot(combined_data.index, combined_data['price_change'], label='Price Change (%)')
    plt.title('Bitcoin Price Changes and Social Media Sentiment Over Time')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'{RESULTS_DIR}/sentiment_price_timeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    
    return correlation

def main():
    create_directories()
    
    # Collect data
    print("\nCollecting Twitter data...")
    twitter_collector = TwitterCollector()
    tweets_df = twitter_collector.collect_bitcoin_tweets()
    
    print("\nCollecting Reddit data...")
    reddit_collector = RedditCollector()
    reddit_df = reddit_collector.collect_bitcoin_posts()
    
    print("\nCollecting price data...")
    price_collector = PriceCollector()
    price_df = price_collector.collect_bitcoin_prices()
    
    # Analyze correlation
    if not tweets_df.empty and not reddit_df.empty and not price_df.empty:
        print("\nAnalyzing sentiment correlation...")
        correlation = analyze_sentiment_correlation(tweets_df, reddit_df, price_df)
        print("\nCorrelation Analysis Results:")
        print(correlation)
        
        # Print summary statistics
        print("\nSummary Statistics:")
        print(f"Total Tweets Analyzed: {len(tweets_df)}")
        print(f"Total Reddit Posts Analyzed: {len(reddit_df)}")
        print(f"Average Tweet Sentiment: {tweets_df['sentiment_polarity'].mean():.3f}")
        print(f"Average Reddit Post Sentiment: {reddit_df['title_sentiment_polarity'].mean():.3f}")
    else:
        print("Error: Not enough data collected for analysis")

if __name__ == "__main__":
    main() 