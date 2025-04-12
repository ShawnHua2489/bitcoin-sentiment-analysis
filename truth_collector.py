from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import random
import requests
from bs4 import BeautifulSoup
from config import *
import re
import logging
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

class TruthCollector:
    def __init__(self):
        print("Starting TruthCollector initialization...")
        self.base_url = "https://trumpstruth.org"
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Set up Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Initialize the WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
        
        # Set up session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        
        # Rate limiting settings
        self.min_delay = 2.0  # Minimum delay between requests
        self.max_delay = 4.0  # Maximum delay between requests
        self.last_request_time = 0
        
        # Check robots.txt
        self._check_robots_txt()
        
        print("TruthCollector initialization completed successfully")

    def _check_robots_txt(self):
        """Check robots.txt for scraping permissions"""
        try:
            rp = RobotFileParser()
            rp.set_url(f"{self.base_url}/robots.txt")
            rp.read()
            if not rp.can_fetch(self.session.headers['User-Agent'], self.base_url):
                self.logger.warning("Scraping not allowed by robots.txt")
        except Exception as e:
            self.logger.warning(f"Could not read robots.txt: {str(e)}")

    def _respect_rate_limit(self):
        """Implement exponential backoff for rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            delay = self.min_delay + random.uniform(0, self.max_delay - self.min_delay)
            time.sleep(delay)
        self.last_request_time = time.time()

    def _get_page(self, url, max_retries=3):
        """Get page content with proper error handling and retries"""
        for attempt in range(max_retries):
            try:
                self._respect_rate_limit()
                self.logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                return response.text
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error fetching {url}: {str(e)}")
                if attempt < max_retries - 1:
                    delay = (2 ** attempt) * self.min_delay  # Exponential backoff
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"Max retries reached for {url}")
                    return None

    def get_trump_posts(self, start_date=None, max_posts=100):
        """Get Trump's posts with improved error handling and data validation"""
        if start_date is None:
            start_date = datetime(2025, 1, 1)

        posts = []
        seen_urls = set()  # Track seen URLs to avoid duplicates
        page = 1
        
        try:
            while len(posts) < max_posts:
                url = f"{self.base_url}/?page={page}"
                self.logger.info(f"Processing page {page}")
                
                html = self._get_page(url)
                if not html:
                    break
                
                soup = BeautifulSoup(html, 'html.parser')
                post_elements = soup.find_all(class_="status-card")
                
                if not post_elements:
                    self.logger.info("No more posts found")
                    break
                
                for post in post_elements:
                    try:
                        # Extract and validate URL
                        source_url = post.get('href')
                        if not source_url or source_url in seen_urls:
                            continue
                        seen_urls.add(source_url)
                        
                        # Extract content
                        title = post.find(class_="status-card__title")
                        description = post.find(class_="status-card__description")
                        
                        if not title or not description:
                            self.logger.warning(f"Skipping post with missing content: {source_url}")
                            continue
                        
                        # Extract and validate date
                        post_time = self._extract_date(source_url, post)
                        if not post_time:
                            self.logger.warning(f"Could not extract date for post: {source_url}")
                            continue
                        
                        if post_time < start_date:
                            self.logger.info(f"Reached posts older than {start_date}")
                            return pd.DataFrame(posts)
                        
                        # Extract source
                        source = post.find(class_="status-card__overline")
                        source_name = source.text.strip() if source else "Unknown source"
                        
                        posts.append({
                            'created_at': post_time,
                            'text': f"{title.text.strip()}\n\n{description.text.strip()}",
                            'source': source_name,
                            'url': source_url,
                            'replies': 0,
                            'reblogs': 0,
                            'favorites': 0
                        })
                        
                        self.logger.info(f"Collected post from {post_time}")
                        
                        if len(posts) >= max_posts:
                            self.logger.info(f"Reached maximum number of posts ({max_posts})")
                            return pd.DataFrame(posts)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing post: {str(e)}")
                        continue
                
                page += 1
                
        except Exception as e:
            self.logger.error(f"Error during collection: {str(e)}")
        finally:
            self.driver.quit()  # Clean up resources
            
        return pd.DataFrame(posts)

    def _extract_date(self, url, post):
        """Extract date from URL or post content with validation"""
        try:
            # Try to extract from URL first
            date_match = re.search(r'/(\d{4})/([a-z]{3})/(\d{2})/', url)
            if date_match:
                year, month, day = date_match.groups()
                month_map = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }
                return datetime(int(year), month_map[month.lower()], int(day))
            
            # Try to find date in post content
            date_element = post.find(class_="status-card__date")
            if date_element:
                date_text = date_element.text.strip()
                date_formats = [
                    "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d",
                    "%d %B %Y", "%d %b %Y", "%Y/%m/%d"
                ]
                for date_format in date_formats:
                    try:
                        return datetime.strptime(date_text, date_format)
                    except ValueError:
                        continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting date: {str(e)}")
            return None

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
                        'source': post['source'],
                        'url': post['url'],
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
                    print(f"Source: {row['source']}")
                    print(f"URL: {row['url']}")

            return results_df

        except Exception as e:
            print(f"Error in impact analysis: {str(e)}")
            return None 