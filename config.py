import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twitter API credentials
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Reddit API credentials
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = 'BitcoinSentimentAnalyzer/1.0'

# Search parameters
BITCOIN_KEYWORDS = [
    'bitcoin', 'btc', '#bitcoin', '#btc',
    'crypto', 'cryptocurrency', 'digital gold'
]

# Data collection settings
MAX_TWEETS = 1000
MAX_REDDIT_POSTS = 100
TIME_WINDOW_HOURS = 24

# File paths
DATA_DIR = 'data'
RESULTS_DIR = 'results' 