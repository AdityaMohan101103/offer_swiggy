import csv
import os
from datetime import datetime
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Complete list of Burger Singh store URLs
STORE_URLS = [
    # (url list truncated for brevity; use full list as previously provided)
    "https://www.swiggy.com/restaurants/burger-singh-big-punjabi-burgers-ganeshguri-guwahati-579784",
    "https://www.swiggy.com/restaurants/burger-singh-big-punjabi-burgers-stational-club-durga-mandir-purnea-purnea-698848",
    # Add the rest of the URLs...
]

def get_desktop_path():
    """Get the desktop path for the current user"""
    return os.path.join(os.path.expanduser("~"), "Desktop")

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Uncomment the next line if you want to run in headless mode (no browser window)
    # chrome_options.add_argument("--headless")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {str(e)}")
        return None

def get_store_name_from_url(url):
    """Extract store location/name from URL for identification"""
    try:
        if '/city/' in url:
            parts = url.split('/city/')[1].split('/')
            city = parts[0] if parts else 'unknown'
            location = parts[1].split('-rest')[0] if len(parts) > 1 else 'unknown'
            return f"{city}-{location}"
        elif '/restaurants/' in url:
            parts = url.split('/restaurants/')[1].split('-rest')[0]
            return parts.replace('-', ' ').title()
        else:
            return url.split('/')[-1]
    except:
        return "unknown-store"

def scrape_single_store(driver, url):
    """Scrape offers from a single store"""
    try:
        print(f"Processing: {get_store_name_from_url(url)}")
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        
        # Try to find and click any cookie acceptance or location popup
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))).click()
            print("Accepted cookie popup.")
        except (TimeoutException, NoSuchElementException):
            print("No cookie acceptance popup found or already accepted.")
        
        # Scroll down to make sure offers section is loaded
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(3)
        
        offers = []
        
        # Multiple selector strategies
        selectors_to_try = [
            "div[data-testid*='offer-card-container']",
            "div.sc-dExYaf.hQBmmU",
            "div[class*='offer']",
            "//div[contains(@class, 'offer') or contains(@data-testid, 'offer')]",
            "//h2[contains(text(), 'Deals') or contains(text(), 'Offers')]/following-sibling::*//div",
        ]
        
        offer_elements = []
        
        for selector in selectors_to_try:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    offer_elements.extend(elements)  # Collect all found elements
            except Exception as e:
                print(f"Error finding elements with selector {selector}: {str(e)}")
                continue
        
        if not offer_elements:
            print("No offer elements found.")
            return []
        
        # Extract data from found elements
        for element in offer_elements:
            try:
                offer_data = {}
                
                element_text = element.text.strip()
                
                if not element_text or len(element_text) < 3:
                    continue
                
                # Try to find title and description within the element
                title_element = None
                desc_element = None
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, "div[class*='title'], h3, h4")
                except:
                    pass
                
                try:
                    desc_element = element.find_element(By.CSS_SELECTOR, "div[class*='desc'], span[class*='code']")
                except:
                    pass
                
                offer_data['title'] = title_element.text.strip() if title_element else element_text.split('\n')[0]
                offer_data['description'] = desc_element.text.strip() if desc_element else (element_text.split('\n')[1] if '\n' in element_text else 'N/A')
                
                # Add metadata
                offer_data['store_name'] = get_store_name_from_url(url)
                offer_data['store_url'] = url
                
                # Skip if title is too generic or empty
                if offer_data['title'] in ['N/A', ''] or len(offer_data['title']) < 3:
                    continue
                
                offers.append(offer_data)
                
            except Exception as e:
                print(f"Error extracting offer data: {str(e)}")
                continue
        
        print(f"  Found {len(offers)} offers for {get_store_name_from_url(url)}")
        return offers
        
    except Exception as e:
        print(f"  Error processing store: {str(e)}")
        return []

def scrape_all_stores():
    """Scrape offers from all stores in the list"""
    driver = setup_driver()
    if not driver:
        return []
    
    all_offers = []
    total_stores = len(STORE_URLS)
    
    print(f"=== BURGER SINGH OFFERS SCRAPER ===")
    print(f"Total stores to process: {total_stores}")
    print("Starting scraping process...\n")
    
    try:
        for i, url in enumerate(STORE_URLS, 1):
            print(f"[{i}/{total_stores}] ", end="")
            
            try:
                offers = scrape_single_store(driver, url)
                all_offers.extend(offers)
                
                # Add random delay between stores to avoid being blocked
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                print(f"  Error with store {i}: {str(e)}")
                continue
            
            # Print progress every 10 stores
            if i % 10 == 0:
                print(f"\n--- Progress: {i}/{total_stores} stores completed, {len(all_offers)} total offers found ---\n")
        
        return all_offers
        
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user. Saving collected data...")
        return all_offers
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        return all_offers
    finally:
        driver.quit()

def save_to_csv(offers, filename=None):
    """Save offers data to CSV file on desktop."""
    if not offers:
        print("No offers to save!")
        return
    
    desktop_path = get_desktop_path()
    
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"burger_singh_offers_{timestamp}.csv"
    
    filepath = os.path.join(desktop_path, filename)
    
    # Define CSV headers
    fieldnames = ['store_name', 'store_url', 'title', 'description']
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            last_store = None
            for offer in offers:
                row = {}
                if last_store != offer['store_name']:
                    row['store_name'] = offer.get('store_name', '')
                    row['store_url'] = offer.get('store_url', '')
                    last_store = offer['store_name']
                else:
                    row['store_name'] = ''
                    row['store_url'] = ''
                row['title'] = offer.get('title', '')
                row['description'] = offer.get('description', '')
                writer.writerow(row)
        
        print(f"\n✅ SUCCESS! Offers saved to: {filepath}")
        print(f"📊 Total offers saved: {len(offers)}")
        
    except Exception as e:
        print(f"❌ Error saving to CSV: {str(e)}")

def main():
    """Main function to run the complete scraping process"""
    print("🍔 BURGER SINGH OFFERS SCRAPER")
    print("=" * 50)
    print("This will scrape offers from all Burger Singh stores.")
    print(f"Total stores: {len(STORE_URLS)}")
    print("Method: Selenium (automated browser)")
    print("Output: CSV file saved to desktop")
    print("=" * 50)
    
    offers = scrape_all_stores()
    save_to_csv(offers)

if __name__ == "__main__":
    main()
