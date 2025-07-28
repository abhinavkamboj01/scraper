

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def extract_rfq_data(driver):
    cards = driver.find_elements(By.CLASS_NAME, 'rfq-search-item')
    data = []

    for card in cards:
        try:
            product_name = card.find_element(By.CLASS_NAME, 'title').text
            quantity = card.find_element(By.CLASS_NAME, 'requirement').text

            # Buyer country
            country = card.find_element(By.CLASS_NAME, 'country-name').text

            # Date posted
            date_posted = card.find_element(By.CLASS_NAME, 'date').text

            # Purchase Frequency (often missing)
            purchase_frequency = ""
            freq_el = card.find_elements(By.CLASS_NAME, 'frequency')
            if freq_el:
                purchase_frequency = freq_el[0].text

            # Category (optional)
            category = ""
            cat_el = card.find_elements(By.CLASS_NAME, 'cat')
            if cat_el:
                category = cat_el[0].text

            # Buyer Info
            buyer_info_parts = []
            if card.find_elements(By.CLASS_NAME, 'member-tag'):
                buyer_info_parts.append(card.find_element(By.CLASS_NAME, 'member-tag').text)

            if card.find_elements(By.XPATH, ".//span[contains(text(), 'Email Confirmed')]"):
                buyer_info_parts.append("Email Confirmed")

            if card.find_elements(By.XPATH, ".//span[contains(text(), 'Typically replies')]"):
                buyer_info_parts.append("Typically replies")

            buyer_info = " | ".join(buyer_info_parts)

            data.append({
                "Product Name": product_name,
                "Quantity": quantity,
                "Purchase Frequency": purchase_frequency,
                "Buyer Country": country,
                "Date Posted": date_posted,
                "Category": category,
                "Buyer Info": buyer_info
            })
        except Exception as e:
            print("⚠️ Skipped card due to error:", e)
    return data


def scrape_all_pages(url, max_pages=5):
    driver = setup_driver()
    driver.get(url)
    time.sleep(3)

    all_data = []
    for page in range(1, max_pages + 1):
        print(f"Scraping page {page}")
        all_data.extend(extract_rfq_data(driver))
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, 'button.next')
            if 'disabled' in next_button.get_attribute('class'):
                break
            next_button.click()
            time.sleep(3)
        except:
            break

    driver.quit()
    return all_data

if __name__ == "__main__":
    url = "https://sourcing.alibaba.com/rfq/rfq_search_list.htm?country=AE&recently=Y"
    data = scrape_all_pages(url, max_pages=10)
    df = pd.DataFrame(data)
    df.to_csv("alibaba_rfq_output.csv", index=False)
    print("✅ Output saved as alibaba_rfq_output.csv")
