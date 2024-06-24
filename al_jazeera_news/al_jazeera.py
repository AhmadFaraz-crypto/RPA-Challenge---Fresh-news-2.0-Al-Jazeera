import datetime
import re

import shutil
from typing import List

from RPA.HTTP import HTTP
from dateutil.relativedelta import relativedelta
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from RPA.Archive import Archive

from al_jazeera_news.constants import SITE_URL, NEWS_DATA
from al_jazeera_news.exceptions import AljazeeraNewsDateReachedException
from al_jazeera_news.locators import AlJazeeraLocators
from al_jazeera_news.utils import check_date, convert_string_to_datetime

from utils.service_logger import logger

amount_re_pattern = r'\$[\d,]+(?:\.\d+)?|\b\d+\s*dollars?\b|\b\d+\s*USD\b'


class AlJazeera:
    def __init__(self, search_input='', month=0):
        """
        Initializes an instance of AlJazeera with optional search input and month range.

        Args:
            search_input (str, optional): Search input string for queries (default is '').
            month (int, optional): Number of months back from current date to consider (default is 0).
        """
        self.browser = Selenium()
        self.excel = Files()
        self.data = []
        self.search_input = search_input
        self.month_range = datetime.datetime.now() - relativedelta(months=month)
        self.downloader = HTTP()
        self.article_counter = 0
        self.lib = Archive()

    def open_website(self) -> None:
        """
            Opens a web browser and navigates to a specified URL.

            This method initializes a web browser, maximizes its window, and then navigates
            to the predefined SITE_URL constant.

            Returns:
                None
        """
        self.browser.open_available_browser(maximized=True)
        self.browser.go_to(SITE_URL)
        logger.info("Page navigate successfully.")

    def search_news(self) -> None:
        """
            Performs a news search and sorts results by date on the Al Jazeera website.

            This method triggers the search functionality on the website header, fills in the search field
            with a specified search phrase, clicks the search button, and then sorts
            the search results by date.

            Returns:
                None
        """
        logger.info('Searching news with search input.')
        self.browser.element_should_be_visible(locator=AlJazeeraLocators.SEARCH_READER_TEXT,
                                               message="Click here to search")
        self.browser.click_button(locator=AlJazeeraLocators.SEARCH_TRIGGER)
        self.browser.input_text(AlJazeeraLocators.SEARCH_INPUT, self.search_input)
        self.browser.element_should_be_visible(locator=AlJazeeraLocators.SEARCH_BUTTON, message="Search")
        self.browser.click_button(locator=AlJazeeraLocators.SEARCH_BUTTON)
        logger.info('Sorting news with date.')
        self.browser.wait_until_page_contains_element(AlJazeeraLocators.COOKIES_ACCEPT)
        self.browser.click_element_when_visible(AlJazeeraLocators.COOKIES_ACCEPT)
        self.browser.wait_until_page_contains_element(AlJazeeraLocators.SORT)
        self.browser.select_from_list_by_value(AlJazeeraLocators.SORT, 'date')

    def process_news_articles(self, articles: List) -> None:
        """
            Processes a list of news articles from a webpage, extracting relevant information and storing.
        """
        for index, article in enumerate(articles):
            news_obj = {}
            title = article.find_element(By.CLASS_NAME, AlJazeeraLocators.TITLE).text
            news_obj['Title'] = title
            logger.info(f'Getting news with title {title}')
            is_description = article.find_element(By.CLASS_NAME, AlJazeeraLocators.DESCRIPTION).is_displayed()
            if is_description:
                description = article.find_element(By.CLASS_NAME, AlJazeeraLocators.DESCRIPTION)
                news_obj['Description'] = description.text.split('...', 1)[-1]
            else:
                news_obj['Description'] = ''
            try:
                if not check_date(article.find_element(By.CLASS_NAME, AlJazeeraLocators.DATE).text, self.month_range):
                    return None
                news_obj['Date'] = convert_string_to_datetime(
                    article.find_element(By.CLASS_NAME, AlJazeeraLocators.DATE).text
                ).strftime('%Y/%m/%d')
            except NoSuchElementException:
                news_obj['Date'] = "Null"
            image = article.find_element(By.CLASS_NAME, AlJazeeraLocators.IMAGE)
            file_name = f"image_{index}"
            self.downloader.download(image.get_attribute('src'), f'images/{file_name}.jpg')
            news_obj['Image'] = f'images/{file_name}.jpg'
            match = re.findall(amount_re_pattern, news_obj['Description'] + news_obj['Title'])
            news_obj['Does Contain Amount'] = str(bool(match))
            news_obj['Word Count'] = (news_obj['Description'] + news_obj['Title']).count(self.search_input)
            self.data.append(news_obj)

    def get_article_data(self) -> None:
        """
            Get news data from news lists.
        """
        articles_per_page = 10
        try:
            articles = self.browser.find_elements(locator=AlJazeeraLocators.CLICKABLE_CARD)
            self.process_news_articles(articles[self.article_counter:self.article_counter + articles_per_page])
            self.article_counter += articles_per_page
            try:
                self.browser.execute_javascript("window.scrollTo(0, document.body.scrollHeight);")
                self.browser.click_element_when_visible(AlJazeeraLocators.SHOW_MORE_BUTTON)
                self.browser.wait_until_element_is_visible(AlJazeeraLocators.SHOW_MORE_BUTTON)
                self.get_article_data()
            except AssertionError as e:
                logger.info("Could not find the show more button.")
        except AljazeeraNewsDateReachedException:
            ...

    def create_report(self) -> None:
        """
            Create and save excel file and images zip
        """
        self.excel.create_workbook(path=NEWS_DATA, fmt="xlsx")
        self.excel.append_rows_to_worksheet(self.data, header=True)
        self.excel.save_workbook()
        self.lib.archive_folder_with_tar('./images', 'output/images.tar', recursive=True)
        shutil.rmtree("images")
        logger.info("Excel file created successfully.")
