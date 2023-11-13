import time
import random
import logging
import re
import json
import os

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

logging.basicConfig(filename='logs/scraper_fetchReview.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

DEFAULT_PAGE_NUMBER = 1


def get_total_review_pages(url):
    logging.info(f"Finding the total number of review pages.")
    browser.get(url)
    print(browser.current_url)

    element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "paginationFooter"))
    )

    source = browser.page_source
    soup = BeautifulSoup(source, 'html.parser')

    # Regular expression pattern to match the number of reviews
    pattern = r'of ([\d,]+) Reviews'

    # Find the 'paginationFooter' element
    pagination_footer = soup.find('div', class_='paginationFooter')

    if pagination_footer:
        matches = re.findall(pattern, pagination_footer.text)
        if matches:
            num_reviews_str = matches[0].replace(',', '')
            num_reviews = int(num_reviews_str)
            logging.info(f"Finding a total of {num_reviews} reviews.")
            print(f"Finding a total of {num_reviews} reviews.")

            num_page = round(num_reviews / 10)

            return num_page
    else:
        print("Pagination footer not found.")
        logging.error("No total review number found.")

    return None


def get_total_salary_pages(url):
    logging.info(f"Finding the total number of salary pages.")
    browser.get(url)
    print(browser.current_url)

    time.sleep(10)

    source = browser.page_source
    soup = BeautifulSoup(source, 'html.parser')

    # Find all <nav> elements
    navs = soup.find_all('nav')

    # Initialize the variable to store the number of viewable objects
    num_viewable_objects = 0

    # Check if we have any <nav> elements
    if navs:
        # Get the last <nav> element
        last_nav = navs[-1]

        # Find the <p> element that immediately follows the last <nav>
        p_after_last_nav = last_nav.find_next_sibling('p')

        # Use a regular expression to find the number
        if p_after_last_nav:
            matches = re.search(r'of (\d+)', p_after_last_nav.text)
            if matches:
                num_viewable_objects = int(matches.group(1).replace(',', ''))
                print(num_viewable_objects)  # Output should be 6960
                logging.info(f"Finding a total of {num_viewable_objects} salary records.")
                print(f"Finding a total of {num_viewable_objects} salary records.")

                num_page = round(num_viewable_objects / 20)

                return num_page

            else:
                logging.error("No numeric value found in paragraph.")
        else:
            logging.error("No <p> element found after the last <nav>.")
    else:
        logging.error("No <nav> elements found on the page.")

    return None


def get_total_interview_pages(url):
    logging.info(f"Finding the total number of interview pages.")
    browser.get(url)
    print(browser.current_url)

    element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "paginationFooter"))
    )

    source = browser.page_source
    soup = BeautifulSoup(source, 'html.parser')

    # Regular expression pattern to match the number of reviews
    pattern = r'of ([\d,]+)'

    # Find the 'paginationFooter' element
    pagination_footer = soup.find('div', class_='paginationFooter')

    if pagination_footer:
        matches = re.findall(pattern, pagination_footer.text)
        if matches:
            num_interviews_str = matches[0].replace(',', '')
            num_interviews = int(num_interviews_str)
            logging.info(f"Finding a total of {num_interviews} interviews.")
            print(f"Finding a total of {num_interviews} interviews.")

            num_page = round(num_interviews / 10)

            return num_page
    else:
        print("Pagination footer not found.")
        logging.error("No total interview number found.")

    return None


def get_benefit_list(url):
    browser.get(url)
    print(browser.current_url)

    source = browser.page_source
    soup = BeautifulSoup(source, 'html.parser')

    # Find the div with aria-label 'Location'
    location_div = soup.find('div', {'aria-label': 'Location'})

    # Initialize an empty list for country names
    country_names = []

    if location_div:
        # Find all <span> elements with class 'dropdownOptionLabel' within the location_div
        country_name_elements = location_div.find_all('span', class_='dropdownOptionLabel')

        # Extract the text from each <span> element and replace spaces with hyphens
        country_names = [elem.get_text(strip=True).replace(' ', '-') for elem in country_name_elements]

    # Find the select with data-test 'employee-status-filter' and get option values
    employee_status_select = soup.find('select', {'data-test': 'employee-status-filter'})
    employee_status_values = []
    if employee_status_select:
        option_elements = employee_status_select.find_all('option')
        employee_status_values = [option.get('value') for option in option_elements]

    # If the first value is 'None', remove it
    if employee_status_values and employee_status_values[0] is None:
        employee_status_values.pop(0)

    return country_names, employee_status_values


def random_delay(minimum=10, maximum=15):
    """Wait for a random period of time between `minimum` and `maximum` seconds."""
    time.sleep(random.uniform(minimum, maximum))


