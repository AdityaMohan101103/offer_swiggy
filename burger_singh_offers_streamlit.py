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

# Add Burger Singh store URLs here
STORE_URLS = [
    "https://www.swiggy.com/city/guwahati/burger-singh-big-punjabi-burgers-city-center-mall-christian-basti-rest579784",
    "https://www.swiggy.com/restaurants/burger-singh-big-punjabi-burgers-stational-club-durga-mandir-purnea-purnea-698848",
    # Add more URLs as needed
]

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        st.error(f"Error setting up Chrome driver: {str(e)}")
        return None

def get_store_name_from_url(url):
    try:
        if '/restaurants/' in url:
            parts = url.split('/restaurants/')[1].split('-')
            return ' '.join(parts[:-1]).title()
        return url
    except:
        return "Unknown Store"

def scrape_single_store(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))

        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
            ).click()
        except (TimeoutException, NoSuchElementException):
            pass

        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(3)

        offers = []

        offer_boxes = driver.find_elements(By.CSS_SELECTOR, "div[data-testid^='offer-card-container']")
        if not offer_boxes:
            offer_boxes = driver.find_elements(By.CSS_SELECTOR, "div.sc-dBmzty")  # fallback for some designs

        for box in offer_boxes:
            try:
                # Try different paths to get offer and code
                title = ""
                code = ""

                try:
                    title = box.find_element(By.CSS_SELECTOR, "div.sc-aXZVg.hsuIwO").text.strip()
                except:
                    title = box.text.split('\n')[0].strip()

                try:
                    code = box.find_element(By.CSS_SELECTOR, "div.sc-aXZVg.foYDCM").text.strip()
                except:
                    lines = box.text.strip().split('\n')
                    code = lines[1] if len(lines) > 1 else "N/A"

                if title and code:
                    offers.append({
                        'store_name': get_store_name_from_url(url),
                        'store_url': url,
                        'discounts': title,
                        'CODE': code
                    })
            except:
                continue

        return offers

    except Exception as e:
        st.error(f"Error processing store {url}: {str(e)}")
        return []

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
        time.sleep(random.uniform(2, 4))

    driver.quit()
    return all_offers

def save_offers_to_csv(offers):
    output = io.StringIO()
    fieldnames = ['store_name', 'store_url', 'discounts', 'CODE']
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
        row['discounts'] = offer['discounts']
        row['CODE'] = offer['CODE']
        writer.writerow(row)

    return output.getvalue()

def main():
    st.title("🍔 Burger Singh Offers Scraper")
    st.write("Scrape current offers (including BOGO) from Swiggy restaurant pages.")

    if st.button("Start Scraping"):
        progress_text = st.empty()
        progress_bar = st.progress(0)

        offers = scrape_all_stores(progress_text, progress_bar)

        if offers:
            st.success(f"Scraping completed! Total offers found: {len(offers)}")
            df = pd.DataFrame(offers)
            st.dataframe(df)

            csv_data = save_offers_to_csv(offers)
            st.download_button(label="📥 Download CSV", data=csv_data, file_name="burger_singh_offers.csv", mime="text/csv")
        else:
            st.warning("No offers found or scraping failed.")

if __name__ == "__main__":
    main()
