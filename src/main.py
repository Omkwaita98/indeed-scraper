from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium_proxy import add_proxy
from selenium_proxy.schemas import Proxy

from apify import Actor


async def main() -> None:
    async with Actor:
        # Retrieve the Actor input, and use default values if not provided
        actor_input = await Actor.get_input() or {}
        start_urls = actor_input.get("start_urls")

        # Exit if no start URLs are provided
        if not start_urls:
            Actor.log.info("No start URLs specified in actor input, exiting...")
            await Actor.exit()

        # Extract the URL of the target page
        url = start_urls[0]["url"]

        # Configure Chrome to run:
        # 1. In headless mode
        # 2. On a large window to avoid responsive rendering
        # 3. With a real-world User-Agent
        # 4. Improve stability in containerized environments
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless")  # Enable headless mode for non-GUI execution
        chrome_options.add_argument("--window-size=1920,1080")  # Set a fixed resolution to avoid layout shifts
        chrome_options.add_argument("--no-sandbox")  # Bypass OS security restrictions (useful in Docker)
        chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent crashes in low-memory environments

        # Set a real-world User-Agent
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")

        # Configure residential proxy settings
        proxy = {
            "host": "proxy.apify.com",
            "port": "8000",
            "username": "groups-RESIDENTIAL",
            "password": "<YOUR_PROXY_PASSWORD>"
        }
        add_proxy(chrome_options, proxy=Proxy(**proxy))

        # Initialize a WebDriver instance to control Chrome
        driver = webdriver.Chrome(options=chrome_options)

        # Visit the target page
        driver.get(url)

        # Where to store the scraped data
        job_postings = []

        # Select all job posting card HTML elements on the page
        job_posting_card_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid=\\"
        slider_container\\"]")

        # Iterate over them and extract data from each job posting
        for job_posting_card_element in job_posting_card_elements:
            # Scraping logic

            job_title_element = job_posting_card_element.find_element(By.CSS_SELECTOR, "[id^=\\"
            jobTitle\\"]")
            job_title = job_title_element.text

            try:
                company_element = job_posting_card_element.find_element(By.CSS_SELECTOR, "[data-testid=\\"
                company - name\\"]")
                company = company_element.text
            except NoSuchElementException:
                company = None

            try:
                location_element = job_posting_card_element.find_element(By.CSS_SELECTOR, "[data-testid=\\"
                text - location\\"]")
                location = location_element.text
            except NoSuchElementException:
                location = None

            try:
                salary_element = job_posting_card_element.find_element(By.CSS_SELECTOR, "[data-testid=\\"
                attribute_snippet_testid\\"]")
                salary_range = salary_element.text
            except NoSuchElementException:
                salary_range = None

            try:
                description_element = job_posting_card_element.find_element(By.CSS_SELECTOR, "[data-testid=\\"
                jobsnippet_footer\\"]")
                job_description = description_element.text
            except NoSuchElementException:
                job_description = None

            # Populate an object with the scraped data
            job_posting = {
                "title": job_title,
                "company": company,
                "location": location,
                "salary_range": salary_range,
                "description": job_description
            }
            # Add it to the list of scraped job postings
            job_postings.append(job_posting)

        # Close the Selenium Chrome driver and release its resources
        driver.quit()

        # Register the scraped data to the Actor
        await Actor.push_data(job_postings)