def get_interview_url(company, idx):
    return f"https://www.glassdoor.com/Interview/{company}-Interview-Questions-{idx}_P{{}}.htm"


def get_salary_url(company, idx):
    return f"https://www.glassdoor.com/Salary/{company}-Salaries-{idx}_P{{}}.htm"


def get_benefit_url(company, idx):
    # return f"https://www.glassdoor.com.au/Benefits/{company}-Benefits-{idx}.htm"
    url = f"https://www.glassdoor.com/Benefits/{company}-Benefits-{idx}.htm"
    country_names, employee_status_values = get_benefit_list(url)

    results = []
    for status in employee_status_values:
        results.append(
            f"https://www.glassdoor.com/Benefits/{company}-Benefits-{idx}.htm?filter.employmentStatus={status}")

    return results


def get_diversity_url(company, idx):
    return f"https://www.glassdoor.com/Culture/{company}-DEI-{idx}.htm"


def processTopReview(top_reviews):
    ratings, titles, dates, employees, employee_details, locations, pros, cons = ([] for _ in range(8))

    is_recommends = []
    is_ceo_approvals = []
    is_business_outlooks = []
    # Define the mapping for each index to the corresponding category
    category_mapping = {
        0: is_recommends,
        1: is_ceo_approvals,
        2: is_business_outlooks
    }

    for review in top_reviews:
        # Extract rating
        rating_element = review.find(class_='review-details__review-details-module__overallRating')
        rating = rating_element.text.strip() if rating_element else None

        # Extract title
        title_element = review.find(
            class_='review-details__review-details-module__detailsLink review-details__review-details-module__title')
        title = title_element.text.strip() if title_element else None

        # Extract date
        date_element = review.find(class_='review-details__review-details-module__reviewDate')
        date = date_element.text.strip() if date_element else None

        # Extract employee
        employee_element = review.find(class_='review-details__review-details-module__employee')
        employee = employee_element.text.strip() if employee_element else None

        # Extract employee details
        employee_detail_element = review.find(class_='review-details__review-details-module__employeeDetails')
        employee_detail = employee_detail_element.text.strip() if employee_detail_element else None

        # Extract location
        location_element = review.find(class_='review-details__review-details-module__location')
        location = location_element.text.strip() if location_element else None

        # Extract Review detail
        review_detail = review.find(class_='review-details__review-details-module__iconContainer')

        # Define the sentiment SVG path values
        approve_path = "m8.835 17.64-3.959-3.545a1.19 1.19 0 0 1 0-1.735 1.326 1.326 0 0 1 1.816 0l3.058 2.677 7.558-8.678a1.326 1.326 0 0 1 1.816 0 1.19 1.19 0 0 1 0 1.736l-8.474 9.546c-.501.479-1.314.479-1.815 0Z"
        disapprove_path = "M18.299 5.327a1.5 1.5 0 0 1 0 2.121l-4.052 4.051 4.052 4.053a1.5 1.5 0 0 1-2.121 2.121l-4.053-4.052-4.051 4.052a1.5 1.5 0 0 1-2.122-2.121l4.052-4.053-4.052-4.051a1.5 1.5 0 1 1 2.122-2.121l4.05 4.051 4.054-4.051a1.5 1.5 0 0 1 2.12 0Z"
        no_opinion_rect = "width=\"17.461\" height=\"3\" x=\"3.395\" y=\"10\""
        na_circle = "cx=\"12\" cy=\"12\" r=\"7.5\""

        # Search for SVG paths in the document
        svg_elements = review_detail.find_all('svg')

        for idx, svg in enumerate(svg_elements):
            path = svg.find('path', {'d': approve_path})
            if path:
                # This SVG represents "Approve"
                category_mapping.get(idx).append("Approve")
            path = svg.find('path', {'d': disapprove_path})
            if path:
                # This SVG represents "Disapprove"
                category_mapping.get(idx).append("Disapprove")
            rect = svg.find('rect', {'width': '17.461'})
            if rect:
                # This SVG represents "No Opinion"
                category_mapping.get(idx).append("No Opinion")
            circle = svg.find('circle', {'r': '7.5'})
            if circle:
                # This SVG represents "N/A"
                category_mapping.get(idx).append("N/A")

        # Extract pro
        pro_element = review.find('span', {'data-test': 'pros'})
        pro = pro_element.text.strip() if pro_element else None

        # Extract con
        con_element = review.find('span', {'data-test': 'cons'})
        con = con_element.text.strip() if con_element else None

        ratings.append(rating)
        titles.append(title)
        dates.append(date)
        employees.append(employee)
        employee_details.append(employee_detail)
        locations.append(location)
        pros.append(pro)
        cons.append(con)

    return ratings, titles, dates, employees, employee_details, locations, is_recommends, is_ceo_approvals, is_business_outlooks, pros, cons


