import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import os
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
import backoff
import logging

import pdfkit
import PyPDF2
from io import BytesIO
from typing import Optional

from app.utils.logger import LoggerConfig

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager
import base64
import time
import asyncio

###COOKIE TEST###
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

import pyautogui

logger = LoggerConfig().get_logger(__name__)

LISTING_OUTPUT_PATH = os.getenv("LISTING_OUTPUT_PATH")
# @logger.log_execution
# def some_function():
#     with logger.operation_logger("important operation"):
#         # Do work
#         pass

class JobScraperService:
    ALLOWED_DRIVERS = {"safari", "chrome"}
    """Service class for scraping and processing job listing webpage content"""

    def __init__(self, driver: str):
        """Initialize beautiful soup headers and set OpenAI API key"""
        self.logger = LoggerConfig().get_logger(__name__)
        load_dotenv()
        self.data_dir = LISTING_OUTPUT_PATH
        if driver not in self.ALLOWED_DRIVERS:
            raise ValueError(f"Invalid driver: {driver}")
        self.driver = driver

    def setup_chrome_driver(self, driver_dir: str) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        chrome_version = os.getenv("CHROME_VERSION")
        cache = DriverCacheManager(driver_dir)
        driver_manager = ChromeDriverManager(
            driver_version=chrome_version,
            cache_manager=cache,
        )
        return webdriver.Chrome(service=Service(driver_manager.install()),
                                        options=options
                                        )

    def setup_safari_driver(self) -> webdriver.Safari:
        return webdriver.Safari()

    def generate_pdf_chrome(self, driver:webdriver.Chrome, pdf_path:str):
        pdf_options = {
            "landscape": False,
            "printBackground": True,
            "scale": 1.0,
            "paperWidth": 8.27,  # A4 width in inches
            "paperHeight": 11.69,  # A4 height in inches
            "marginTop": 0.4,
            "marginBottom": 0.4,
            "marginLeft": 0.4,
            "marginRight": 0.4,
            "preferCSSPageSize": True
        }

        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", pdf_options)
        with open(pdf_path, "wb") as file:
            file.write(base64.b64decode(pdf_data["data"])
        )

    def generate_pdf_safari(self, driver: webdriver.Safari, pdf_path: str):
        driver.execute_script('window.print();')
        time.sleep(2)  # Wait for print dialog to open
        pyautogui.hotkey('command', 'p')  # Open print dialog
        time.sleep(2)  # Wait for print dialog to open
        pyautogui.hotkey('command', 's')  # Save as PDF
        time.sleep(2)  # Wait for save dialog to open
        pyautogui.typewrite(pdf_path)  # Type the file path
        pyautogui.press('enter')  # Confirm save

    def url_to_pdf(self, url: str, source_type: str) -> Optional[str]:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        driver_dir = os.path.join(current_dir, "drivers")#install chrome driver within the repo
        os.makedirs(driver_dir, exist_ok=True)

        if self.driver == "chrome":
            web_driver = self.setup_chrome_driver(driver_dir)
        elif self.driver == "safari":
            web_driver = self.setup_safari_driver()
        else:
            raise ValueError(f"Invalid driver: {self.driver}")

        try:
            # Navigate to the URL
            web_driver.get(url)
            ################COOKIE TEST STARTS################
            # Common cookie button selectors # TODO: takes a long time... better way
            cookie_selectors = [
                "button[id*='cookie-accept']",
                "button[id*='accept-cookies']",
                "[aria-label*='Accept cookies']",
                "button[class*='cookie']",
                "#onetrust-accept-btn-handler",
                "[data-cookiebanner='accept_button']",
                # "button[contains(text(), 'Allow')]",
                "[aria-label*='Allow']",
                "button.allow-button",
                "#allow-cookies",
                "ppc-content[key='gdpr-allowCookiesText']",
                "#consent_agree",  # Direct ID selector
                "button.consent-agree",  # Class-based selector
                "button[data-action*='acceptCookies']",  # Attribute-based selector
                "button[type='button'][data-bs-dismiss='modal']",
                "#survale-survey-dialog-close"
            ]

            # Try each selector
            wait = WebDriverWait(web_driver, 2)
            for selector in cookie_selectors:
                try:
                    cookie_button = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    self.logger.info("Accepted cookies")
                    break
                except TimeoutException:
                    continue

            # Wait for the page to fully render
            time.sleep(3)
            ################COOKIE TEST ENDS################

            # Save the rendered page as a PDF
            # Use a Chrome DevTools command for generating the PDF
            pdf_path = f"{self.data_dir}/{source_type}.pdf"
            pdf_path = os.path.abspath(pdf_path)

            if self.driver == "chrome":
                self.generate_pdf_chrome(web_driver, pdf_path)
            elif self.driver == "safari":
                self.generate_pdf_safari(web_driver, pdf_path)

            self.logger.info(f"PDF generated successfully at: {pdf_path} using {self.driver} \
                                driver")
            return pdf_path

        except Exception as e:
            self.logger.error(f"Error occurred: {e}")
        finally:
            web_driver.quit()

    @LoggerConfig().log_execution
    async def execute(self, url: str, source_type) -> dict:
        """
        Main execution method for scraping job listing webpage content

        Args:
            url (str): Target webpage to scrape

        Returns:
            dict: Extracted job details from the webpage
        """
        job_path = await asyncio.to_thread(self.url_to_pdf, url, source_type)
        return job_path

if __name__== "__main__":
    # this is wrong since JobScraperService is now async
    url = "https://careers.wbd.com/global/en/job/WAMEGLOBALR000087600EXTERNALENGLOBAL/Senior-Data-Scientist?utm_source=linkedin&utm_medium=phenom-feeds"
    source_type = "test"
    scraper = JobScraperService(driver = "chrome")
    test_path = scraper.execute(url, source_type)
