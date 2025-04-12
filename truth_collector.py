import pandas as pd
from datetime import datetime, timedelta
import time
import os
import random
import requests
from bs4 import BeautifulSoup
from config import *

class TruthCollector:
    def __init__(self):
        print("Starting TruthCollector initialization...")
        self.base_url = "https://trumpstruth.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.rate_limit_delay = random.uniform(0.5, 1)  # Reduced delay since we're using requests
        self.last_request_time = 0
        print("TruthCollector initialization completed successfully")

    def _respect_rate_limit(self):
        """Ensure we don't make requests too quickly"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

    def _get_page(self, url):
        """Get page content with rate limiting and error handling"""
        try:
            self._respect_rate_limit()
            print(f"Fetching {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.text
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {str(e)}")
            return None

    def get_trump_posts(self, start_date=None, max_posts=100):
        """Get Trump's posts from Trump's Truth archive"""
        if start_date is None:
            start_date = datetime(2025, 1, 1)

        posts = []
        page = 1
        retry_count = 0
        max_retries = 2
        
        try:
            while len(posts) < max_posts and retry_count < max_retries:
                url = f"{self.base_url}/?page={page}"
                print(f"\nFetching page {page}...")
                
                html = self._get_page(url)
                if not html:
                    print("Failed to fetch page. Retrying...")
                    retry_count += 1
                    if retry_count >= max_retries:
                        print("Max retries reached. Stopping collection.")
                        break
                    time.sleep(2)  # Short delay before retry
                    continue
                
                retry_count = 0  # Reset retry count on successful page load
                
                # Parse the HTML
                soup = BeautifulSoup(html, 'html.parser')
                post_elements = soup.find_all(class_="post")
                
                if not post_elements:
                    print("No posts found on page")
                    break
                
                print(f"Found {len(post_elements)} posts on page {page}")
                
                for post in post_elements:
                    try:
                        # Extract post content
                        content = post.find(class_="content")
                        if not content:
                            print("No content found in post")
                            continue

                        # Extract timestamp
                        time_element = post.find(class_="timestamp")
                        if not time_element:
                            print("No timestamp found in post")
                            continue
                        
                        post_time = datetime.strptime(time_element.text.strip(), "%B %d, %Y, %I:%M %p")
                        if post_time < start_date:
                            print(f"Reached posts older than {start_date}. Stopping collection.")
                            return pd.DataFrame(posts)

                        # Extract text
                        text = content.text.strip()
                        
                        # Extract engagement metrics if available
                        stats = post.find(class_="stats")
                        replies = 0
                        reblogs = 0
                        favorites = 0
                        if stats:
                            stats_text = stats.text
                            replies = int(stats_text.split("Replies: ")[1].split()[0]) if "Replies: " in stats_text else 0
                            reblogs = int(stats_text.split("Reblogs: ")[1].split()[0]) if "Reblogs: " in stats_text else 0
                            favorites = int(stats_text.split("Favorites: ")[1].split()[0]) if "Favorites: " in stats_text else 0

                        posts.append({
                            'created_at': post_time,
                            'text': text,
                            'replies': replies,
                            'reblogs': reblogs,
                            'favorites': favorites,
                            'url': post.find(class_="permalink")['href'] if post.find(class_="permalink") else None
                        })

                        print(f"Collected post from {post_time}")
                        
                        if len(posts) >= max_posts:
                            print(f"Reached maximum number of posts ({max_posts}).")
                            break

                    except Exception as e:
                        print(f"Error processing post: {str(e)}")
                        continue

                page += 1
                # Add small delay between pages
                time.sleep(random.uniform(0.5, 1))

        except Exception as e:
            print(f"Error during collection: {str(e)}")

        return pd.DataFrame(posts)

    def analyze_post_impact(self, posts_df, price_df, hours_before=6, hours_after=6):
        """Analyze Bitcoin price movements around Trump's posts"""
        if posts_df.empty or price_df.empty:
            print("Not enough data for analysis")
            return None

        try:
            results = []
            price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
            posts_df['created_at'] = pd.to_datetime(posts_df['created_at'])

            for _, post in posts_df.iterrows():
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
                # Save results
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = os.path.join(RESULTS_DIR, f'trump_impact_analysis_{timestamp}.csv')
                results_df.to_csv(file_path, index=False)
                print(f"\nAnalysis results saved to: {file_path}")

                # Print summary
                print("\nTrump Post Impact Analysis:")
                print(f"Average price change: {results_df['price_change'].mean():.2f}%")
                print(f"Maximum price change: {results_df['max_change'].max():.2f}%")
                print(f"Minimum price change: {results_df['min_change'].min():.2f}%")

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