def scrapeDiversityPage(url):
    browser.get(url)
    print(browser.current_url)

    # Wait for the div with class 'css-xjxhjz egu3u860' to be present
    dropdown = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".css-xjxhjz.egu3u860"))
    )

    random_delay(1, 3)

    # Find the 'selectedLabel' within the dropdown and click it to open the list
    selected_label = dropdown.find_element(By.CSS_SELECTOR, ".selectedLabel")
    selected_label.click()

    # Wait for the options to be visible after the dropdown is clicked
    options = WebDriverWait(browser, 10).until(
        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".css-xjxhjz.egu3u860 .dropdownOption"))
    )

    results = []
    # Click each dropdown option from top to bottom
    for index, option in enumerate(options):

        # If we are on the last item, we may need to scroll within the dropdown
        if index == len(options) - 1:
            # Scroll the dropdown list
            browser.execute_script("arguments[0].parentNode.scrollTop = arguments[0].parentNode.scrollHeight", option)
            time.sleep(1)  # Adding delay to ensure the dropdown scrolls before the next command

        # Wait for option to be clickable
        WebDriverWait(browser, 10).until(EC.element_to_be_clickable(option))

        option.click()

        # After the page updates, locate the div and click all buttons inside it
        demographic_buttons_div = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".d-flex.flex-wrap.demographicOptions"))
        )
        buttons = demographic_buttons_div.find_elements(By.TAG_NAME, "button")

        for button in buttons:
            # Click the button to open the modal
            WebDriverWait(browser, 10).until(EC.element_to_be_clickable(button)).click()

            # Wait for the modal content to be visible
            modal_content = WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "modal_content"))
            )

            # Extract the title (assuming there's only one h2 with class 'mt-0 mb css-93svrw el6ke055' within the modal)
            modal_title = modal_content.find_element(By.CSS_SELECTOR, "h2.mt-0.mb.css-93svrw.el6ke055").text

            # Extract the overall rating (assuming there's only one span with class 'my-0 mr-xsm gd-ui-star css-1dq5rja el6ke054' within the modal)
            overall_rating = modal_content.find_element(By.CSS_SELECTOR,
                                                        "span.my-0.mr-xsm.gd-ui-star.css-1dq5rja.el6ke054").text

            # Find all the tspan elements with the specified class
            percentage_elements = modal_content.find_elements(By.CSS_SELECTOR, "tspan.emtn-lc7fha")

            # Retrieve the text content from each element which is the percentage number
            percentages = [elem.text + "%" for elem in percentage_elements]

            # Find all the div elements for the rating categories
            rating_divs = modal_content.find_elements(By.CSS_SELECTOR,
                                                      "div.ratingBarFill.d-flex.justify-content-end.align-items-center.px-xsm")

            # Retrieve the text content (rating) from each element
            ratings = [div.text for div in rating_divs]

            # Initialize the list with modal title and overall rating
            result = [modal_title, overall_rating]
            # Extend the list with the percentages
            result.extend(percentages)
            # Extend the list with the ratings
            result.extend(ratings)

            # Save the result to the returned list
            results.append(result)

            # Wait for the close button to be clickable
            close_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[@alt='Close']"))
            )

            close_button.click()

            # Ensure the modal has disappeared before clicking the next button
            WebDriverWait(browser, 10).until(
                EC.invisibility_of_element_located((By.XPATH, "//span[@alt='Close']"))
            )

        random_delay(1, 3)

        # You may need to click the dropdown again to open the list for subsequent options
        selected_label.click()

    return results


def scrapeBenefitPage(url):
    browser.get(url)
    print(browser.current_url)

    source = browser.page_source
    soup = BeautifulSoup(source, 'html.parser')

    # Find the div with 'data-test="benefit-rating"'
    rating_div = soup.find('div', {'data-test': 'benefit-rating'})

    # Extract the rating (assuming it is inside the <strong> tag as per your HTML structure)
    star_rating = rating_div.find('strong').get_text() if rating_div else None

    # Find the div that contains the number of ratings (you might need to adjust the selector based on the actual HTML content)
    ratings_div = soup.find('div', {'class': 'd-flex justify-content-center mb css-1uyte9r'})
    number_of_ratings = ratings_div.get_text(strip=True) if ratings_div else None

    def get_employment_status_from_url(url):
        # Check if the 'employmentStatus' is in the URL
        if 'filter.employmentStatus=' in url:
            # Split the URL on 'filter.employmentStatus=' and take the second part
            status_part = url.split('filter.employmentStatus=')[1]
            # Split on '&' in case there are more query parameters after 'employmentStatus'
            status = status_part.split('&')[0]
            return status
        return None

    status = get_employment_status_from_url(url)
    # Print results
    print("Temployee status:", status)
    print("Star Rating:", star_rating)
    print("Number of Ratings:", number_of_ratings)

    return status, star_rating, number_of_ratings


