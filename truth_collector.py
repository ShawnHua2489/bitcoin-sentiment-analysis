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
import ssl

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

class TruthCollector:
    def __init__(self, proxy_list=None):
        print("Starting TruthCollector initialization...")
        
        # Initialize proxy list with free proxies
        self.proxy_list = proxy_list or self._fetch_free_proxies()
        self.current_proxy_index = 0
        self.max_proxy_retries = 3
        self.proxy_retry_count = 0
        
        # Set up Chrome options with advanced anti-detection
        print("Setting up Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=412,915')  # Mobile-like window size
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        
        # Advanced anti-detection settings
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add mobile user agent
        mobile_user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
        ]
        self.current_user_agent = random.choice(mobile_user_agents)
        chrome_options.add_argument(f'--user-agent={self.current_user_agent}')
        
        # Initialize the WebDriver
        print("Initializing Chrome WebDriver...")
        try:
            # Check system architecture
            system = platform.system()
            machine = platform.machine()
            print(f"System: {system}, Architecture: {machine}")
            
            if system == "Darwin" and machine == "arm64":
                print("Detected Mac ARM64 architecture")
                chrome_driver_path = "/opt/homebrew/bin/chromedriver"
                if not os.path.exists(chrome_driver_path):
                    raise FileNotFoundError(f"ChromeDriver not found at {chrome_driver_path}. Please run 'brew install chromedriver'")
                
                service = Service(executable_path=chrome_driver_path)
                chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            else:
                raise NotImplementedError("This script currently only supports Mac ARM64")
            
            # Set up initial proxy
            proxy = self._get_next_proxy()
            print(f"Using proxy: {proxy}")
            chrome_options.add_argument(f'--proxy-server={proxy}')
            
            print("Creating Chrome WebDriver instance...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute CDP commands to further reduce detection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": self.current_user_agent
            })
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
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
        self.rate_limit_delay = random.uniform(5, 10)
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
        """Rotate to a new proxy and reinitialize the driver"""
        if not self.proxy_list:
            return False
        
        try:
            self.proxy_retry_count += 1
            if self.proxy_retry_count >= self.max_proxy_retries:
                print("Max proxy retries reached. Refreshing proxy list...")
                self.proxy_list = self._fetch_free_proxies()
                self.proxy_retry_count = 0
                if not self.proxy_list:
                    return False
            
            old_proxy = self._get_next_proxy()
            new_proxy = self._get_next_proxy()
            print(f"Rotating proxy from {old_proxy} to {new_proxy}")
            
            # Close existing driver
            try:
                self.driver.quit()
            except:
                pass
            
            # Create new options
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=412,915')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--allow-insecure-localhost')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Use a different user agent
            self.current_user_agent = random.choice([
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
            ])
            chrome_options.add_argument(f'--user-agent={self.current_user_agent}')
            chrome_options.add_argument(f'--proxy-server={new_proxy}')
            
            # Reinitialize the driver
            self.driver = webdriver.Chrome(
                service=Service(executable_path="/opt/homebrew/bin/chromedriver"),
                options=chrome_options
            )
            
            # Reapply CDP commands
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": self.current_user_agent
            })
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
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
            # Get page height
            page_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down in random increments
            current_position = 0
            while current_position < page_height:
                scroll_amount = random.randint(100, 300)
                current_position += scroll_amount
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(0.5, 2.0))
                
                # Randomly scroll back up sometimes
                if random.random() < 0.2:
                    back_amount = random.randint(50, 150)
                    current_position = max(0, current_position - back_amount)
                    self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                    time.sleep(random.uniform(0.5, 1.5))
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(1.0, 2.0))
            
        except Exception as e:
            print(f"Error during scrolling: {str(e)}")

    def _get_page(self, url):
        """Navigate to a page with rate limiting and error handling"""
        try:
            self._respect_rate_limit()
            print(f"Navigating to {url}")
            
            # Set page load timeout
            self.driver.set_page_load_timeout(60)
            
            try:
                self.driver.get(url)
            except TimeoutException:
                print("Page load timed out after 60 seconds")
                return None
            except WebDriverException as e:
                if "ERR_CONNECTION_RESET" in str(e):
                    print("Connection reset detected. Rotating proxy...")
                    if self._rotate_proxy():
                        return self._get_page(url)
                    return None
                raise
            
            print("Page loaded, waiting for body element...")
            
            # Wait for the page to load with multiple element checks
            try:
                # First wait for body
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("Body element found")
                
                # Check for error messages
                if "unavailable in your area" in self.driver.page_source.lower():
                    print("Detected geo-blocking. Rotating proxy...")
                    if self._rotate_proxy():
                        return self._get_page(url)
                    return None
                
                # Then wait for main content
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
                print("Main content found")
                
                # Simulate human-like behavior
                self._scroll_page()
                
                # Additional wait for dynamic content
                time.sleep(random.uniform(3, 7))
                
            except TimeoutException:
                print("Timeout waiting for page elements")
                return None
            
            # Check if we're on a login page
            current_url = self.driver.current_url.lower()
            print(f"Current URL: {current_url}")
            
            if "login" in current_url:
                print("Warning: Redirected to login page. Truth Social may be blocking automated access.")
                return None
            
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
        retry_count = 0
        max_retries = 3
        
        try:
            while len(posts) < max_posts and retry_count < max_retries:
                url = f"{self.base_url}/@realDonaldTrump?page={page}"
                print(f"\nFetching page {page}...")
                
                html = self._get_page(url)
                if not html:
                    print("Failed to fetch page. Retrying...")
                    retry_count += 1
                    if retry_count >= max_retries:
                        print("Max retries reached. Stopping collection.")
                        break
                    time.sleep(10)  # Wait before retry
                    continue
                
                retry_count = 0  # Reset retry count on successful page load
                
                # Wait for posts to load with multiple selectors
                print("Waiting for posts to load...")
                try:
                    # Try different selectors for posts
                    selectors = [
                        (By.CLASS_NAME, "status"),
                        (By.CLASS_NAME, "status__wrapper"),
                        (By.CLASS_NAME, "status__content")
                    ]
                    
                    for by, selector in selectors:
                        try:
                            WebDriverWait(self.driver, 20).until(
                                EC.presence_of_element_located((by, selector))
                            )
                            print(f"Posts found using selector: {selector}")
                            break
                        except TimeoutException:
                            continue
                    
                    # Additional wait for content to load
                    time.sleep(5)
                    
                except TimeoutException:
                    print("Timeout waiting for posts to load")
                    continue

                # Try different methods to find posts
                post_elements = []
                for by, selector in selectors:
                    try:
                        elements = self.driver.find_elements(by, selector)
                        if elements:
                            post_elements = elements
                            print(f"Found {len(elements)} posts using selector: {selector}")
                            break
                    except:
                        continue
                
                if not post_elements:
                    print("No posts found on page")
                    continue
                
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
                proxies.extend([f"https://{proxy}" for proxy in proxy_list])
                print(f"Added {len(proxy_list)} proxies from ProxyScrape")
        except Exception as e:
            print(f"Error fetching from ProxyScrape: {str(e)}")
            print("Please check if your API endpoint is correct and your IP is authenticated")
        
        # Test and filter proxies
        working_proxies = []
        for proxy in proxies:
            try:
                # Create a custom SSL context
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                response = requests.get(
                    'https://api.ipify.org?format=json',
                    proxies={'https': proxy},
                    timeout=5,
                    verify=False
                )
                if response.status_code == 200:
                    working_proxies.append(proxy)
                    print(f"Working proxy found: {proxy}")
            except:
                continue
        
        print(f"Found {len(working_proxies)} working proxies")
        return working_proxies 