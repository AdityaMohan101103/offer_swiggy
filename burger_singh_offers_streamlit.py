import streamlit as st
import time
import random
import pandas as pd
import undetected_chromedriver.v2 as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

STORE_URLS = [
    "https://www.swiggy.com/restaurants/burger-singh-big-punjabi-burgers-ganeshguri-guwahati-579784",
    "https://www.swiggy.com/restaurants/burger-singh-big-punjabi-burgers-stational-club-durga-mandir-purnea-purnea-698848"
]

def get_store_name_from_url(url):
    try:
        if '/restaurants/' in url:
            parts = url.split('/restaurants/')[1].split('-rest')[0]
            return parts.replace('-', ' ').title()
        else:
            return url.split('/')[-1]
    except:
        return "unknown-store"

def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = uc.Chrome(options=options)
    return driver

def scrape_single_store(driver, url):
    offers = []
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))

        try:
            accept_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
            )
            accept_btn.click()
        except:
            pass

        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(3)

        offer_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-testid*='offer-card-container']")
        for el in offer_elements:
            text = el.text.strip()
            if text:
                lines = text.split('\n')
                title = lines[0]
                desc = lines[1] if len(lines) > 1 else 'N/A'
                offers.append({
                    'store_name': get_store_name_from_url(url),
                    'store_url': url,
                    'title': title,
                    'description': desc
                })
    except Exception as e:
        st.error(f"Error scraping {url}: {e}")
    return offers

def scrape_all_stores(progress_text, progress_bar):
    driver = setup_driver()
    all_offers = []
    total = len(STORE_URLS)
    for i, url in enumerate(STORE_URLS, 1):
        offers = scrape_single_store(driver, url)
        all_offers.extend(offers)
        progress_text.text(f"Processed {i}/{total} stores. Offers found: {len(all_offers)}")
        progress_bar.progress(i / total)
        time.sleep(random.uniform(2, 4))
    driver.quit()
    return all_offers

def main():
    st.title("🍔 Burger Singh Offers Scraper")
    st.write("Scrape current offers from Burger Singh Swiggy pages.")

    if st.button("Start Scraping"):
        progress_text = st.empty()
        progress_bar = st.progress(0)

        offers = scrape_all_stores(progress_text, progress_bar)

        if offers:
            df = pd.DataFrame(offers)
            st.success(f"Scraping complete. {len(offers)} offers found.")
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False), "offers.csv", "text/csv")
        else:
            st.warning("No offers found.")

if __name__ == "__main__":
    main()