# def scrapeBenefitPage(browser, url):
#     browser.get(url)
#
#     # Wait for the listbox with 'data-test="location-filterContent"' to be present
#     location_filter = WebDriverWait(browser, 10).until(
#         EC.presence_of_element_located((By.XPATH, '//div[@data-test="location-filterContent"]'))
#     )
#
#     # Click the element which is used to open the dropdown, assuming it is labeled 'selectedLabel' under the location_filter
#     location_filter_label = location_filter.find_element(By.XPATH, './/div[contains(@class, "selectedLabel")]')
#     location_filter_label.click()  # This should open the dropdown
#
#     # Wait for the dropdown options to be visible after clicking the dropdown
#     location_options = WebDriverWait(browser, 10).until(
#         EC.visibility_of_any_elements_located(
#             (By.XPATH, './/div[@data-test="location-filterContent"]//div[contains(@class, "dropdownOption")]'))
#     )
#
#     random_delay(1, 3)
#
#     for location_option in location_options:
#         # Click the location dropdown option
#         location_option.click()
#
#         # Wait for the employee status filter to be visible and clickable
#         employee_status_filter = WebDriverWait(browser, 10).until(
#             EC.element_to_be_clickable((By.XPATH, '//div[@data-test="employee-status-filterContent"]'))
#         )
#
#         # Find all the dropdown options under the employee status filter
#         status_options = employee_status_filter.find_elements(By.XPATH, './/div[contains(@class, "dropdownOption")]')
#
#         random_delay(1, 3)
#
#         for status_option in status_options:
#             # Hover over the element to make it visible and clickable
#             ActionChains(browser).move_to_element(status_option).perform()
#
#             # Wait for the element with 'data-test="benefit-rating"' to be visible
#             benefit_rating_element = WebDriverWait(browser, 10).until(
#                 EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-test="benefit-rating"]'))
#             )
#
#             random_delay(1, 3)
#
#             # Click the status dropdown option
#             status_option.click()
#
#         # Assuming you want to deselect and move to the next, you need to click the location filter again
#         location_filter.click()


def scrapeInterviewPage(url):
    interview_titles, applications, interviews, questions = ([] for _ in range(4))

    browser.get(url)
    print(browser.current_url)

    source = browser.page_source
    soup = BeautifulSoup(source, 'html.parser')

    # Find the main div containing the interviews list
    interview_list = soup.find('div', {'data-test': 'InterviewList'})

    # If interview_list is found, process each 'row' within it
    if interview_list:
        rows = interview_list.find_all('div', class_='row')

        for row in rows:
            # Fetch the title
            title_tag = row.find('h2', {'data-test': True})
            title = title_tag.get_text(strip=True) if title_tag else None

            # Fetch the application details
            application_details_tag = row.find('div', {'data-test': True, 'class': 'mt'})
            application = application_details_tag.get_text(strip=True) if application_details_tag else None

            # Fetch the interview details
            strong_interview_tag = row.find('strong', string='Interview')
            if strong_interview_tag:
                interview_p = strong_interview_tag.find_next('p')  # Directly look for the next <p> tag
                interview = interview_p.get_text(strip=True) if interview_p else None
            else:
                interview = None

            # Fetch the interview questions
            interview_questions = None
            strong_questions_tag = row.find('strong', class_='d-block mb-xsm', string='Interview Questions')
            if strong_questions_tag:
                # Directly look for the next element that might contain the interview questions text
                interview_questions_tag = strong_questions_tag.find_next()
                if interview_questions_tag:
                    interview_questions = interview_questions_tag.get_text(strip=True)

            interview_titles.append(title)
            applications.append(application)
            interviews.append(interview)
            questions.append(interview_questions if interview_questions else 'Not Provided')

            # print(f"Title: {title}")
            # print(f"Application: {application}")
            # print(f"Interview: {interview}")
            # print(f"Interview Questions: {interview_questions if interview_questions else 'Not Provided'}\n")
    else:
        logging.info(f"No interview list found.")

    return interview_titles, applications, interviews, questions


