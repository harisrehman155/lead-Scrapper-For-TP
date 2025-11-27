import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import logging
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self):
        self.base_url = os.getenv("TARGET_URL")
        if not self.base_url:
             logger.error("TARGET_URL not found in .env")
             # Fallback or raise error? For now, let's assume it's there or handle gracefully
             self.base_url = "" 

        self.login_url = f"{self.base_url}/index.php"
        self.invoice_url = f"{self.base_url}/invoiceDetail.php"
        
        self.username = os.getenv("SCRAPER_USERNAME")
        self.password = os.getenv("SCRAPER_PASSWORD")
        self.starting_id = int(os.getenv("STARTING_INVOICE_ID", "158696"))
        
        # State
        self.data = []
        self.emails_seen = set()
        self.blank_count = 0
        self.is_running = False
        self.current_id = self.starting_id
        self.total_records = 0
        self.visual_mode = False
        
        # Files - Updated paths for new structure
        # Assuming running from backend root, so output/ is correct
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.state_file = os.path.join(self.output_dir, "scraper_state.json")
        self.json_file = os.path.join(self.output_dir, "leads.json")
        self.data_file = os.path.join(self.output_dir, "invoices.xlsx") # Keep for export
        
        # Requests session
        self.session = requests.Session()
        
        # Playwright objects
        self.pw = None
        self.browser = None
        self.page = None
        
        self.load_state()
        self.load_existing_data()

    def toggle_mode(self, visual: bool):
        self.visual_mode = visual
        logger.info(f"Switched to {'Visual' if visual else 'Fast'} mode.")
        if not visual:
            self.close_browser()

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.current_id = state.get('last_invoice_id', self.starting_id)
                    self.total_records = state.get('total_records', 0)
                    logger.info(f"Resuming from Invoice ID: {self.current_id}")
            except Exception as e:
                logger.error(f"Error loading state: {e}")

    def save_state(self):
        state = {
            'last_invoice_id': self.current_id,
            'total_records': self.total_records
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f)

    def load_existing_data(self):
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r') as f:
                    self.data = json.load(f)
                
                # Rebuild emails_seen set
                for record in self.data:
                    if record.get('Email'):
                        self.emails_seen.add(record['Email'])
                        
                logger.info(f"Loaded {len(self.data)} existing records from JSON.")
            except Exception as e:
                logger.error(f"Error loading existing data: {e}")

    def save_data(self):
        if not self.data:
            return
            
        try:
            with open(self.json_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            logger.info(f"Saved {len(self.data)} records to {self.json_file}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def start_browser(self):
        if self.visual_mode and not self.browser:
            logger.info("Starting Playwright browser...")
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch(headless=False)
            self.page = self.browser.new_page()

    def close_browser(self):
        if self.browser:
            logger.info("Closing Playwright browser...")
            self.browser.close()
            self.pw.stop()
            self.browser = None
            self.page = None
            self.pw = None

    def login(self):
        logger.info(f"Attempting login ({'Visual' if self.visual_mode else 'Fast'})...")
        try:
            if self.visual_mode:
                self.start_browser()
                self.page.goto(self.login_url)
                
                try:
                    # Wait for form
                    self.page.wait_for_selector("input[name='Uname']", timeout=5000)
                    
                    # Fill credentials
                    self.page.fill("input[name='Uname']", self.username)
                    self.page.fill("input[name='password']", self.password)
                    
                    # Submit by pressing Enter
                    self.page.press("input[name='password']", "Enter")
                    
                    # Alternative: Click login button if Enter doesn't work
                    # self.page.click("button[type='submit']")
                except Exception as e:
                     logger.error(f"Visual login interaction failed: {e}")
                     # Take screenshot for debugging
                     self.page.screenshot(path="login_failed.png")
                     return False
                
                self.page.wait_for_load_state('networkidle')
                
                # Check success
                if "Logout" in self.page.content() or "dashboard" in self.page.url.lower() or "invoice" in self.page.url.lower():
                    logger.info("Visual login successful.")
                    return True
                
                logger.warning("Visual login verification failed.")
                self.page.screenshot(path="login_verification_failed.png")
                return False
            else:
                # Fast mode (Requests)
                payload = {
                    'Uname': self.username, # Updated field name
                    'password': self.password,
                    'login': 'Login' # This might need adjustment if the backend expects a specific button name
                }
                response = self.session.post(self.login_url, data=payload)
                cookies = self.session.cookies.get_dict()
                if 'session_username' in cookies or 'PHPSESSID' in cookies or "Logout" in response.text:
                     logger.info("Fast login successful.")
                     return True
                return False
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def get_page_content(self, url):
        if self.visual_mode:
            # Ensure browser is open and logged in
            if not self.page:
                if not self.login():
                    return None

            self.page.goto(url)
            # Check for redirect to login
            if "login" in self.page.url.lower() and "invoiceDetail" not in self.page.url:
                 logger.info("Redirected to login in visual mode.")
                 if self.login():
                     self.page.goto(url)
                 else:
                     return None
            return self.page.content()
        else:
            response = self.session.get(url)
            if "login" in response.url.lower():
                logger.info("Redirected to login in fast mode.")
                if self.login():
                    response = self.session.get(url)
                else:
                    return None
            return response.text

    def scrape_invoice(self, invoice_id):
        url = f"{self.invoice_url}?invoiceId={invoice_id}"
        try:
            html_content = self.get_page_content(url)
            if not html_content:
                return None

            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraction Logic (Updated based on user HTML)
            
            # Helper to find value in the next cell
            def get_next_cell_value(label_text):
                # Find the element containing the label
                label_elem = soup.find(string=lambda t: t and label_text in t)
                if not label_elem:
                    return ""
                
                # Navigate up to the td
                td = label_elem.find_parent('td')
                if not td:
                    return ""
                
                # Find the next td
                next_td = td.find_next_sibling('td')
                if not next_td:
                    return ""
                
                return next_td.get_text(strip=True)

            invoice_num = get_next_cell_value("Invoice #")
            
            # If we can't find the invoice number, it might be a blank page or invalid ID
            if not invoice_num:
                return None

            date_val = get_next_cell_value("Date:")

            # Bill To Section
            # The HTML shows labels like "Company :", "Name:", "Email:", "Address:"
            company = get_next_cell_value("Company :")
            name = get_next_cell_value("Name:")
            email = get_next_cell_value("Email:")
            address = get_next_cell_value("Address:")

            return {
                "Invoice #": invoice_num,
                "Date": date_val,
                "Name": name,
                "Email": email,
                "Company": company,
                "Address": address,
                "Phone #": ""
            }

        except Exception as e:
            logger.error(f"Error scraping invoice {invoice_id}: {e}")
            return None

    def run(self):
        self.is_running = True
        logger.info(f"Starting scraper in {'Visual' if self.visual_mode else 'Fast'} mode...")
        
        if not self.login():
            logger.error("Initial login failed. Stopping.")
            self.is_running = False
            self.close_browser()
            return

        while self.is_running:
            if self.blank_count >= 1000:
                logger.info("Reached 1000 consecutive blank records. Stopping.")
                self.is_running = False
                break

            logger.info(f"Processing Invoice ID: {self.current_id}")
            
            try:
                data = self.scrape_invoice(self.current_id)
                
                if data:
                    self.blank_count = 0
                    if data['Email'] and data['Email'] in self.emails_seen:
                        logger.info(f"Duplicate email found: {data['Email']}. Skipping.")
                    else:
                        if data['Email']:
                            self.emails_seen.add(data['Email'])
                        self.data.append(data)
                        self.total_records += 1
                        if len(self.data) % 10 == 0:
                            self.save_data()
                else:
                    self.blank_count += 1
                    logger.info(f"Blank/Invalid record. Consecutive blanks: {self.blank_count}")

                self.current_id += 1
                self.save_state()
                
                # Delay
                if self.visual_mode:
                    time.sleep(1) # Slower in visual mode to be watchable
                else:
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Unexpected error in run loop: {e}")
                self.save_data()
                self.is_running = False
                break
        
        self.save_data()
        self.save_state()
        self.close_browser()
        logger.info("Scraper stopped.")

    def stop(self):
        self.is_running = False

scraper_instance = Scraper()
