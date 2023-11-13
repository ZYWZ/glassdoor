import pandas as pd
import time
import random
import logging
import re
import json

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from bs4 import BeautifulSoup

import csv

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotVisibleException,
    WebDriverException
)

logging.basicConfig(filename='logs/scraper_searchCompanyList.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')


def random_delay(minimum=10, maximum=15):
    """Wait for a random period of time between `minimum` and `maximum` seconds."""
    time.sleep(random.uniform(minimum, maximum))


def restart_driver():
    global browser
    try:
        browser.quit()
    except Exception as e:
        print(f"Error closing the driver: {e}")

    options = webdriver.ChromeOptions()
    chrome_prefs = {}
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
    options.experimental_options["prefs"] = chrome_prefs
    # options.add_argument(
    #     r"--user-data-dir=C:\Users\liuxi\AppData\Local\Google\Chrome\User Data")  # e.g. C:\Users\You\AppData\Local\Google\Chrome\User Data
    # options.add_argument(r'--profile-directory=Default')  # e.g. Profile 3
    # options.add_argument('--headless')
    options.add_argument('window-size=1920x1080')
    # options.add_argument(
    #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
        # ... add as many user agents as you need
    ]
    # Randomly choose a user agent from the list
    random_user_agent = random.choice(user_agents)
    options.add_argument(f'user-agent={random_user_agent}')

    browser = webdriver.Chrome(options=options)
    browser.maximize_window()

def get_company_name_list(file_path):
    # Reading the first sheet (sheets are 0-indexed)
    company_name = pd.read_excel(file_path, sheet_name=0, usecols="A")

    # company_ticker = pd.read_excel(file_path, sheet_name=0, usecols="C")

    companies = company_name.iloc[:, 0].tolist()

    company_names = []
    tickers = []

    for item in companies:
        # Splitting the string into name and ticker parts
        name, ticker_info = item.split(' (')
        ticker = ticker_info.split(':')[-1].rstrip(')')

        # Removing the trailing '.' if the name ends with 'Inc.'
        if name.endswith('Inc.'):
            name = name.rstrip('.')

        company_names.append(name)
        tickers.append(ticker)

    print("Company Names:", company_names)
    print("Tickers:", tickers)

    return company_names


def search_for_company(name):
    url = None
    company_info = None
    # restart_driver()
    try:
        logging.info(f"Searching for Company Name: {name}.")
        # Open the URL
        browser.get('https://www.glassdoor.com.au/Community/index.htm')

        # Find and click the search button
        search_button = browser.find_element(By.CLASS_NAME, "search__searchBarStyles__searchButton")
        search_button.click()

        # Wait for the input field to be available and find it
        input_field = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "sc.keyword"))
        )

        # Enter company name in the input field
        input_field.send_keys(name)

        random_delay(3, 5)
        input_field.send_keys(Keys.DOWN)
        random_delay(1, 3)
        input_field.send_keys(Keys.RETURN)

        # Wait for the new page to load and for the <ul> element to be present
        ul_element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "employer-overview__employer-overview-module__employerDetails"))
        )

        # Extracting information from the <ul> element
        company_info = ul_element.text.replace('\n', '; ')
        print("Extracted Information:", company_info)

        url = browser.current_url

    except NoSuchElementException as e:
        logging.error(f"An error occurred during scraping: {e}. Element not found. Skipping.")
        random_delay(30, 60)
        pass
    except TimeoutException as e:
        logging.error(f"An error occurred during scraping: {e}. Page load timed out. Skipping.")
        random_delay(30, 60)
        pass
    except WebDriverException as e:
        logging.error(f"An error occurred during scraping: {e}. WebDriver error. Skipping.")
        random_delay(30, 60)
        pass
    except Exception as e:
        logging.error(
            f"An error occurred during scraping: {e}. An unexpected error occurred. Skipping.")
        random_delay(30, 60)
        pass

    finally:
        # Close the browser after some time or after your operations are done
        restart_driver()

    return url, company_info


if __name__ == '__main__':
    company_names = get_company_name_list('SPGlobal_IndexProfile_Constituents.xls')

    failed_list = []

    restart_driver()

    with open('company_info.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Company Name', 'URL', 'Company Info'])

        for name in company_names[:5]:
            url, company_info = search_for_company(name)
            if url:
                writer.writerow([name, url, company_info])
            else:
                failed_list.append(name)

            random_delay(5, 10)

        while failed_list:
            for name in failed_list[:]:
                url, company_info = search_for_company(name)
                if url:
                    writer.writerow([name, url, company_info])
                    failed_list.remove(name)
                random_delay(5, 10)