def scrapeSalaryPage(url):
    browser.get(url)
    print(browser.current_url)

    source = browser.page_source
    soup = BeautifulSoup(source, 'html.parser')

    # Find all the rows with the specified class
    rows = soup.find_all('tr', class_='salarylist_table-row__ThC_D')

    titles, total_pays, bases, additionals = ([] for _ in range(4))

    for row in rows:
        # Find the job title, specifically looking for the 'a' element within the 'td' with 'data-testid' attribute 'jobTitle'
        job_title_tag = row.find('td', {'data-testid': 'jobTitle'}).find('a')
        job_title = job_title_tag.get_text(strip=True) if job_title_tag else None

        # Find the total compensation, specifically looking for the 'p' element with class 'salarylist_bold__J20df' within the 'td'
        total_comp_tag = row.find('td', {'data-testid': 'totalComp'}).find('p', class_='salarylist_bold__J20df')
        total_comp = total_comp_tag.get_text(strip=True) if total_comp_tag else None

        # Find base and additional compensation details separately
        additional_comp_tags = row.find('td', {'data-testid': 'totalComp'}).find_all('p',
                                                                                     class_='salarylist_sub-data__MsmA5')
        if additional_comp_tags:
            base, additional = additional_comp_tags[0].get_text(strip=True).split('|')
        else:
            base = additional = None  # default values

        # print(f"Job Title: {job_title}, Total Compensation: {total_comp}, Base: {base}, Additional: {additional}")

        titles.append(job_title)
        total_pays.append(total_comp)
        bases.append(base)
        additionals.append(additional)

    return titles, total_pays, bases, additionals


def regexFindRatings(text):
    # Regex pattern to find all specified ratings followed by an integer
    pattern = (
        r'"ratingWorkLifeBalance":(\d+)|'
        r'"ratingCultureAndValues":(\d+)|'
        r'"ratingDiversityAndInclusion":(\d+)|'
        r'"ratingSeniorLeadership":(\d+)|'
        r'"ratingCareerOpportunities":(\d+)|'
        r'"ratingCompensationAndBenefits":(\d+)'
    )

    # Search for the pattern and organize the results
    ratings = {
        'ratingWorkLifeBalance': [],
        'ratingCultureAndValues': [],
        'ratingDiversityAndInclusion': [],
        'ratingSeniorLeadership': [],
        'ratingCareerOpportunities': [],
        'ratingCompensationAndBenefits': []
    }

    for match in re.finditer(pattern, text):
        # match.groups() will contain None for non-matching groups,
        # so we check which one has a value and add it to the corresponding list.
        for i, value in enumerate(match.groups()):
            if value:
                # The index of the group corresponds to the order of the rating types in the pattern
                rating_type = list(ratings.keys())[i]
                ratings[rating_type].append(int(value))

    # Output the results
    # for rating_type, values in ratings.items():
    #     print(f"{rating_type}: {values}")

    return ratings


def regexFind(text):
    # Expanded regex pattern to include more ratings
    pattern = (
        r'"overallRating":(\d+(?:\.\d+)?)|'
        r'"reviewCount":(\d+)|'
        r'"recommendToFriendRating":(\d+(?:\.\d+)?)|'
        r'"ceoRating":(\d+(?:\.\d+)?)|'
        r'"businessOutlookRating":(\d+(?:\.\d+)?)|'
        r'"cultureAndValuesRating":(\d+(?:\.\d+)?)|'
        r'"diversityAndInclusionRating":(\d+(?:\.\d+)?)|'
        r'"careerOpportunitiesRating":(\d+(?:\.\d+)?)|'
        r'"workLifeBalanceRating":(\d+(?:\.\d+)?)|'
        r'"seniorManagementRating":(\d+(?:\.\d+)?)|'
        r'"compensationAndBenefitsRating":(\d+(?:\.\d+)?)'
    )

    # Search for the pattern
    matches = re.finditer(pattern, text)

    # Initialize variables to None for each rating
    ratings = {
        'overall_rating': None,
        'review_count': None,
        'recommend_to_friend_rating': None,
        'ceo_rating': None,
        'business_outlook_rating': None,
        'culture_and_values_rating': None,
        'diversity_and_inclusion_rating': None,
        'career_opportunities_rating': None,
        'work_life_balance_rating': None,
        'senior_management_rating': None,
        'compensation_and_benefits_rating': None
    }

    # Iterate over the matches and assign to the respective rating
    for match in matches:
        groups = match.groups()
        for index, rating in enumerate(ratings):
            if groups[index]:
                ratings[rating] = groups[index]

    # Output the results
    # for rating, value in ratings.items():
    #     print(f"{rating.replace('_', ' ').capitalize()}: {value}")

    return ratings


