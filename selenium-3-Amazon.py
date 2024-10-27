import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import os

def launchBrowser():
    PATH = "C:\\Program Files (x86)\\chromedriver.exe"
    service = Service(PATH)

    # Configure Chrome options to suppress logging
    options = Options()
    options.add_argument("--log-level=3")  # Suppress logging

    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.amazon.com.au/s?k=cleanser&crid=GWRI2G5GRHLT&sprefix=cleanser%2Caps%2C389&ref=nb_sb_noss_1")

    # Initialize the JSON file
    json_file_path = 'amazon_search_results.json'
    if not os.path.exists(json_file_path):
        with open(json_file_path, 'w') as f:
            json.dump([], f)

    # while True:
        # Extract text and href from the specified XPath range
    for x in range(7, 61):
        xpath = f'//*[@id="search"]/div[1]/div[1]/div/span[1]/div[1]/div[{x}]/div/div/span/div/div/div[2]/div[1]/h2/a/span'
        try:
            element = driver.find_element(By.XPATH, xpath)
            parent_anchor = element.find_element(By.XPATH, './ancestor::a')
            href = parent_anchor.get_attribute('href')
            text = element.text
            # print(f"Text for X={x}: {text}")
            # print(f"Link for X={x}: {href}")

            # Append the new data to the JSON file
            with open(json_file_path, 'r+') as f:
                data = json.load(f)
                data.append({"text": text, "link": href})
                f.seek(0)
                json.dump(data, f, indent=4)
        except NoSuchElementException:
                print(f"No element found for X={x}")

        # # Check if the "Next" button is present and click it
        # try:
        #     next_button = driver.find_element(By.CSS_SELECTOR, "a.s-pagination-item.s-pagination-next")
        #     next_button.click()
        #     time.sleep(2)  # Wait for the next page to load
        # except NoSuchElementException:
        #     break




    
launchBrowser()