import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
# from twitter_collector import TwitterCollector
from reddit_collector import RedditCollector
from price_collector import PriceCollector
from news_collector import NewsCollector
from trends_collector import TrendsCollector
from trump_collector import TrumpCollector
from truth_collector import TruthCollector
from config import *

def create_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

def analyze_truth_impact(truth_df, price_df, hours_before=6, hours_after=6):
    """Analyze Bitcoin price movements around Trump's Truth Social posts"""
    if truth_df.empty or price_df.empty:
        print("Not enough data for analysis")
        return
        
    try:
        # Convert timestamps
        price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
        truth_df['created_at'] = pd.to_datetime(truth_df['created_at'])
        
        # Filter data from January 1, 2025
        start_date = datetime(2025, 1, 1)
        truth_df = truth_df[truth_df['created_at'] >= start_date]
        price_df = price_df[price_df['timestamp'] >= start_date]
        
        # Print data range information
        print("\nData Range Information:")
        print(f"Truth Social posts: {truth_df['created_at'].min()} to {truth_df['created_at'].max()}")
        print(f"Price data: {price_df['timestamp'].min()} to {price_df['timestamp'].max()}")
        
        results = []
        for _, post in truth_df.iterrows():
            post_time = post['created_at']
            start_time = post_time - timedelta(hours=hours_before)
            end_time = post_time + timedelta(hours=hours_after)
            
            # Get price data around the post
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
                    'post_time': post_time,
                    'text': post['text'],
                    'replies': post['replies'],
                    'reblogs': post['reblogs'],
                    'favorites': post['favorites'],
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
            results_file = os.path.join(RESULTS_DIR, f'truth_impact_analysis_{start_date.date()}_to_{datetime.now().date()}_{timestamp}.csv')
            results_df.to_csv(results_file, index=False)
            print(f"\nAnalysis results saved to: {results_file}")
            
            # Plot price changes by engagement
            plt.figure(figsize=(12, 6))
            sns.scatterplot(x='favorites', y='price_change', data=results_df)
            plt.axhline(y=0, color='r', linestyle='-')
            plt.title('Bitcoin Price Change vs. Post Favorites (2025)')
            plt.xlabel('Number of Favorites')
            plt.ylabel('Price Change (%)')
            plt.tight_layout()
            plt.savefig(f'{RESULTS_DIR}/truth_impact_by_favorites_{timestamp}.png')
            
            # Plot price changes over time
            plt.figure(figsize=(12, 6))
            sns.lineplot(x='post_time', y='price_change', data=results_df)
            plt.axhline(y=0, color='r', linestyle='-')
            plt.title('Bitcoin Price Change After Truth Social Posts (2025)')
            plt.xlabel('Post Time')
            plt.ylabel('Price Change (%)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'{RESULTS_DIR}/truth_impact_over_time_{timestamp}.png')
            
            # Calculate correlations
            print("\nCorrelation Analysis:")
            print("\nPrice Change vs. Engagement:")
            print(results_df[['price_change', 'replies', 'reblogs', 'favorites']].corr())
            
            # Print most impactful posts
            print("\nMost Impactful Posts:")
            top_impact = results_df.nlargest(3, 'price_change')
            for _, row in top_impact.iterrows():
                print(f"\n{row['post_time']}:")
                print(f"Text: {row['text'][:100]}...")
                print(f"Price Change: {row['price_change']:.2f}%")
                print(f"Engagement: {row['replies']} replies, {row['reblogs']} reblogs, {row['favorites']} favorites")
            
            return results_df
            
    except Exception as e:
        print(f"Error in impact analysis: {str(e)}")
        return None

def analyze_trump_announcements(announcements_df, price_df, hours_before=6, hours_after=6):
    """Analyze Bitcoin price movements around Trump's announcements"""
    if announcements_df.empty or price_df.empty:
        print("Not enough data for analysis")
        return
        
    try:
        # Convert timestamps
        price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
        announcements_df['published_at'] = pd.to_datetime(announcements_df['published_at'])
        
        # Filter data from January 1, 2025
        start_date = datetime(2025, 1, 1)
        announcements_df = announcements_df[announcements_df['published_at'] >= start_date]
        price_df = price_df[price_df['timestamp'] >= start_date]
        
        # Print data range information
        print("\nData Range Information:")
        print(f"Trump announcements: {announcements_df['published_at'].min()} to {announcements_df['published_at'].max()}")
        print(f"Price data: {price_df['timestamp'].min()} to {price_df['timestamp'].max()}")
        
        results = []
        for _, announcement in announcements_df.iterrows():
            announcement_time = announcement['published_at']
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
                    'text': announcement['description'],
                    'source': announcement['source'],
                    'url': announcement['url'],
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
            results_file = os.path.join(RESULTS_DIR, f'trump_announcements_impact_{start_date.date()}_to_{datetime.now().date()}_{timestamp}.csv')
            results_df.to_csv(results_file, index=False)
            print(f"\nAnalysis results saved to: {results_file}")
            
            # Plot price changes by source
            plt.figure(figsize=(12, 6))
            sns.scatterplot(x='source', y='price_change', data=results_df)
            plt.axhline(y=0, color='r', linestyle='-')
            plt.title('Bitcoin Price Change vs. News Source (2025)')
            plt.xlabel('News Source')
            plt.ylabel('Price Change (%)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'{RESULTS_DIR}/trump_impact_by_source_{timestamp}.png')
            
            # Plot price changes over time
            plt.figure(figsize=(12, 6))
            sns.lineplot(x='announcement_time', y='price_change', data=results_df)
            plt.axhline(y=0, color='r', linestyle='-')
            plt.title('Bitcoin Price Change After Trump Announcements (2025)')
            plt.xlabel('Announcement Time')
            plt.ylabel('Price Change (%)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'{RESULTS_DIR}/trump_impact_over_time_{timestamp}.png')
            
            # Calculate correlations
            print("\nCorrelation Analysis:")
            print("\nPrice Change vs. Source:")
            print(results_df[['price_change', 'source']].corr())
            
            # Print most impactful announcements
            print("\nMost Impactful Announcements:")
            top_impact = results_df.nlargest(3, 'price_change')
            for _, row in top_impact.iterrows():
                print(f"\n{row['announcement_time']}:")
                print(f"Title: {row['title']}")
                print(f"Price Change: {row['price_change']:.2f}%")
                print(f"Source: {row['source']}")
                print(f"URL: {row['url']}")
            
            return results_df
            
    except Exception as e:
        print(f"Error in impact analysis: {str(e)}")
        return None

def main():
    create_directories()
    
    # Set start date to January 1, 2025
    start_date = datetime(2025, 1, 1)
    
    # Collect Trump announcements from NewsAPI
    print("\nCollecting Trump announcements from NewsAPI...")
    news_collector = NewsCollector()
    announcements_df = news_collector.get_news(
        query='trump AND (bitcoin OR crypto OR cryptocurrency)',
        max_articles=100
    )
    
    # Collect Bitcoin price data
    print("\nCollecting Bitcoin price data...")
    price_collector = PriceCollector()
    price_df = price_collector.collect_bitcoin_prices(start_date=start_date)
    
    # Analyze impact of Trump announcements
    if not announcements_df.empty and not price_df.empty:
        print("\nAnalyzing impact of Trump announcements on Bitcoin price...")
        results = analyze_trump_announcements(announcements_df, price_df)
    
    # Print summary statistics
    print("\nSummary Statistics:")
    if not announcements_df.empty:
        print(f"Total Trump announcements analyzed: {len(announcements_df)}")
        print(f"News sources: {announcements_df['source'].nunique()}")
        print(f"Time window analyzed: 6 hours before and after each announcement")
        print(f"Analysis period: {start_date.date()} to present")
        print(f"Total NewsAPI requests made: {news_collector.request_count}")

if __name__ == "__main__":
    main() 