def scrapeReviewPage(url):
    # restart_driver()

    browser.get(url)
    print(browser.current_url)

    # Now, let's extract the script content that contains the window.appCache assignment
    # The exact details of this might depend on the structure of the HTML and the script tags
    script_content = browser.execute_script("""
        var scripts = document.getElementsByTagName('script');
        for (var i = 0; i < scripts.length; i++) {
            if (scripts[i].textContent.includes('window.appCache')) {
                return scripts[i].textContent;
            }
        }
        return '';
    """)

    # regexFind(script_content)
    ratings_dict = regexFindRatings(script_content)

    source = browser.page_source
    soup = BeautifulSoup(source, 'html.parser')

    # Locate all the top reviews
    top_reviews = soup.find_all(class_='review-details__review-details-module__topReview')

    ratings, titles, dates, employees, employee_details, locations, is_recommends, is_ceo_approvals, is_business_outlooks, pros, cons = processTopReview(
        top_reviews)

    # Create a combined dictionary for all data
    combined_data = {
        'ratings': ratings,
        'titles': titles,
        'dates': dates,
        'employees': employees,
        'employee_details': employee_details,
        'locations': locations,
        'is_recommends': is_recommends,
        'is_ceo_approvals': is_ceo_approvals,
        'is_business_outlooks': is_business_outlooks,
        'pros': pros,
        'cons': cons
    }
    # Add the ratings to the combined dictionary
    for rating_type, values in ratings_dict.items():
        combined_data[rating_type] = values

    return combined_data


