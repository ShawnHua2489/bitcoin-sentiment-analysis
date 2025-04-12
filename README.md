# Bitcoin Social Media Sentiment Analyzer

This project collects and analyzes social media sentiment about Bitcoin from multiple sources and correlates it with Bitcoin price movements. It also includes analysis of the relationship between Trump-related search interest and Bitcoin metrics.

## Features

- Collects Bitcoin-related posts from Reddit
- Gathers news articles about Bitcoin
- Fetches Bitcoin price data from Binance
- Tracks Google Trends data for Bitcoin and Trump-related searches
- Performs sentiment analysis on social media content
- Analyzes correlation between various indicators and price movements
- Generates visualizations of the analysis

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root with your API credentials:
```
# Reddit API credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USERNAME=your_reddit_username

# News API credentials
NEWSAPI_KEY=your_newsapi_key
```

3. To get Reddit API credentials:
   - Go to https://www.reddit.com/prefs/apps
   - Create a new application
   - Note the client ID and client secret

4. To get NewsAPI credentials:
   - Go to https://newsapi.org/
   - Sign up for a free API key

## Usage

Run the main script:
```bash
python main.py
```

The script will:
1. Collect posts from Bitcoin-related subreddits
2. Gather news articles about Bitcoin
3. Fetch Bitcoin price data
4. Track Google Trends data for Bitcoin and Trump-related searches
5. Perform sentiment analysis
6. Generate correlation analysis
7. Save results in the `data` and `results` directories

## Analysis Features

- Sentiment analysis of Reddit posts and news articles
- Correlation analysis between:
  - Bitcoin price and social media sentiment
  - Bitcoin price and search interest
  - Trump-related search interest and Bitcoin metrics
- Time series visualization of all indicators
- Correlation heatmap showing relationships between different metrics

## Output

- Raw data is saved in the `data` directory as CSV files
- Analysis results and visualizations are saved in the `results` directory
- Correlation heatmap showing relationships between different indicators
- Time series plots showing how indicators move together

## Notes

- The script collects data from the last 24 hours by default
- Sentiment analysis is performed using TextBlob
- Price data is fetched from Binance exchange
- Google Trends data is normalized to 0-100 scale
- Trump-related analysis includes search terms: 'donald trump', 'trump', 'president trump' 