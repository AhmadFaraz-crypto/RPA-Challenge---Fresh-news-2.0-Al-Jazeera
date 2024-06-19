import datetime
import re

import shutil
import time

from RPA.HTTP import HTTP
from dateutil.relativedelta import relativedelta
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from RPA.Archive import Archive

from al_jazeera_news.constants import SITE_URL, NEWS_DATA
from al_jazeera_news.locators import AlJazeeraLocators
from utils.check_date import check_date, convert_string_to_datetime

from service_logger import  logger


class AlJazeera:
    def __init__(self, search_input='', month=0):
        self.browser = Selenium()
        self.excel = Files()
        self.data = []
        self.search_input = search_input
        self.month_range = datetime.datetime.now() - relativedelta(months=month)
        self.is_amount = False
        self.downloader = HTTP()
        self.lib = Archive()

    def open_website(self):
        """
            Navigates to the given URL
        """
        self.browser.open_available_browser(maximized=True)
        self.browser.go_to(SITE_URL)
        logger.info("Page navigate successfully.")

    def search_news(self):
        """
            Trigger search field from the headers
            Fill search field from the given phrase
        """
        self.browser.element_should_be_visible(locator=AlJazeeraLocators.SEARCH_READER_TEXT,
                                               message="Click here to search")
        self.browser.click_button(locator=AlJazeeraLocators.SEARCH_TRIGGER)
        self.browser.input_text(AlJazeeraLocators.SEARCH_INPUT, self.search_input)
        self.browser.element_should_be_visible(locator=AlJazeeraLocators.SEARCH_BUTTON, message="Search")
        self.browser.click_button(locator=AlJazeeraLocators.SEARCH_BUTTON)
        self.browser.wait_until_page_contains_element('//button[@id="onetrust-accept-btn-handler"]')
        self.browser.click_element_when_visible('//button[@id="onetrust-accept-btn-handler"]')
        self.browser.wait_until_page_contains_element('//select[@id="search-sort-option"]')
        self.browser.select_from_list_by_value('//select[@id="search-sort-option"]', 'date')
        self.click_show_more_until_available()

    def click_show_more_until_available(self):
        """
            Open up all the news with clicking show more until is exist no more, its set to 10 at mx by the website
        """
        self.browser.wait_until_page_contains_element(AlJazeeraLocators.SHOW_MORE_BUTTON, timeout=30)
        tries = 10
        while tries:
            try:
                self.browser.execute_javascript("window.scrollTo(0, document.body.scrollHeight);")
                self.browser.click_element_when_visible(AlJazeeraLocators.SHOW_MORE_BUTTON)
                self.browser.wait_until_element_is_visible(AlJazeeraLocators.SHOW_MORE_BUTTON)
                tries -= 1
            except AssertionError:
                break

    def get_article_data(self):
        """
            Get news data from news lists.
        """
        time.sleep(4)
        articles = self.browser.find_elements(locator=AlJazeeraLocators.CLICKABLE_CARD)
        for article in articles:
            try:
                news_obj = {}
                title = article.find_element(By.CLASS_NAME, AlJazeeraLocators.TITLE).text
                news_obj['title'] = title
                logger.info(f'Getting news with title {title}')
                is_description = article.find_element(By.CLASS_NAME, AlJazeeraLocators.DESCRIPTION).is_displayed()
                if is_description:
                    description = article.find_elements(By.CLASS_NAME, AlJazeeraLocators.DESCRIPTION)
                    news_obj['description'] = description[0].text.split('...', 1)[-1]
                else:
                    news_obj['description'] = ''
                try:
                    is_date = article.find_element(By.CLASS_NAME, AlJazeeraLocators.DATE).is_displayed()
                except NoSuchElementException:
                    is_date = False
                if is_date:
                    if not check_date(article.find_element(By.CLASS_NAME, AlJazeeraLocators.DATE).text, self.month_range):
                        return None
                    news_obj['date'] = convert_string_to_datetime(
                        article.find_element(By.CLASS_NAME, AlJazeeraLocators.DATE).text
                    )
                else:
                    news_obj['date'] = ""
                is_image = article.find_element(By.CLASS_NAME, AlJazeeraLocators.IMAGE).is_displayed()
                if is_image:
                    image = article.find_elements(By.CLASS_NAME, AlJazeeraLocators.IMAGE)
                    self.downloader.download(image[0].get_attribute('src'), f'images/{news_obj["title"][:20]}.jpg')
                    news_obj['image'] = f'images/{news_obj["title"][:10]}.jpg'
                amount_re_pattern = r'\$[\d,]+(?:\.\d+)?|\b\d+\s*dollars?\b|\b\d+\s*USD\b'
                match = re.findall(amount_re_pattern, news_obj['description'] + news_obj['title'])
                news_obj['does_contain_amount'] = str(bool(match))
                news_obj['Word Count'] = (news_obj['description'] + news_obj['title']).count(self.search_input)
                self.data.append(news_obj)
            except Exception as e:
                logger.warning(f'Skipped news due to error {e}')

    def create_report(self):
        """
            Create and save excel file and images zip
        """
        self.excel.create_workbook(path=NEWS_DATA, fmt="xlsx")
        self.excel.append_rows_to_worksheet(self.data, header=True)
        self.excel.save_workbook()
        self.lib.archive_folder_with_tar('./images', 'output/images.tar', recursive=True)
        shutil.rmtree("images")
        logger.info("Excel file created successfully.")
