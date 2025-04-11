import praw
import pandas as pd
from datetime import datetime, timedelta
from textblob import TextBlob
from config import *

class RedditCollector:
    def __init__(self):
        try:
            self.reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=f"BitcoinSentimentAnalyzer/1.0 by /u/your_reddit_username"  # Replace with your Reddit username
            )
            # Test the connection
            self.reddit.user.me()
            print("Successfully connected to Reddit API")
        except Exception as e:
            print(f"Error connecting to Reddit API: {str(e)}")
            print("Please check your credentials in the .env file")
            raise
        
    def get_posts(self, subreddit_name, max_posts=MAX_REDDIT_POSTS):
        posts = []
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            print(f"Accessing subreddit: r/{subreddit_name}")
            
            # Get posts from the last 24 hours
            since_date = datetime.now() - timedelta(hours=TIME_WINDOW_HOURS)
            
            for post in subreddit.new(limit=max_posts):
                if datetime.fromtimestamp(post.created_utc) < since_date:
                    continue
                    
                # Perform sentiment analysis on title and selftext
                title_sentiment = TextBlob(post.title).sentiment
                text_sentiment = TextBlob(post.selftext).sentiment if post.selftext else title_sentiment
                
                posts.append({
                    'id': post.id,
                    'created_at': datetime.fromtimestamp(post.created_utc),
                    'title': post.title,
                    'text': post.selftext,
                    'author': post.author.name if post.author else '[deleted]',
                    'score': post.score,
                    'num_comments': post.num_comments,
                    'url': post.url,
                    'title_sentiment_polarity': title_sentiment.polarity,
                    'title_sentiment_subjectivity': title_sentiment.subjectivity,
                    'text_sentiment_polarity': text_sentiment.polarity,
                    'text_sentiment_subjectivity': text_sentiment.subjectivity
                })
                
        except Exception as e:
            print(f"Error collecting posts from r/{subreddit_name}: {str(e)}")
            print("Please check if the subreddit exists and is accessible")
            
        return pd.DataFrame(posts)
    
    def collect_bitcoin_posts(self):
        subreddits = ['Bitcoin', 'CryptoCurrency', 'BitcoinMarkets']
        all_posts = pd.DataFrame()
        
        for subreddit in subreddits:
            print(f"\nCollecting posts from r/{subreddit}")
            posts = self.get_posts(subreddit)
            if not posts.empty:
                all_posts = pd.concat([all_posts, posts], ignore_index=True)
                print(f"Successfully collected {len(posts)} posts from r/{subreddit}")
            else:
                print(f"No posts collected from r/{subreddit}")
        
        if not all_posts.empty:
            # Remove duplicates
            all_posts = all_posts.drop_duplicates(subset=['id'])
            
            # Save to CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            all_posts.to_csv(f'{DATA_DIR}/reddit_data_{timestamp}.csv', index=False)
            print(f"\nTotal posts collected: {len(all_posts)}")
            print(f"Data saved to: {DATA_DIR}/reddit_data_{timestamp}.csv")
        else:
            print("\nNo posts were collected from any subreddit")
        
        return all_posts 