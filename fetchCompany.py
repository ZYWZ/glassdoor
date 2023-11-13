import time
import random
import logging

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

import csv

logging.basicConfig(filename='logs/scraper_fetchCompany.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')


def random_delay(minimum=10, maximum=15):
    """Wait for a random period of time between `minimum` and `maximum` seconds."""
    time.sleep(random.uniform(minimum, maximum))


def scrapeCompany(browser, url):
    results = []

    logging.info(f"Scraping started for URL: {url}")

    browser.get(url)

    random_delay()

    print(browser.current_url)

    wait = WebDriverWait(browser, 20)
    wait.until(EC.presence_of_element_located((By.ID, "Explore")))

    # Find all 'a' elements with the data-test attribute set to 'cell-Reviews-url'
    review_links = browser.find_elements(By.CSS_SELECTOR, 'a[data-test="cell-Reviews-url"]')

    # Extract the href attribute from each link
    company_links = [link.get_attribute('href') for link in review_links]

    unsuccessful_links = []
    # iterating through each company's "Overview" url
    for url in company_links:
        try:  # fail safe for inevitable errors
            print(url)
            results.append(url)
        except:  # fail safe for inevitable errors
            unsuccessful_links.append(url)  # adding unsuccessful urls to a list
            print('ERROR: ', url)  # optional code to see list of urls that don't scrape properly
            time.sleep(10)  # extra time here to let your internet catch up after an error

    logging.info(f"Scraping finished for URL: {url}")

    return results


# -----------------------------------------------------------------------------------------Original Code----------------------------------------------
# # Find all 'a' elements with the data-test attribute set to 'cell-Reviews-url'
# review_links = browser.find_elements(By.CSS_SELECTOR, 'a[data-test="cell-Reviews-url"]')
#
# # Extract the href attribute from each link
# review_urls = [link.get_attribute('href') for link in review_links]
#
# # Now you have all the URLs in the review_urls list
# for url in review_urls:
#     print(url)
#     results.append(url)
#
# return results
# -----------------------------------------------------------------------------------------Original Code----------------------------------------------

# # Find all elements that are company cards
# company_cards = browser.find_elements(By.XPATH, '//div[@data-test="employer-card-single"]')
#
# # Store URLs from the cards
# company_urls = []
#
# for card in company_cards:
#     # Random delay before each card click
#     random_delay()
#
#     # Scroll down by pixel
#     browser.execute_script("window.scrollBy(0, 500);")
#     random_delay(3, 5)
#
#     # Move to the card element
#     ActionChains(browser).move_to_element(card).perform()
#
#     # Use JavaScript click as an alternative to standard click
#     browser.execute_script("arguments[0].click();", card)
#
#     # Wait for the card to be clickable
#     wait = WebDriverWait(browser, 20)
#     wait.until(EC.number_of_windows_to_be(2))
#
#     # Store the ID of the original tab
#     original_window = browser.current_window_handle
#
#     # Switch to the new window (which is the last one in the list of windows)
#     new_window = [window for window in browser.window_handles if window != original_window][0]
#     browser.switch_to.window(new_window)
#
#     # Wait until the new page is loaded (identify a unique element on the new page to ensure it's loaded)
#     wait = WebDriverWait(browser, 20)
#     wait.until(EC.presence_of_element_located((By.ID, "MainContent")))
#     random_delay(30, 60)
#
#     # Get the current URL
#     company_urls.append(browser.current_url)
#     print(browser.current_url)
#
#     # Close the new tab if you are done with it
#     browser.close()
#
#     # Switch back to the original tab
#     browser.switch_to.window(original_window)


def scrapeCompanies():
    logging.info("Scraping job started.")

    base_url = "https://www.glassdoor.com.au/Reviews/index.htm?overall_rating_low=0&page={}&filterType=RATING_OVERALL"
    num_pages = 100
    urls = [base_url.format(i) for i in range(1, num_pages + 1)]

    options = webdriver.ChromeOptions()
    chrome_prefs = {}
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
    options.experimental_options["prefs"] = chrome_prefs
    # options.add_argument(
    #     r"--user-data-dir=C:\Users\liuxi\AppData\Local\Google\Chrome\User Data")  # e.g. C:\Users\You\AppData\Local\Google\Chrome\User Data
    # options.add_argument(r'--profile-directory=Default')  # e.g. Profile 3
    options.add_argument('--headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome(options=options)

    try:
        # Open a CSV file to write
        with open('results/company_urls.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write header with the new 'Status' column
            writer.writerow(['URL', 'Status'])

            for url in urls:
                results = scrapeCompany(browser, url)
                # Write each URL into the CSV file with 'Unscraped' as the status
                for result in results:
                    writer.writerow([result, 'Unscraped'])  # Write the URL and status into the file
                    logging.info(f"URL written to CSV: {result}")

    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}")

    finally:
        browser.close()
        logging.info("Browser closed and scraping job finished.")


if __name__ == '__main__':
    start_time = time.time()
    logging.info("The scraper script started.")

    scrapeCompanies()

    end_time = time.time()

    elapsed_time = end_time - start_time
    logging.info(f"The scraper took {elapsed_time} seconds to run.")
    print(f"The scraper took {elapsed_time} seconds to run.")
