import praw
import pandas as pd
from datetime import datetime, timedelta
import os
from config import *
from textblob import TextBlob

class TrumpCollector:
    def __init__(self):
        try:
            self.reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT
            )
            print("Successfully connected to Reddit API for Trump announcements")
        except Exception as e:
            print(f"Error connecting to Reddit API: {str(e)}")
            raise

    def categorize_announcement(self, title, text):
        """Categorize the type of announcement and determine if it's a direct Trump statement"""
        # Convert to lowercase for case-insensitive matching
        title_lower = title.lower()
        text_lower = text.lower() if text else title_lower
        
        # Direct statement indicators
        direct_indicators = [
            'trump says', 'trump announces', 'trump declares', 'trump tweets',
            'trump statement', 'trump statement on', 'trump:', 'trump stated',
            'trump commented', 'trump remarked', 'trump made clear',
            'trump made it clear', 'trump made the announcement',
            'trump made the statement', 'trump made the comment',
            'trump made the remark', 'trump made the declaration'
        ]
        
        # Crypto-related keywords
        crypto_keywords = [
            'bitcoin', 'btc', 'crypto', 'cryptocurrency', 'digital currency',
            'blockchain', 'digital asset', 'digital gold', 'crypto asset',
            'crypto currency', 'crypto market', 'crypto regulation',
            'crypto policy', 'crypto ban', 'crypto tax', 'crypto mining'
        ]
        
        # Determine if it's a direct Trump statement
        is_direct = any(indicator in title_lower for indicator in direct_indicators)
        
        # Check if it's crypto-related
        is_crypto = any(keyword in title_lower or keyword in text_lower 
                       for keyword in crypto_keywords)
        
        # Analyze sentiment
        title_sentiment = TextBlob(title).sentiment
        text_sentiment = TextBlob(text).sentiment if text else title_sentiment
        
        # Determine the type of content
        content_type = 'other'
        if is_crypto:
            content_type = 'crypto'
        elif any(keyword in title_lower for keyword in ['trade', 'tariff', 'economy', 'market']):
            content_type = 'trade'
        elif any(keyword in title_lower for keyword in ['policy', 'decision', 'action', 'order']):
            content_type = 'policy'
        elif any(keyword in title_lower for keyword in ['election', 'campaign', 'president']):
            content_type = 'political'
        elif any(keyword in title_lower for keyword in ['court', 'trial', 'investigation']):
            content_type = 'legal'
        
        # Calculate confidence score
        confidence_score = 0
        if is_direct:
            confidence_score += 0.4
        if is_crypto:
            confidence_score += 0.3
        if content_type == 'crypto':
            confidence_score += 0.3
        
        return {
            'is_direct': is_direct,
            'is_crypto': is_crypto,
            'content_type': content_type,
            'confidence_score': confidence_score,
            'sentiment_polarity': title_sentiment.polarity,
            'sentiment_subjectivity': title_sentiment.subjectivity
        }

    def get_trump_announcements(self, start_date=datetime(2025, 1, 1)):
        """Get Trump-related announcements from political subreddits"""
        try:
            # List of relevant subreddits
            subreddits = [
                'politics',
                'news',
                'worldnews',
                'conservative',
                'democrats',
                'Republican',
                'Trump',
                'The_Donald',
                'AskTrumpSupporters',
                'CryptoCurrency',
                'Bitcoin',
                'CryptoMarkets'
            ]
            
            print(f"\nSearching for Trump announcements from {start_date.date()} to present...")
            
            announcements = []
            for subreddit_name in subreddits:
                print(f"\nSearching r/{subreddit_name} for Trump announcements...")
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Search for Trump-related posts with different queries
                    queries = [
                        'trump announcement OR trump statement OR trump tweet',
                        'trump policy OR trump decision OR trump action',
                        'trump trade OR trump tariff OR trump economy',
                        'trump crypto OR trump bitcoin OR trump cryptocurrency',
                        'trump digital currency OR trump blockchain',
                        'trump crypto regulation OR trump crypto policy'
                    ]
                    
                    for query in queries:
                        print(f"Searching with query: {query}")
                        for post in subreddit.search(
                            query=query,
                            time_filter='year',
                            limit=1000
                        ):
                            post_date = datetime.fromtimestamp(post.created_utc)
                            if post_date >= start_date:
                                # Categorize the announcement
                                categorization = self.categorize_announcement(post.title, post.selftext)
                                
                                # Only include if it's a direct statement or has high confidence
                                if categorization['is_direct'] or categorization['confidence_score'] >= 0.6:
                                    announcements.append({
                                        'title': post.title,
                                        'text': post.selftext,
                                        'created_at': post_date,
                                        'url': post.url,
                                        'subreddit': subreddit_name,
                                        'score': post.score,
                                        'num_comments': post.num_comments,
                                        'query': query,
                                        'is_direct': categorization['is_direct'],
                                        'is_crypto': categorization['is_crypto'],
                                        'content_type': categorization['content_type'],
                                        'confidence_score': categorization['confidence_score'],
                                        'sentiment_polarity': categorization['sentiment_polarity'],
                                        'sentiment_subjectivity': categorization['sentiment_subjectivity']
                                    })
                except Exception as e:
                    print(f"Error searching r/{subreddit_name}: {str(e)}")
                    continue
            
            df = pd.DataFrame(announcements)
            if not df.empty:
                print(f"\nFound {len(df)} Trump-related announcements since {start_date.date()}")
                
                # Sort by confidence score and creation date
                df = df.sort_values(['confidence_score', 'created_at'], ascending=[False, False])
                
                # Print sample announcements with categorization
                print("\nSample Announcements:")
                for i in range(min(5, len(df))):
                    print(f"\n{df.iloc[i]['created_at']}: {df.iloc[i]['title']}")
                    print(f"Type: {'Direct' if df.iloc[i]['is_direct'] else 'Indirect'} {df.iloc[i]['content_type']} announcement")
                    print(f"Crypto-related: {'Yes' if df.iloc[i]['is_crypto'] else 'No'}")
                    print(f"Confidence Score: {df.iloc[i]['confidence_score']:.2f}")
                    print(f"Sentiment: {df.iloc[i]['sentiment_polarity']:.2f} (polarity), {df.iloc[i]['sentiment_subjectivity']:.2f} (subjectivity)")
                    print(f"Subreddit: r/{df.iloc[i]['subreddit']}")
                    print(f"Score: {df.iloc[i]['score']}, Comments: {df.iloc[i]['num_comments']}")
                
                # Save to CSV with detailed filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = os.path.join(DATA_DIR, f'trump_announcements_{start_date.date()}_to_{datetime.now().date()}_{timestamp}.csv')
                df.to_csv(file_path, index=False)
                print(f"\nData saved to: {file_path}")
                
                # Print summary statistics
                print("\nSummary Statistics:")
                print(f"Total announcements: {len(df)}")
                print(f"Direct announcements: {df['is_direct'].sum()}")
                print(f"Crypto-related announcements: {df['is_crypto'].sum()}")
                print(f"High confidence announcements (score >= 0.6): {len(df[df['confidence_score'] >= 0.6])}")
                print("\nAnnouncements by type:")
                print(df['content_type'].value_counts())
                print("\nAnnouncements by subreddit:")
                print(df['subreddit'].value_counts())
                print("\nAverage confidence by content type:")
                print(df.groupby('content_type')['confidence_score'].mean())
                
            return df
                
        except Exception as e:
            print(f"Error collecting Trump announcements: {str(e)}")
            return pd.DataFrame()

    def analyze_price_impact(self, announcements_df, price_df, hours_before=6, hours_after=6):
        """Analyze Bitcoin price movements around Trump announcements"""
        if announcements_df.empty or price_df.empty:
            print("No data available for analysis")
            return pd.DataFrame()
            
        try:
            results = []
            price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
            
            for _, announcement in announcements_df.iterrows():
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
                # Save results
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = os.path.join(RESULTS_DIR, f'trump_impact_analysis_{timestamp}.csv')
                results_df.to_csv(file_path, index=False)
                print(f"\nAnalysis results saved to: {file_path}")
                
                # Print summary
                print("\nTrump Announcement Impact Analysis:")
                print(f"Average price change: {results_df['price_change'].mean():.2f}%")
                print(f"Maximum price change: {results_df['max_change'].max():.2f}%")
                print(f"Minimum price change: {results_df['min_change'].min():.2f}%")
                
                # Print most impactful announcements
                print("\nMost Impactful Announcements:")
                top_impact = results_df.nlargest(3, 'price_change')
                for _, row in top_impact.iterrows():
                    print(f"\n{row['announcement_time']}: {row['title']}")
                    print(f"Price Change: {row['price_change']:.2f}%")
                    print(f"Subreddit: r/{row['subreddit']}")
                
            return results_df
            
        except Exception as e:
            print(f"Error analyzing price impact: {str(e)}")
            return pd.DataFrame() 