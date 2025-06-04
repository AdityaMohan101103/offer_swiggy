import streamlit as st
import csv
import io
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Add your full list of Burger Singh URLs here
STORE_URLS = [
    "https://www.swiggy.com/restaurants/burger-singh-big-punjabi-burgers-ganeshguri-guwahati-579784",
    "https://www.swiggy.com/restaurants/burger-singh-big-punjabi-burgers-stational-club-durga-mandir-purnea-purnea-698848",
    # Add more URLs as needed
]

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode for Streamlit cloud
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        st.error(f"Error setting up Chrome driver: {str(e)}")
        return None

def get_store_name_from_url(url):
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
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))

        # Dismiss cookie or consent popup if any
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
            ).click()
        except (TimeoutException, NoSuchElementException):
            pass

        driver.execute_script("window.scrollTo(0, 1000);")  # Scroll down to load offers
        time.sleep(3)  # Wait for content to load

        offers = []

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
                    offer_elements.extend(elements)
            except:
                continue

        if not offer_elements:
            return []

        for element in offer_elements:
            try:
                element_text = element.text.strip()
                if not element_text or len(element_text) < 3:
                    continue

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

                title = title_element.text.strip() if title_element else element_text.split('\n')[0]
                description = desc_element.text.strip() if desc_element else (element_text.split('\n')[1] if '\n' in element_text else 'N/A')

                offers.append({
                    'store_name': get_store_name_from_url(url),
                    'store_url': url,
                    'title': title,
                    'description': description
                })
            except:
                continue

        return offers

    except Exception as e:
        st.error(f"Error processing store {url}: {str(e)}")
        return []

def remove_duplicates(offers):
    seen = set()
    unique_offers = []
    for offer in offers:
        key = (offer['store_name'], offer['title'], offer['description'])
        if key not in seen:
            seen.add(key)
            unique_offers.append(offer)
    return unique_offers

def scrape_all_stores(progress_text, progress_bar):
    driver = setup_driver()
    if not driver:
        return []

    all_offers = []
    total_stores = len(STORE_URLS)

    for i, url in enumerate(STORE_URLS, 1):
        offers = scrape_single_store(driver, url)
        all_offers.extend(offers)
        progress_text.text(f"Processed {i}/{total_stores} stores. Offers found: {len(all_offers)}")
        progress_bar.progress(i / total_stores)
        time.sleep(random.uniform(2, 5))

    driver.quit()

    all_offers = remove_duplicates(all_offers)
    return all_offers

def save_offers_to_csv(offers):
    output = io.StringIO()
    fieldnames = ['store_name', 'store_url', 'title', 'description']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    last_store = None
    for offer in offers:
        row = {}
        if last_store != offer['store_name']:
            row['store_name'] = offer['store_name']
            row['store_url'] = offer['store_url']
            last_store = offer['store_name']
        else:
            row['store_name'] = ''
            row['store_url'] = ''
        row['title'] = offer['title']
        row['description'] = offer['description']
        writer.writerow(row)

    return output.getvalue()

def main():
    st.title("🍔 Burger Singh Offers Scraper")
    st.write("Scrape current offers from Burger Singh restaurant pages on Swiggy.")

    if st.button("Start Scraping"):
        progress_text = st.empty()
        progress_bar = st.progress(0)

        offers = scrape_all_stores(progress_text, progress_bar)

        if offers:
            st.success(f"Scraping completed! Total unique offers found: {len(offers)}")
            df = pd.DataFrame(offers)
            st.dataframe(df)

            csv_data = save_offers_to_csv(offers)
            st.download_button(label="Download CSV", data=csv_data, file_name="burger_singh_offers.csv", mime="text/csv")
        else:
            st.warning("No offers found or scraping failed.")

if __name__ == "__main__":
    main()
