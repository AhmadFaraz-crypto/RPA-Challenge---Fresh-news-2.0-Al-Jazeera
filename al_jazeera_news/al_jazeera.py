import datetime
import re

import os
import shutil

from RPA.HTTP import HTTP
from dateutil.relativedelta import relativedelta
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
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
        self.image_urls = []
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
        self.browser.wait_until_page_contains_element('//button[@class="show-more-button grid-full-width"]')
        not_results_found = self.browser.is_element_visible(locator=AlJazeeraLocators.SEARCH_RESULTS)
        is_results_visible = self.browser.is_element_visible(locator=AlJazeeraLocators.SEARCH_RESULTS_SUMMARY)

        if not_results_found:
            logger.error("Sorry, not results found.")
            self.browser.close_browser()
        elif is_results_visible:
            self.browser.element_should_be_visible(locator=AlJazeeraLocators.SEARCH_RESULTS_SUMMARY, message="Sort by")
            logger.info("Articles list display successfully.")
            self.check_date_validity()
        else:
            logger.error("Something went wrong.")
            self.browser.close_browser()

    def check_date_validity(self):
        date = self.browser.find_elements(locator=AlJazeeraLocators.GC_DATE)[0].text
        if not check_date(date, self.month_range):
            return None
        while True:
            if self.browser.does_page_contain_element(locator=AlJazeeraLocators.SHOW_MORE_BUTTON):
                self.browser.execute_javascript("window.scrollTo(0, document.body.scrollHeight);")
                self.browser.find_element(locator=AlJazeeraLocators.SHOW_MORE_BUTTON).click()
                date = self.browser.find_elements(locator=AlJazeeraLocators.GC_DATE)[-1].text
                if not check_date(date, self.month_range):
                    self.get_article_data()
                    break
            else:
                break

    def get_article_data(self):
        """
            Get text data from a WebElement based on a locator.
        """
        self.browser.wait_until_page_contains_element('//button[@class="show-more-button grid-full-width"]')
        self.browser.scroll_element_into_view('//button[@class="show-more-button grid-full-width"]')
        self.browser.wait_until_page_contains_element(AlJazeeraLocators.CLICKABLE_CARD, timeout=30, limit=20)
        articles = self.browser.find_elements(locator=AlJazeeraLocators.CLICKABLE_CARD)
        for article in articles:
            article_text = ""
            is_title = article.find_element(By.CLASS_NAME, AlJazeeraLocators.TITLE).is_displayed()
            if is_title:
                title = article.find_element(By.CLASS_NAME, AlJazeeraLocators.TITLE).text
                article_text += title
                self.title.append(title)
            is_description = article.find_element(By.CLASS_NAME, AlJazeeraLocators.DESCRIPTION).is_displayed()
            if is_description:
                description = article.find_elements(By.CLASS_NAME, AlJazeeraLocators.DESCRIPTION)
                article_text += description[0].text
                self.description.append(description[0].text)
                logger.info("Description found")
            else:
                logger.error("Description not found")
            try:
                is_date = article.find_element(By.CLASS_NAME, AlJazeeraLocators.DATE).is_displayed()
            except NoSuchElementException:
                is_date = False
            if is_date:
                logger.info(f'Date found')
                self.date.append(article.find_element(By.CLASS_NAME, AlJazeeraLocators.DATE).text)
            else:
                logger.error("Date not found")
            is_image = article.find_element(By.CLASS_NAME, AlJazeeraLocators.IMAGE).is_displayed()
            if is_image:
                image = article.find_elements(By.CLASS_NAME, AlJazeeraLocators.IMAGE)
                self.picture.append(image[0].get_attribute('alt'))
                self.image_urls.append(image[0].get_attribute('src'))
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
        for index, image in enumerate(self.image_urls):
            downloader.download(image, f'images/image-{index}.jpg')
            logger.info(f"Image downloaded successfully. {image}")
        if len(self.image_urls):
            lib.archive_folder_with_tar('./images', 'output/images.tar', recursive=True)
            logger.info(f"Images zip created successfully.")
            shutil.rmtree("images")
            logger.info(f"Images directory removed successfully.")