def scrapePages(base_url, company, company_idx):
    restart_driver()
    try:
        # Write to csv
        # Prepare CSV file for writing

        SCRAPE_REVIEW = True
        SCRAPE_SALARY = True
        SCRAPE_INTERVIEW = True
        SCRAPE_BENEFIT = True
        SCRAPE_DIVERSITY = False

        logging.info("Scraping job started.")

        # ----------------------------------------------- Scrape Review pages -------------------------------------------------------
        if SCRAPE_REVIEW:
            total_review_pages = get_total_review_pages(base_url.format(1))
            if total_review_pages:
                num_pages = total_review_pages
            else:
                num_pages = DEFAULT_PAGE_NUMBER

            # num_pages = 3
            urls = [base_url.format(i) for i in range(1, num_pages + 1)]
            restart_threshold = random.randint(30,
                                               50)  # Randomly choose when to restart the driver between 30 and 50 URLs
            url_count = 0  # Initialize the URL counter

            with open(f'results/{company}/OverallReviews.csv', 'a', newline='', encoding='utf-8') as file:

                browser.get(urls[0])
                logging.info(f"Retrieving overall ratings for {company}")

                # Now, let's extract the script content that contains the window.appCache assignment
                # The exact details of this might depend on the structure of the HTML and the script tags
                script_content = browser.execute_script("""
                                        var scripts = document.getElementsByTagName('script');
                                        for (var i = 0; i < scripts.length; i++) {
                                            if (scripts[i].textContent.includes('window.appCache')) {
                                                return scripts[i].textContent;
                                            }
                                        }
                                        return '';
                                    """)

                ratings = regexFind(script_content)

                writer = csv.DictWriter(file, fieldnames=ratings.keys())

                # Write the header (the dictionary keys)
                writer.writeheader()

                # Write the dictionary as a single row
                writer.writerow(ratings)

            with open(f'results/{company}/reviews.csv', 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL, quotechar='"')

                # Write the header row to the CSV file
                writer.writerow(
                    ["Rating", "Title", "Date", "Employee", "EmployeeDetails", "Location", "Recommend", "CEO Approval",
                     "Business Outlook", "Pro", "Con", "ratingWorkLifeBalance", "ratingCultureAndValues",
                     "ratingDiversityAndInclusion",
                     "ratingSeniorLeadership", "ratingCareerOpportunities", "ratingCompensationAndBenefits"])

                for url in urls:
                    try:
                        logging.info(f"Scraping company review url {url}.")
                        combined_data = scrapeReviewPage(url)
                        url_count += 1
                        if url_count >= restart_threshold:
                            restart_driver()  # Restart the driver
                            restart_threshold = random.randint(30, 50)  # Reset the threshold for the next cycle
                            url_count = 0  # Reset the URL counter

                        # Get the length of the lists
                        headers = list(combined_data.keys())
                        num_entries = len(combined_data[headers[0]])  # Assumes all lists are the same length

                        # Write the list entries as rows
                        for i in range(num_entries):
                            row = [combined_data[key][i] if i < len(combined_data[key]) else '' for key in headers]
                            writer.writerow(row)

                        random_delay(5, 10)

                    except NoSuchElementException as e:
                        logging.error(f"An error occurred during scraping: {e}. Element not found. Skipping.")
                        pass
                    except TimeoutException as e:
                        logging.error(f"An error occurred during scraping: {e}. Page load timed out. Skipping.")
                        pass
                    except WebDriverException as e:
                        logging.error(f"An error occurred during scraping: {e}. WebDriver error. Skipping.")
                        pass
                    except Exception as e:
                        logging.error(
                            f"An error occurred during scraping: {e}. An unexpected error occurred. Skipping.")
                        pass

        # ----------------------------------------------- Scrape Salary pages -------------------------------------------------------
        if SCRAPE_SALARY:
            restart_driver()

            base_salary_urls = get_salary_url(company, company_idx)

            total_salary_pages = get_total_salary_pages(base_salary_urls.format(1))
            if total_salary_pages:
                num_pages = total_salary_pages
            else:
                num_pages = DEFAULT_PAGE_NUMBER

            # num_pages = 3
            salary_urls = [base_salary_urls.format(i) for i in range(1, num_pages + 1)]
            restart_threshold = random.randint(30,
                                               50)  # Randomly choose when to restart the driver between 30 and 50 URLs
            url_count = 0  # Initialize the URL counter

            with open(f'results/{company}/salaries.csv', 'a', newline='', encoding='utf-8') as file:
                salary_writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL, quotechar='"')

                # Write the header row to the CSV file
                salary_writer.writerow(["Job Title", "Total Pay", "Base", "Additional"])

                for url in salary_urls:
                    try:
                        logging.info(f"Scraping company salary url {url}.")
                        titles, total_pays, bases, additionals = scrapeSalaryPage(url)
                        url_count += 1
                        if url_count >= restart_threshold:
                            restart_driver()  # Restart the driver
                            restart_threshold = random.randint(30, 50)  # Reset the threshold for the next cycle
                            url_count = 0  # Reset the URL counter

                        for title, total_pay, base, additional in zip(titles, total_pays, bases, additionals):
                            salary_writer.writerow([title, total_pay, base, additional])

                        random_delay(5, 10)

                    except NoSuchElementException as e:
                        logging.error(f"An error occurred during scraping: {e}. Element not found. Skipping.")
                        pass
                    except TimeoutException as e:
                        logging.error(f"An error occurred during scraping: {e}. Page load timed out. Skipping.")
                        pass
                    except WebDriverException as e:
                        logging.error(f"An error occurred during scraping: {e}. WebDriver error. Skipping.")
                        pass
                    except Exception as e:
                        logging.error(
                            f"An error occurred during scraping: {e}. An unexpected error occurred. Skipping.")
                        pass

        # ----------------------------------------------- Scrape Interview pages -------------------------------------------------------
        if SCRAPE_INTERVIEW:
            restart_driver()

            base_interview_urls = get_interview_url(company, company_idx)
            total_interview_pages = get_total_interview_pages(base_interview_urls.format(1))
            if total_interview_pages:
                num_pages = total_interview_pages if total_interview_pages < 999 else 999  # Hard limit for interview pages
            else:
                num_pages = DEFAULT_PAGE_NUMBER

            # num_pages = 3
            interview_urls = [base_interview_urls.format(i) for i in range(1, num_pages + 1)]
            restart_threshold = random.randint(30,
                                               50)  # Randomly choose when to restart the driver between 30 and 50 URLs
            url_count = 0  # Initialize the URL counter

            with open(f'results/{company}/interviews.csv', 'a', newline='', encoding='utf-8') as file:
                interview_writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL, quotechar='"')

                interview_writer.writerow(["Interview Title", "Applicaton", "Interview", "Interview Question"])

                for url in interview_urls:
                    try:
                        logging.info(f"Scraping company interview url {url}.")
                        interview_titles, applications, interviews, questions = scrapeInterviewPage(url)
                        url_count += 1
                        if url_count >= restart_threshold:
                            restart_driver()  # Restart the driver
                            restart_threshold = random.randint(30, 50)  # Reset the threshold for the next cycle
                            url_count = 0  # Reset the URL counter

                        for interview_title, application, interview, question in zip(interview_titles, applications,
                                                                                     interviews, questions):
                            interview_writer.writerow([interview_title, application, interview, question])

                        random_delay(5, 10)

                    except NoSuchElementException as e:
                        logging.error(f"An error occurred during scraping: {e}. Element not found. Skipping.")
                        pass
                    except TimeoutException as e:
                        logging.error(f"An error occurred during scraping: {e}. Page load timed out. Skipping.")
                        pass
                    except WebDriverException as e:
                        logging.error(f"An error occurred during scraping: {e}. WebDriver error. Skipping.")
                        pass
                    except Exception as e:
                        logging.error(
                            f"An error occurred during scraping: {e}. An unexpected error occurred. Skipping.")
                        pass

        # ----------------------------------------------- Scrape Benefits pages -------------------------------------------------------
        if SCRAPE_BENEFIT:
            restart_driver()

            benefits_urls = get_benefit_url(company, company_idx)
            with open(f'results/{company}/benefits.csv', 'a', newline='', encoding='utf-8') as file:
                benefits_writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL, quotechar='"')

                benefits_writer.writerow(["Employment Status", "Rating", "Number of Ratings"])

                for url in benefits_urls:
                    try:
                        logging.info(f"Scraping company benefits url {url}.")
                        status, star_rating, number_of_ratings = scrapeBenefitPage(url)
                        benefits_writer.writerow([status, star_rating, number_of_ratings])

                        random_delay(1, 3)
                    except NoSuchElementException as e:
                        logging.error(f"An error occurred during scraping: {e}. Element not found. Skipping.")
                        pass
                    except TimeoutException as e:
                        logging.error(f"An error occurred during scraping: {e}. Page load timed out. Skipping.")
                        pass
                    except WebDriverException as e:
                        logging.error(f"An error occurred during scraping: {e}. WebDriver error. Skipping.")
                        pass
                    except Exception as e:
                        logging.error(
                            f"An error occurred during scraping: {e}. An unexpected error occurred. Skipping.")
                        pass

                    restart_driver()

        # ----------------------------------------------- Scrape Diversity pages -------------------------------------------------------
        if SCRAPE_DIVERSITY:
            restart_driver()

            diversity_url = get_diversity_url(company, company_idx)
            with open(f'results/{company}/diversity.csv', 'a', newline='', encoding='utf-8') as file:
                diversity_writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL, quotechar='"')

                diversity_writer.writerow(["Rating Title", "Overall Rating", "Recommend to a Friend", "Approve of CEO",
                                           "Positive Business Outlook", "Career Opportunities",
                                           "Compensation and Benefits",
                                           "Culture & Values", "Diversity & Inclusion", "Senior Management",
                                           "Work/Life Balance"])

                try:
                    logging.info(f"Scraping company diversity url {diversity_url}.")
                    results = scrapeDiversityPage(diversity_url)

                    for result in results:
                        diversity_writer.writerow(result)

                    random_delay(1, 3)
                except NoSuchElementException as e:
                    logging.error(f"An error occurred during scraping: {e}. Element not found. Skipping.")
                    pass
                except TimeoutException as e:
                    logging.error(f"An error occurred during scraping: {e}. Page load timed out. Skipping.")
                    pass
                except WebDriverException as e:
                    logging.error(f"An error occurred during scraping: {e}. WebDriver error. Skipping.")
                    pass
                except Exception as e:
                    logging.error(
                        f"An error occurred during scraping: {e}. An unexpected error occurred. Skipping.")
                    pass

    except Exception as e:
        logging.error(f"An unkown error occurred during scraping: {e}. Skipping.")
        pass
    finally:
        restart_driver()


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
    options.add_argument('--headless')
    options.add_argument('window-size=1920x1080')
    # options.add_argument(
    #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        # "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
        # ... add as many user agents as you need
    ]
    # Randomly choose a user agent from the list
    random_user_agent = random.choice(user_agents)
    options.add_argument(f'user-agent={random_user_agent}')

    browser = webdriver.Chrome(options=options)
    browser.maximize_window()


