import streamlit as st
import csv
import io
import random
from datetime import datetime
import pandas as pd
import requests

# The list of URLs (truncated for brevity, you can expand with the full list)
STORE_URLS = [
    "https://www.swiggy.com/restaurants/burger-singh-big-punjabi-burgers-ganeshguri-guwahati-579784",
    "https://www.swiggy.com/restaurants/burger-singh-big-punjabi-burgers-stational-club-durga-mandir-purnea-purnea-698848",
    "https://www.swiggy.com/restaurants/burger-singh-gaya-city-gaya-701361",
    # Add the full list as needed...
]

def get_store_name_from_url(url):
    try:
        if '/city/' in url:
            parts = url.split('/city/')[1].split('/')
            city = parts[0] if parts else 'unknown'
            location = parts[1].split('-rest')[0] if len(parts) > 1 else 'unknown'
            return f"{city} - {location}"
        elif '/restaurants/' in url:
            parts = url.split('/restaurants/')[1].split('-rest')[0]
            return parts.replace('-', ' ').title()
        else:
            return url.split('/')[-1]
    except:
        return "unknown-store"

def fetch_offers_from_api(store_url):
    """
    This is a placeholder function to demonstrate how to fetch offers using API.
    Currently Swiggy does not provide a public API for offers, so you need to replace
    this with a proper API call or another data source if available.
    """
    # For demonstration, we return a dummy offer
    dummy_offer = {
        'store_name': get_store_name_from_url(store_url),
        'store_url': store_url,
        'title': '20% off on all burgers',
        'description': 'Use code BURGER20 to get 20% discount on all burgers.'
    }
    return [dummy_offer]

def scrape_all_stores(progress_callback=None):
    all_offers = []
    total_stores = len(STORE_URLS)

    for i, url in enumerate(STORE_URLS, 1):
        # Replace below line with actual API scraping logic
        offers = fetch_offers_from_api(url)
        all_offers.extend(offers)

        if progress_callback:
            progress_callback(i, total_stores, len(all_offers))

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
    st.title("🍔 Burger Singh Offers Scraper (API Placeholder)")
    st.write("This is a demo Streamlit interface using a placeholder API fetch function to show how to connect scraping logic without Selenium.")
    
    if st.button("Start Scraping"):
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        def progress_callback(i, total, offers_count):
            progress_text.text(f"Processing store {i} of {total} — Offers found so far: {offers_count}")
            progress_bar.progress(i / total)
        
        offers = scrape_all_stores(progress_callback)
        
        if offers:
            st.success(f"Scraping completed! Total offers found: {len(offers)}")
            display_data = []
            for offer in offers:
                display_data.append({
                    "Store Name": offer['store_name'],
                    "Store URL": offer['store_url'],
                    "Offer Title": offer['title'],
                    "Offer Description": offer['description']
                })
            df = pd.DataFrame(display_data)
            st.dataframe(df)

            csv_data = save_offers_to_csv(offers)
            st.download_button(label="Download CSV", data=csv_data, file_name="burger_singh_offers.csv", mime="text/csv")
        else:
            st.warning("No offers found or scraping failed.")

if __name__ == "__main__":
    main()

