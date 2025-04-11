import tweepy
import pandas as pd
from datetime import datetime, timedelta
from textblob import TextBlob
from config import *

class TwitterCollector:
    def __init__(self):
        auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        
    def get_tweets(self, query, max_tweets=MAX_TWEETS):
        tweets = []
        try:
            # Get tweets from the last 24 hours
            since_date = datetime.now() - timedelta(hours=TIME_WINDOW_HOURS)
            
            for tweet in tweepy.Cursor(self.api.search_tweets,
                                     q=query,
                                     lang="en",
                                     tweet_mode="extended",
                                     since=since_date.strftime('%Y-%m-%d')).items(max_tweets):
                
                # Perform sentiment analysis
                sentiment = TextBlob(tweet.full_text).sentiment
                
                tweets.append({
                    'id': tweet.id,
                    'created_at': tweet.created_at,
                    'text': tweet.full_text,
                    'user': tweet.user.screen_name,
                    'retweets': tweet.retweet_count,
                    'favorites': tweet.favorite_count,
                    'sentiment_polarity': sentiment.polarity,
                    'sentiment_subjectivity': sentiment.subjectivity
                })
                
        except Exception as e:
            print(f"Error collecting tweets: {str(e)}")
            
        return pd.DataFrame(tweets)
    
    def collect_bitcoin_tweets(self):
        all_tweets = pd.DataFrame()
        for keyword in BITCOIN_KEYWORDS:
            print(f"Collecting tweets for keyword: {keyword}")
            tweets = self.get_tweets(keyword)
            all_tweets = pd.concat([all_tweets, tweets], ignore_index=True)
        
        # Remove duplicates
        all_tweets = all_tweets.drop_duplicates(subset=['id'])
        
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        all_tweets.to_csv(f'{DATA_DIR}/twitter_data_{timestamp}.csv', index=False)
        
        return all_tweets 