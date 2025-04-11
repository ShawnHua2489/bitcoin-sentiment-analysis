import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from reddit_collector import RedditCollector
from price_collector import PriceCollector
from config import *

def create_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

def analyze_sentiment_correlation(reddit_df, price_df):
    """Analyze correlation between Reddit sentiment and price movements"""
    # Get sentiment data
    reddit_sentiment = reddit_df.groupby(pd.Grouper(key='created_at', freq='1H'))['title_sentiment_polarity'].mean()
    
    # Align price and sentiment data
    price_df.set_index('timestamp', inplace=True)
    combined_data = pd.concat([price_df['price_change'], reddit_sentiment], axis=1, join='inner')
    combined_data.columns = ['price_change', 'sentiment']
    
    # Calculate correlation
    correlation = combined_data.corr()
    
    # Plot correlation
    plt.figure(figsize=(10, 6))
    sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0)
    plt.title('Correlation between Bitcoin Price Changes and Reddit Sentiment')
    plt.savefig(f'{RESULTS_DIR}/correlation_heatmap_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    
    return correlation

def main():
    create_directories()
    
    # Collect data
    print("\nCollecting Reddit data...")
    reddit_collector = RedditCollector()
    reddit_df = reddit_collector.collect_bitcoin_posts()
    
    print("\nCollecting price data...")
    price_collector = PriceCollector()
    price_df = price_collector.collect_bitcoin_prices()
    
    # Analyze correlation
    if not reddit_df.empty and not price_df.empty:
        print("\nAnalyzing sentiment correlation...")
        correlation = analyze_sentiment_correlation(reddit_df, price_df)
        print("\nCorrelation Analysis Results:")
        print(correlation)
    else:
        print("Error: Not enough data collected for analysis")

if __name__ == "__main__":
    main() 