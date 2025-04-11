import tweepy
import pandas as pd
from datetime import datetime, timedelta
from textblob import TextBlob
import os
import glob
from dotenv import load_dotenv
from config import *

class TwitterCollector:
    def __init__(self):
        try:
            # Load environment variables
            load_dotenv()
            
            # Get bearer token from environment
            bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            if not bearer_token:
                raise ValueError("TWITTER_BEARER_TOKEN not found in environment variables")
            
            print(f"Using bearer token: {bearer_token[:10]}...")  # Print first 10 chars for debugging
            
            # Initialize the client with Bearer Token
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                wait_on_rate_limit=True
            )
            print("Successfully connected to Twitter API")
        except Exception as e:
            print(f"Error connecting to Twitter API: {str(e)}")
            raise
    
    def get_existing_tweets(self):
        """Get the most recent tweet data file if it exists"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(DATA_DIR, exist_ok=True)
            
            # Find all twitter data files
            files = glob.glob(os.path.join(DATA_DIR, 'twitter_data_*.csv'))
            if files:
                # Get the most recent file
                latest_file = max(files, key=os.path.getctime)
                print(f"\nFound existing tweet data: {latest_file}")
                
                # Check if file is empty or too small (less than 100 bytes)
                if os.path.getsize(latest_file) < 100:
                    print("Existing file is empty or corrupted, will collect new data")
                    return pd.DataFrame()
                    
                df = pd.read_csv(latest_file)
                if df.empty:
                    print("No tweets found in existing file")
                    return pd.DataFrame()
                    
                print(f"Loaded {len(df)} existing tweets")
                return df
            return pd.DataFrame()
        except Exception as e:
            print(f"Error loading existing tweets: {str(e)}")
            return pd.DataFrame()
        
    def get_tweets(self, query, max_tweets=MAX_TWEETS):
        tweets = []
        try:
            # Get tweets from the last 24 hours
            since_date = datetime.now() - timedelta(hours=TIME_WINDOW_HOURS)
            
            print(f"Searching for tweets with query: {query}")
            
            # Search recent tweets
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(100, max_tweets),  # Twitter API v2 has a max of 100 per request
                tweet_fields=['created_at', 'public_metrics', 'text'],
                user_fields=['username'],
                expansions=['author_id']
            )
            
            if response.data:
                print(f"Found {len(response.data)} tweets")
                for tweet in response.data:
                    # Get user information
                    user = next((user for user in response.includes['users'] if user.id == tweet.author_id), None)
                    
                    # Perform sentiment analysis
                    sentiment = TextBlob(tweet.text).sentiment
                    
                    tweets.append({
                        'id': tweet.id,
                        'created_at': tweet.created_at,
                        'text': tweet.text,
                        'user': user.username if user else 'unknown',
                        'retweets': tweet.public_metrics['retweet_count'],
                        'favorites': tweet.public_metrics['like_count'],
                        'sentiment_polarity': sentiment.polarity,
                        'sentiment_subjectivity': sentiment.subjectivity
                    })
            else:
                print("No tweets found in response")
                
        except tweepy.errors.TooManyRequests:
            print("Rate limit exceeded. Using existing data if available.")
            return self.get_existing_tweets()
        except Exception as e:
            print(f"Error collecting tweets for query '{query}': {str(e)}")
            
        return pd.DataFrame(tweets)
    
    def collect_bitcoin_tweets(self):
        # First try to get existing tweets
        all_tweets = self.get_existing_tweets()
        
        if all_tweets.empty:
            print("\nNo existing tweet data found. Attempting to collect new tweets...")
            for keyword in BITCOIN_KEYWORDS:
                print(f"\nCollecting tweets for keyword: {keyword}")
                tweets = self.get_tweets(keyword)
                if not tweets.empty:
                    all_tweets = pd.concat([all_tweets, tweets], ignore_index=True)
                    print(f"Successfully collected {len(tweets)} tweets for '{keyword}'")
                else:
                    print(f"No tweets collected for '{keyword}'")
        
        if not all_tweets.empty:
            # Remove duplicates
            all_tweets = all_tweets.drop_duplicates(subset=['id'])
            
            # Create data directory if it doesn't exist
            os.makedirs(DATA_DIR, exist_ok=True)
            
            # Save to CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(DATA_DIR, f'twitter_data_{timestamp}.csv')
            all_tweets.to_csv(file_path, index=False)
            print(f"\nTotal tweets available: {len(all_tweets)}")
            print(f"Data saved to: {file_path}")
            
            # Print the first few tweets as a sample
            print("\nSample of available tweets:")
            print(all_tweets[['created_at', 'text', 'sentiment_polarity']].head())
        else:
            print("\nNo tweets available")
        
        return all_tweets 