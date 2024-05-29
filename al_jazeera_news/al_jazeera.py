import datetime
import re

import os
import shutil
from RPA.HTTP import HTTP
from dateutil.relativedelta import relativedelta
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from RPA.Archive import Archive

from al_jazeera_news.constants import SITE_URL, NEWS_DATA
from al_jazeera_news.locators import AlJazeeraLocators
from utils.check_date import check_date

from service_logger import service_logger as logger

class AlJazeera:
    def __init__(self, search_input='', month=0):
        self.browser = Selenium()
        self.excel = Files()
        self.title = []
        self.description = []
        self.date = []
        self.picture = []
        self.image_url = []
        self.word_count = []
        self.does_contain_amount = []
        self.search_input = search_input
        self.title_search_phrase_count = 0
        self.description_search_phrase_count = 0
        self.month_range = datetime.datetime.now() - relativedelta(months=month)
        self.is_amount = False

    def open_website(self):
        """
            Navigates to the given URL
        """
        self.browser.open_available_browser(maximized=True)
        self.browser.go_to(SITE_URL)
        logger.info("Page navigate successfully.")
        self.open_search_field()

    def open_search_field(self):
        """
            Trigger search field from the headers
            Fill search field from the given phrase
        """
        self.browser.element_should_be_visible(locator=AlJazeeraLocators.SEARCH_READER_TEXT, message="Click here to search")
        self.browser.click_button(locator=AlJazeeraLocators.SEARCH_TRIGGER)
        self.browser.input_text(AlJazeeraLocators.SEARCH_INPUT, self.search_input)
        self.browser.element_should_be_visible(locator=AlJazeeraLocators.SEARCH_BUTTON, message="Search")
        self.browser.click_button(locator=AlJazeeraLocators.SEARCH_BUTTON)
        logger.info("Search goes successfully.")
        self.should_visible_article_list()

    def should_visible_article_list(self):
        """
            check search results found or not
            if results not found, error will raise and browser will be close
        """
        self.browser.set_selenium_implicit_wait(datetime.timedelta(seconds=5))
        not_results_found = self.browser.is_element_visible(locator=AlJazeeraLocators.SEARCH_RESULTS)
        is_results_visible = self.browser.is_element_visible(locator=AlJazeeraLocators.SEARCH_RESULTS_SUMMARY)

        if not_results_found:
            logger.error("Sorry, not results found.")
            self.browser.close_browser()
        elif is_results_visible:
            self.browser.element_should_be_visible(locator=AlJazeeraLocators.SEARCH_RESULTS_SUMMARY, message="Sort by")
            logger.info("Articles list display successfully.")
            self.get_article_data()
        else:
            logger.error("Something went wrong.")
            self.browser.close_browser()

    def get_article_data(self):
        """
            Get text data from a WebElement based on a locator.
        """
        date = self.browser.find_elements(locator=AlJazeeraLocators.GC_DATE)[0].text
        if not check_date(date, self.month_range):
            return None
        while True:
            self.browser.set_selenium_implicit_wait(datetime.timedelta(seconds=3))
            if self.browser.does_page_contain_element(locator=AlJazeeraLocators.SHOW_MORE_BUTTON):
                self.browser.execute_javascript("window.scrollTo(0, document.body.scrollHeight);")
                self.browser.find_element(locator=AlJazeeraLocators.SHOW_MORE_BUTTON).click()
                date = self.browser.find_elements(locator=AlJazeeraLocators.GC_DATE)[-1].text
                if not check_date(date, self.month_range):
                    break
            else:
                break

        articles = self.browser.find_elements(locator=AlJazeeraLocators.CLICKABLE_CARD)
        for article in articles:
            article_text = ""
            try:
                title = article.find_element(By.CLASS_NAME, AlJazeeraLocators.TITLE).text
                article_text += title
                self.title.append(title)
                is_description = article.find_elements(By.CLASS_NAME, AlJazeeraLocators.DESCRIPTION)
                if is_description:
                    article_text += is_description[0].text
                    self.description.append(is_description[0].text)
                    logger.info("Description found")
                else:
                    logger.error("Description not found")
                is_date = article.find_elements(By.CLASS_NAME, AlJazeeraLocators.DATE)
                if is_date:
                    logger.info(f'Date found')
                    self.date.append(article.find_element(By.CLASS_NAME, AlJazeeraLocators.DATE).text)
                else:
                    logger.error("Date not found")

                is_image = article.find_elements(By.CLASS_NAME, AlJazeeraLocators.IMAGE)

                if is_image:
                    self.picture.append(is_image[0].get_attribute('alt'))
                    self.image_url.append(is_image[0].get_attribute('src'))
            except StaleElementReferenceException:
                logger.error("Element not found.")
            contain_amount = False
            try:
                amount_re_pattern = r'\$[\d,]+(?:\.\d+)?|\b\d+\s*dollars?\b|\b\d+\s*USD\b'
                match = re.findall(amount_re_pattern, article_text)
                contain_amount = bool(match)
            except Exception as e:
                logger.error(f"Failed to check amount in text: {str(e)}")
                contain_amount = False
            self.does_contain_amount.append(str(contain_amount))
        self.create_and_save_excel_file()

    def create_and_save_excel_file(self):
        """
            Create and save excel file
        """
        self.excel.create_workbook(path=NEWS_DATA, fmt="xlsx")
        worksheet_data = {
            "Title": self.title,
            "Description": self.description,
            "Date": self.date,
            "Picture": self.picture,
            "Title and description search phrase count": self.word_count,
            "Is does contain amount": self.does_contain_amount
        }
        self.excel.append_rows_to_worksheet(worksheet_data, header=True)
        self.excel.save_workbook()
        logger.info("Excel file created successfully.")
        self.download_image()

    def download_image(self):
        """
            Download article image with image text
        """
        os.mkdir("images")
        logger.info(f"Images directory created successfully.")
        downloader = HTTP()
        lib = Archive()
        for index, image in enumerate(self.image_url):
            downloader.download(image, f'images/image-{index}.jpg')
            logger.info(f"Image downloaded successfully. {image}")
        lib.archive_folder_with_tar('./images', 'output/images.tar', recursive=True)
        logger.info(f"Images zip created successfully.")
        shutil.rmtree("images")
        logger.info(f"Images directory removed successfully.")