import os
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

# Print environment variables for debugging
print("\nLoading environment variables...")
print(f".env file path: {env_path}")
print(f".env file exists: {os.path.exists(env_path)}")

# Twitter API credentials
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Reddit API credentials
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
REDDIT_USER_AGENT = 'BitcoinSentimentAnalyzer/1.0'

# NewsAPI credentials
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')
if not NEWSAPI_KEY:
    print("Warning: NEWSAPI_KEY not found in environment variables")
    print("Available environment variables:", os.environ.keys())
else:
    print(f"NewsAPI key loaded: {NEWSAPI_KEY[:5]}...")

# Search parameters
BITCOIN_KEYWORDS = [
    'bitcoin', 'btc', '#bitcoin', '#btc',
    'crypto', 'cryptocurrency', 'digital gold'
]

# Data collection settings
MAX_TWEETS = 1000
MAX_REDDIT_POSTS = 100
MAX_NEWS_ARTICLES = 100
TIME_WINDOW_HOURS = 24

# File paths
DATA_DIR = 'data'
RESULTS_DIR = 'results' 