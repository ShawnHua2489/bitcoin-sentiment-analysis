import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
# from twitter_collector import TwitterCollector
from reddit_collector import RedditCollector
from price_collector import PriceCollector
# from news_collector import NewsCollector
from trends_collector import TrendsCollector
from trump_collector import TrumpCollector
from config import *

def create_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

def analyze_announcement_impact(trump_df, price_df, hours_before=6, hours_after=6):
    """Analyze Bitcoin price movements around Trump announcements"""
    if trump_df.empty or price_df.empty:
        print("Not enough data for analysis")
        return
        
    try:
        # Convert timestamps
        price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
        trump_df['created_at'] = pd.to_datetime(trump_df['created_at'])
        
        # Filter data from January 1, 2025
        start_date = datetime(2025, 1, 1)
        trump_df = trump_df[trump_df['created_at'] >= start_date]
        price_df = price_df[price_df['timestamp'] >= start_date]
        
        # Print data range information
        print("\nData Range Information:")
        print(f"Trump announcements: {trump_df['created_at'].min()} to {trump_df['created_at'].max()}")
        print(f"Price data: {price_df['timestamp'].min()} to {price_df['timestamp'].max()}")
        
        results = []
        for _, announcement in trump_df.iterrows():
            announcement_time = announcement['created_at']
            start_time = announcement_time - timedelta(hours=hours_before)
            end_time = announcement_time + timedelta(hours=hours_after)
            
            # Get price data around the announcement
            price_window = price_df[
                (price_df['timestamp'] >= start_time) & 
                (price_df['timestamp'] <= end_time)
            ]
            
            if not price_window.empty:
                # Calculate price changes
                initial_price = price_window.iloc[0]['close']
                final_price = price_window.iloc[-1]['close']
                price_change = ((final_price - initial_price) / initial_price) * 100
                
                # Calculate max and min prices
                max_price = price_window['close'].max()
                min_price = price_window['close'].min()
                max_change = ((max_price - initial_price) / initial_price) * 100
                min_change = ((min_price - initial_price) / initial_price) * 100
                
                results.append({
                    'announcement_time': announcement_time,
                    'title': announcement['title'],
                    'subreddit': announcement['subreddit'],
                    'content_type': announcement['content_type'],
                    'is_direct': announcement['is_direct'],
                    'sentiment_polarity': announcement['sentiment_polarity'],
                    'sentiment_subjectivity': announcement['sentiment_subjectivity'],
                    'score': announcement['score'],
                    'num_comments': announcement['num_comments'],
                    'price_change': price_change,
                    'max_change': max_change,
                    'min_change': min_change,
                    'initial_price': initial_price,
                    'final_price': final_price,
                    'max_price': max_price,
                    'min_price': min_price
                })
        
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            # Save results to CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = os.path.join(RESULTS_DIR, f'trump_impact_analysis_{start_date.date()}_to_{datetime.now().date()}_{timestamp}.csv')
            results_df.to_csv(results_file, index=False)
            print(f"\nAnalysis results saved to: {results_file}")
            
            # Plot price changes by content type
            plt.figure(figsize=(12, 6))
            sns.boxplot(x='content_type', y='price_change', data=results_df)
            plt.axhline(y=0, color='r', linestyle='-')
            plt.title('Bitcoin Price Change After Trump Announcements by Type (2025)')
            plt.xlabel('Announcement Type')
            plt.ylabel('Price Change (%)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'{RESULTS_DIR}/trump_impact_by_type_{timestamp}.png')
            
            # Plot price changes by sentiment
            plt.figure(figsize=(12, 6))
            sns.scatterplot(x='sentiment_polarity', y='price_change', 
                          hue='content_type', data=results_df)
            plt.axhline(y=0, color='r', linestyle='-')
            plt.axvline(x=0, color='r', linestyle='-')
            plt.title('Bitcoin Price Change vs. Announcement Sentiment (2025)')
            plt.xlabel('Sentiment Polarity')
            plt.ylabel('Price Change (%)')
            plt.tight_layout()
            plt.savefig(f'{RESULTS_DIR}/trump_impact_by_sentiment_{timestamp}.png')
            
            # Calculate correlations
            print("\nCorrelation Analysis:")
            print("\nPrice Change vs. Sentiment:")
            print(results_df[['price_change', 'sentiment_polarity', 'sentiment_subjectivity']].corr())
            
            print("\nPrice Change vs. Engagement:")
            print(results_df[['price_change', 'score', 'num_comments']].corr())
            
            # Analyze by content type
            print("\nImpact Analysis by Content Type:")
            for content_type in results_df['content_type'].unique():
                type_df = results_df[results_df['content_type'] == content_type]
                print(f"\n{content_type} announcements:")
                print(f"Average price change: {type_df['price_change'].mean():.2f}%")
                print(f"Maximum price change: {type_df['price_change'].max():.2f}%")
                print(f"Minimum price change: {type_df['price_change'].min():.2f}%")
                print(f"Number of announcements: {len(type_df)}")
            
            # Analyze direct vs. indirect announcements
            print("\nImpact Analysis by Announcement Type:")
            for is_direct in [True, False]:
                type_df = results_df[results_df['is_direct'] == is_direct]
                print(f"\n{'Direct' if is_direct else 'Indirect'} announcements:")
                print(f"Average price change: {type_df['price_change'].mean():.2f}%")
                print(f"Maximum price change: {type_df['price_change'].max():.2f}%")
                print(f"Minimum price change: {type_df['price_change'].min():.2f}%")
                print(f"Number of announcements: {len(type_df)}")
            
            # Print most impactful announcements
            print("\nMost Impactful Announcements:")
            top_impact = results_df.nlargest(3, 'price_change')
            for _, row in top_impact.iterrows():
                print(f"\n{row['announcement_time']}: {row['title']}")
                print(f"Type: {'Direct' if row['is_direct'] else 'Indirect'} {row['content_type']} announcement")
                print(f"Sentiment: {row['sentiment_polarity']:.2f} (polarity)")
                print(f"Price Change: {row['price_change']:.2f}%")
                print(f"Subreddit: r/{row['subreddit']}")
            
            return results_df
            
    except Exception as e:
        print(f"Error in impact analysis: {str(e)}")
        return None

def main():
    create_directories()
    
    # Set start date to January 1, 2025
    start_date = datetime(2025, 1, 1)
    
    # Collect Trump announcements
    print("\nCollecting Trump announcements...")
    trump_collector = TrumpCollector()
    trump_df = trump_collector.get_trump_announcements(start_date=start_date)
    
    # Collect Bitcoin price data
    print("\nCollecting Bitcoin price data...")
    price_collector = PriceCollector()
    price_df = price_collector.collect_bitcoin_prices(start_date=start_date)
    
    # Analyze impact
    if not trump_df.empty and not price_df.empty:
        print("\nAnalyzing impact of Trump announcements on Bitcoin price...")
        results = analyze_announcement_impact(trump_df, price_df)
        
        # Print summary statistics
        print("\nSummary Statistics:")
        print(f"Total Trump announcements analyzed: {len(trump_df)}")
        print(f"Time window analyzed: 6 hours before and after each announcement")
        print(f"Analysis period: {start_date.date()} to present")
    else:
        print("Error: Not enough data collected for analysis")

if __name__ == "__main__":
    main() 