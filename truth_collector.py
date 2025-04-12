import pandas as pd
from datetime import datetime, timedelta
import time
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from config import *
import random
import signal
import platform
import requests
from fake_useragent import UserAgent

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

class TruthCollector:
    def __init__(self, proxy_list=None):
        print("Starting TruthCollector initialization...")
        
        # Initialize proxy list with the provided proxies
        self.proxy_list = proxy_list or [
            "http://156.242.38.14:3128",
            "http://156.228.105.239:3128"
        ]
        self.current_proxy_index = 0
        
        # Set up Chrome options
        print("Setting up Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Use random user agent
        ua = UserAgent()
        chrome_options.add_argument(f'--user-agent={ua.random}')
        
        # Initialize the WebDriver
        print("Initializing Chrome WebDriver...")
        try:
            # Check system architecture
            system = platform.system()
            machine = platform.machine()
            print(f"System: {system}, Architecture: {machine}")
            
            if system == "Darwin" and machine == "arm64":
                print("Detected Mac ARM64 architecture")
                # Use the Homebrew-installed ChromeDriver
                chrome_driver_path = "/opt/homebrew/bin/chromedriver"
                if not os.path.exists(chrome_driver_path):
                    raise FileNotFoundError(f"ChromeDriver not found at {chrome_driver_path}. Please run 'brew install chromedriver'")
                
                service = Service(executable_path=chrome_driver_path)
                chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            else:
                raise NotImplementedError("This script currently only supports Mac ARM64")
            
            # Set up proxy if available
            if self.proxy_list:
                proxy = self._get_next_proxy()
                print(f"Using proxy: {proxy}")
                chrome_options.add_argument(f'--proxy-server={proxy}')
            
            print("Creating Chrome WebDriver instance...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Test the connection
            print("Testing WebDriver connection...")
            self.driver.get("about:blank")
            print("WebDriver initialized successfully!")
            
        except WebDriverException as e:
            print(f"WebDriver error: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error during initialization: {str(e)}")
            raise
        
        self.base_url = "https://truthsocial.com"
        self.rate_limit_delay = random.uniform(5, 10)  # Random delay between 5-10 seconds
        self.last_request_time = 0
        print("TruthCollector initialization completed successfully")

    def _get_next_proxy(self):
        """Get the next proxy from the list and rotate"""
        if not self.proxy_list:
            return None
        
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    def _rotate_proxy(self):
        """Rotate to a new proxy"""
        if not self.proxy_list:
            return False
        
        try:
            old_proxy = self._get_next_proxy()
            new_proxy = self._get_next_proxy()
            print(f"Rotating proxy from {old_proxy} to {new_proxy}")
            
            # Update Chrome options with new proxy
            self.driver.quit()
            chrome_options = self.driver.options
            chrome_options.add_argument(f'--proxy-server={new_proxy}')
            
            # Reinitialize the driver
            self.driver = webdriver.Chrome(
                service=Service(executable_path="/opt/homebrew/bin/chromedriver"),
                options=chrome_options
            )
            return True
        except Exception as e:
            print(f"Error rotating proxy: {str(e)}")
            return False

    def _respect_rate_limit(self):
        """Ensure we don't make requests too quickly"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

    def _scroll_page(self):
        """Scroll the page to simulate human behavior"""
        try:
            # Scroll down slowly
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, {i * 300});")
                time.sleep(random.uniform(0.5, 1.5))
            # Scroll back up
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            print(f"Error during scrolling: {str(e)}")

    def _get_page(self, url):
        """Navigate to a page with rate limiting and error handling"""
        try:
            self._respect_rate_limit()
            print(f"Navigating to {url}")
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            
            try:
                self.driver.get(url)
            except TimeoutException:
                print("Page load timed out after 30 seconds")
                return None
            
            print("Page loaded, waiting for body element...")
            
            # Wait for the page to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("Body element found")
            except TimeoutException:
                print("Timeout waiting for body element")
                return None
            
            # Check if we're on a login page
            current_url = self.driver.current_url.lower()
            print(f"Current URL: {current_url}")
            
            if "login" in current_url:
                print("Warning: Redirected to login page. Truth Social may be blocking automated access.")
                return None
            
            # Simulate human-like behavior
            self._scroll_page()
            
            return self.driver.page_source
            
        except Exception as e:
            print(f"Error navigating to {url}: {str(e)}")
            return None

    def get_trump_posts(self, start_date=None, max_posts=100):
        """Get Trump's posts from Truth Social"""
        if start_date is None:
            start_date = datetime(2025, 1, 1)

        posts = []
        page = 1
        
        try:
            while len(posts) < max_posts:
                url = f"{self.base_url}/@realDonaldTrump?page={page}"
                print(f"\nFetching page {page}...")
                
                html = self._get_page(url)
                if not html:
                    print("Failed to fetch page. Stopping collection.")
                    break

                # Wait for posts to load
                print("Waiting for posts to load...")
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "status"))
                    )
                    print("Posts found on page")
                except TimeoutException:
                    print("Timeout waiting for posts to load")
                    break

                post_elements = self.driver.find_elements(By.CLASS_NAME, "status")
                print(f"Found {len(post_elements)} posts on page {page}")
                
                for post in post_elements:
                    try:
                        # Extract post content
                        content = post.find_element(By.CLASS_NAME, "content")
                        if not content:
                            print("No content found in post")
                            continue

                        # Extract timestamp
                        time_element = post.find_element(By.TAG_NAME, "time")
                        if not time_element:
                            print("No timestamp found in post")
                            continue
                        
                        post_time = datetime.fromisoformat(time_element.get_attribute("datetime"))
                        if post_time < start_date:
                            print(f"Reached posts older than {start_date}. Stopping collection.")
                            return pd.DataFrame(posts)

                        # Extract text
                        text = content.text.strip()
                        
                        # Extract engagement metrics
                        stats = post.find_elements(By.CLASS_NAME, "status__action-counter")
                        replies = int(stats[0].text.strip() or 0)
                        reblogs = int(stats[1].text.strip() or 0)
                        favorites = int(stats[2].text.strip() or 0)

                        posts.append({
                            'created_at': post_time,
                            'text': text,
                            'replies': replies,
                            'reblogs': reblogs,
                            'favorites': favorites,
                            'url': f"{self.base_url}{post.find_element(By.CLASS_NAME, 'status__relative-time').get_attribute('href')}"
                        })

                        print(f"Collected post from {post_time}")
                        
                        if len(posts) >= max_posts:
                            print(f"Reached maximum number of posts ({max_posts}).")
                            break

                    except Exception as e:
                        print(f"Error processing post: {str(e)}")
                        continue

                page += 1
                # Add random delay between pages
                delay = random.uniform(2, 5)
                print(f"Waiting {delay:.1f} seconds before next page...")
                time.sleep(delay)

        finally:
            # Always close the browser
            print("Closing browser...")
            self.driver.quit()

        return pd.DataFrame(posts)

    def analyze_post_impact(self, posts_df, price_df, hours_before=6, hours_after=6):
        """Analyze Bitcoin price movements around Trump's Truth Social posts"""
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
                file_path = os.path.join(RESULTS_DIR, f'truth_impact_analysis_{timestamp}.csv')
                results_df.to_csv(file_path, index=False)
                print(f"\nAnalysis results saved to: {file_path}")

                # Print summary
                print("\nTruth Social Post Impact Analysis:")
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

    def _fetch_free_proxies(self):
        """Fetch and test free proxies from various sources"""
        print("Fetching free proxies...")
        proxies = []
        
        try:
            # Use the specific ProxyScrape API endpoint from your dashboard
            api_url = "https://api.proxyscrape.com/v2/services/premium/proxy-list/5fab5ead-54cc-4ca9-bff8-68ee7a1e2a2c"
            response = requests.get(api_url)
            if response.status_code == 200:
                proxy_list = response.text.strip().split('\r\n')
                proxies.extend([f"http://{proxy}" for proxy in proxy_list])
                print(f"Added {len(proxy_list)} proxies from ProxyScrape")
        except Exception as e:
            print(f"Error fetching from ProxyScrape: {str(e)}")
            print("Please check if your API endpoint is correct and your IP is authenticated")
        
        # Test and filter proxies
        working_proxies = []
        for proxy in proxies:
            try:
                response = requests.get(
                    'https://api.ipify.org?format=json',
                    proxies={'http': proxy, 'https': proxy},
                    timeout=5
                )
                if response.status_code == 200:
                    working_proxies.append(proxy)
                    print(f"Working proxy found: {proxy}")
            except:
                continue
        
        print(f"Found {len(working_proxies)} working proxies")
        return working_proxies 