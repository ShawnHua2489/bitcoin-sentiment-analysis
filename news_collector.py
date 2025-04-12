from newsapi import NewsApiClient
import pandas as pd
from datetime import datetime, timedelta
from textblob import TextBlob
import os
import glob
from dotenv import load_dotenv
from config import *

class NewsCollector:
    def __init__(self):
        self.request_count = 0
        try:
            # Load environment variables directly
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            load_dotenv(env_path)
            
            # Print environment variables for debugging
            print("\nEnvironment variables check:")
            print(f"NEWSAPI_KEY exists: {'NEWSAPI_KEY' in os.environ}")
            print(f"NEWSAPI_KEY value: {os.environ.get('NEWSAPI_KEY', 'Not found')[:5]}...")
            
            # Get API key directly from environment
            api_key = os.environ.get('NEWSAPI_KEY')
            if not api_key:
                raise ValueError("NewsAPI key is missing or invalid")
                
            self.client = NewsApiClient(api_key=api_key)
            
            # Test the connection with a simple request
            self.request_count += 1
            print(f"\nMaking test request #{self.request_count}...")
            test_response = self.client.get_top_headlines(q='bitcoin', language='en', page_size=1)
            if 'status' in test_response and test_response['status'] == 'ok':
                print("Successfully connected to NewsAPI")
            else:
                print(f"Test request failed: {test_response}")
                raise ValueError("Failed to connect to NewsAPI")
                
        except Exception as e:
            print(f"Error connecting to NewsAPI: {str(e)}")
            raise

    def get_existing_articles(self):
        """Get the most recent news data file if it exists"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(DATA_DIR, exist_ok=True)
            
            # Find all news data files
            files = glob.glob(os.path.join(DATA_DIR, 'news_data_*.csv'))
            if files:
                # Get the most recent file
                latest_file = max(files, key=os.path.getctime)
                print(f"\nFound existing news data: {latest_file}")
                
                # Check if file is empty or too small (less than 100 bytes)
                if os.path.getsize(latest_file) < 100:
                    print("Existing file is empty or corrupted, will collect new data")
                    return pd.DataFrame()
                    
                df = pd.read_csv(latest_file)
                if df.empty:
                    print("No articles found in existing file")
                    return pd.DataFrame()
                    
                # Check if data is recent enough (within TIME_WINDOW_HOURS)
                df['published_at'] = pd.to_datetime(df['published_at'])
                latest_article_time = df['published_at'].max()
                time_diff = datetime.now() - latest_article_time
                
                if time_diff.total_seconds() / 3600 <= TIME_WINDOW_HOURS:
                    print(f"Loaded {len(df)} existing articles from the last {TIME_WINDOW_HOURS} hours")
                    return df
                else:
                    print(f"Existing data is too old ({time_diff.total_seconds()/3600:.1f} hours), will collect new data")
                    return pd.DataFrame()
                    
            return pd.DataFrame()
        except Exception as e:
            print(f"Error loading existing articles: {str(e)}")
            return pd.DataFrame()

    def get_news(self, query='bitcoin OR btc OR cryptocurrency', max_articles=100):
        articles = []
        try:
            # Get news from the last 24 hours
            from_date = (datetime.now() - timedelta(hours=TIME_WINDOW_HOURS)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            print(f"\nNewsAPI Request Details:")
            print(f"Query: {query}")
            print(f"From date: {from_date}")
            print(f"To date: {to_date}")
            print(f"Max articles per request: {min(100, max_articles)}")
            
            # Get news articles
            self.request_count += 1
            print(f"\nMaking article request #{self.request_count}...")
            response = self.client.get_everything(
                q=query,
                from_param=from_date,
                to=to_date,
                language='en',
                sort_by='relevancy',
                page_size=min(100, max_articles)
            )
            
            print(f"\nNewsAPI Response:")
            print(f"Status: {response.get('status', 'No status')}")
            total_results = response.get('totalResults', 0)
            print(f"Total articles available: {total_results}")
            print(f"Articles returned in this request: {len(response.get('articles', []))}")
            print(f"Note: NewsAPI free tier limits to 100 articles per request")
            
            if response.get('status') == 'error':
                print(f"API Error: {response.get('message', 'Unknown error')}")
                return pd.DataFrame()
            
            if not response or 'articles' not in response:
                print(f"Unexpected response format: {response}")
                return pd.DataFrame()
            
            if response['articles']:
                print(f"\nProcessing {len(response['articles'])} articles...")
                for article in response['articles']:
                    try:
                        # Perform sentiment analysis on title and description
                        title_sentiment = TextBlob(article['title']).sentiment
                        desc_sentiment = TextBlob(article['description']).sentiment if article['description'] else title_sentiment
                        
                        articles.append({
                            'source': article['source']['name'],
                            'author': article['author'],
                            'title': article['title'],
                            'description': article['description'],
                            'url': article['url'],
                            'published_at': article['publishedAt'],
                            'title_sentiment_polarity': title_sentiment.polarity,
                            'title_sentiment_subjectivity': title_sentiment.subjectivity,
                            'description_sentiment_polarity': desc_sentiment.polarity,
                            'description_sentiment_subjectivity': desc_sentiment.subjectivity
                        })
                    except Exception as e:
                        print(f"Error processing article: {str(e)}")
                        continue
            else:
                print("No articles found in response")
                
        except Exception as e:
            print(f"Error collecting news articles: {str(e)}")
            print(f"API Key: {NEWSAPI_KEY[:5]}...")  # Print first 5 chars of API key for debugging
            
        return pd.DataFrame(articles)

    def collect_bitcoin_news(self):
        # First try to get existing articles
        articles = self.get_existing_articles()
        
        if articles.empty:
            print("\nNo existing news data found or data is too old. Attempting to collect new articles...")
            articles = self.get_news()
        
        if not articles.empty:
            # Save to CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(DATA_DIR, f'news_data_{timestamp}.csv')
            articles.to_csv(file_path, index=False)
            print(f"\nTotal articles collected: {len(articles)}")
            print(f"Data saved to: {file_path}")
            
            # Print the first few articles as a sample
            print("\nSample of collected articles:")
            print(articles[['source', 'title', 'title_sentiment_polarity']].head())
        else:
            print("\nNo articles were collected")
            
        print(f"\nTotal NewsAPI requests made: {self.request_count}")
        
        return articles 