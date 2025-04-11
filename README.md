# Bitcoin Social Media Sentiment Analyzer

This project collects and analyzes social media sentiment about Bitcoin from Twitter and Reddit, and correlates it with Bitcoin price movements.

## Features

- Collects Bitcoin-related tweets using Twitter API
- Gathers posts from relevant Bitcoin subreddits
- Fetches Bitcoin price data from Binance
- Performs sentiment analysis on social media content
- Correlates sentiment with price movements
- Generates visualizations of the analysis

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root with your API credentials:
```
# Twitter API credentials
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

# Reddit API credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

3. To get Twitter API credentials:
   - Go to https://developer.twitter.com/
   - Create a new project and app
   - Generate API keys and access tokens

4. To get Reddit API credentials:
   - Go to https://www.reddit.com/prefs/apps
   - Create a new application
   - Note the client ID and client secret

## Usage

Run the main script:
```bash
python main.py
```

The script will:
1. Collect tweets about Bitcoin
2. Gather posts from Bitcoin-related subreddits
3. Fetch Bitcoin price data
4. Perform sentiment analysis
5. Generate correlation analysis
6. Save results in the `data` and `results` directories

## Output

- Raw data is saved in the `data` directory as CSV files
- Analysis results and visualizations are saved in the `results` directory
- A correlation heatmap showing the relationship between sentiment and price movements

## Notes

- The script collects data from the last 24 hours by default
- Sentiment analysis is performed using TextBlob
- Price data is fetched from Binance exchange
- The analysis focuses on correlation between social media sentiment and price movements 