def get_company_list():
    file_path = 'company_info.csv'
    second_column_data = []

    names = []
    codes = []

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row
        for row in reader:
            if row:  # Check if row is not empty
                second_column_data.append(row[1])  # Assuming the second column is at index 1

    # Regular expression pattern
    pattern = r'Working-at-(.*?)-EI_I(E\d+)'

    for url in second_column_data:
        # Perform regex search
        match = re.search(pattern, url)

        if match:
            company_name = match.group(1)
            code = match.group(2)
            print("Company Name:", company_name)
            print("Code:", code)
            names.append(company_name)
            codes.append(code)
        else:
            print("No match found")

    return names, codes


def scrapeGlassdoor():
    # base_url = "https://www.glassdoor.com.au/Reviews/Apple-Reviews-E1138_P{}.htm?filter.iso3Language=eng"

    # browser = None
    restart_driver()

    names, codes = get_company_list()

    for name, code in zip(names, codes):
        result_path = f"results/{name}"
        # Check if the directory exists
        if not os.path.exists(result_path):
            # Create the directory
            os.makedirs(result_path)
            print(f"Directory '{result_path}' created.")
        else:
            print(f"Directory '{result_path}' already exists.")

        base_url = f"https://www.glassdoor.com/Reviews/{name}-Reviews-{code}_P{{}}.htm?filter.iso3Language=eng"

        scrapePages(base_url, name, code)

    browser.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    start_time = time.time()

    scrapeGlassdoor()

    end_time = time.time()

    elapsed_time = end_time - start_time
    print(f"The scraper took {elapsed_time} seconds to run.")
