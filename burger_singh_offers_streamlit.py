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

# Add your list of Burger Singh store URLs here
STORE_URLS = [
    "https://www.swiggy.com/city/guwahati/burger-singh-big-punjabi-burgers-city-center-mall-christian-basti-rest579784",
    "https://www.swiggy.com/restaurants/burger-singh-big-punjabi-burgers-stational-club-durga-mandir-purnea-purnea-698848",
    # Add more URLs if needed
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
            parts = url.split('/restaurants/')[1].split('-rest')[0]
            return parts.replace('-', ' ').title()
        else:
            return url.split('/')[-1]
    except:
        return "unknown-store"

def scrape_single_store(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Try dismissing pop-ups
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
            ).click()
        except:
            pass

        time.sleep(3)
        offers = []

        offer_boxes = driver.find_elements(By.CSS_SELECTOR, "div[data-testid^='offer-card-container']")
        if not offer_boxes:
            return []

        seen = set()
        for box in offer_boxes:
            try:
                # Try getting offer title from image alt (for BOGO) or text
                try:
                    title = box.find_element(By.CSS_SELECTOR, "img[alt]").get_attribute("alt").strip()
                except:
                    title = box.find_element(By.CSS_SELECTOR, "div.sc-aXZVg.hsuIwO").text.strip()

                # Get offer code
                code = box.find_element(By.CSS_SELECTOR, "div.sc-aXZVg.foYDCM").text.strip()

                key = (title, code)
                if key in seen:
                    continue
                seen.add(key)

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
    total = len(STORE_URLS)

    for i, url in enumerate(STORE_URLS, 1):
        offers = scrape_single_store(driver, url)
        all_offers.extend(offers)
        progress_text.text(f"Processed {i}/{total} stores. Total offers: {len(all_offers)}")
        progress_bar.progress(i / total)
        time.sleep(random.uniform(1.5, 3.5))

    driver.quit()
    return all_offers

def save_offers_to_csv(offers):
    output = io.StringIO()
    fieldnames = ['store_name', 'store_url', 'discounts', 'CODE']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    last_store = ""
    for offer in offers:
        row = {
            'store_name': offer['store_name'] if offer['store_name'] != last_store else '',
            'store_url': offer['store_url'] if offer['store_name'] != last_store else '',
            'discounts': offer['discounts'],
            'CODE': offer['CODE']
        }
        last_store = offer['store_name']
        writer.writerow(row)

    return output.getvalue()

def main():
    st.title("🍔 Burger Singh Offers Scraper")
    st.write("Get live offers from Swiggy restaurant pages for Burger Singh.")

    if st.button("Start Scraping"):
        progress_text = st.empty()
        progress_bar = st.progress(0)

        offers = scrape_all_stores(progress_text, progress_bar)

        if offers:
            st.success(f"Scraping completed! {len(offers)} offers found.")
            df = pd.DataFrame(offers)
            st.dataframe(df)

            csv_data = save_offers_to_csv(offers)
            st.download_button("Download CSV", csv_data, "burger_singh_offers.csv", "text/csv")
        else:
            st.warning("No offers found or something went wrong.")

if __name__ == "__main__":
    main()
