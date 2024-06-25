import datetime

import shutil

from RPA.HTTP import HTTP
from dateutil.relativedelta import relativedelta
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from RPA.Archive import Archive

from al_jazeera_news.constants import SITE_URL, NEWS_EXCEL_FILE
from al_jazeera_news.exceptions import AljazeeraNewsDateReachedException
from al_jazeera_news.locators import AlJazeeraLocators
from al_jazeera_news.models import News
from al_jazeera_news.utils import is_date_in_given_range

from utils.service_logger import logger

amount_re_pattern = r'\$[\d,]+(?:\.\d+)?|\b\d+\s*dollars?\b|\b\d+\s*USD\b'


class AlJazeera:
    def __init__(self, search_input: str = '', month: int = 0):
        """
        Initializes an instance of AlJazeera with optional search input and month range.

        Args:
            search_input (str, optional): Search input string for queries (default is '').
            month (int, optional): Number of months back from current date to consider (default is 0).
        """
        self.browser = Selenium()
        self.excel = Files()
        self.news_list: list[News] = []
        self.search_input = search_input
        self.month_range = datetime.datetime.now() - relativedelta(months=month)
        self.downloader = HTTP()
        self.article_counter = 0
        self.archive_lib = Archive()

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
        self.browser.element_should_be_visible(
            locator=AlJazeeraLocators.SEARCH_READER_TEXT,
            message="Click here to search"
        )
        self.browser.click_button(locator=AlJazeeraLocators.SEARCH_TRIGGER)
        self.browser.input_text(AlJazeeraLocators.SEARCH_INPUT, self.search_input)
        self.browser.element_should_be_visible(locator=AlJazeeraLocators.SEARCH_BUTTON, message="Search")
        self.browser.click_button(locator=AlJazeeraLocators.SEARCH_BUTTON)
        logger.info('Sorting news with date.')
        self.browser.wait_until_page_contains_element(AlJazeeraLocators.COOKIES_ACCEPT)
        self.browser.click_element_when_visible(AlJazeeraLocators.COOKIES_ACCEPT)
        self.browser.wait_until_page_contains_element(AlJazeeraLocators.SORT)
        self.browser.select_from_list_by_value(AlJazeeraLocators.SORT, 'date')

    def process_news_articles(self, articles: list):
        """
       Processes a list of news articles, extracting and processing relevant data for each article.

       Args:
           articles (list): A list of web elements representing news articles.

       This method performs the following steps for each article:
           1. Logs the extraction of news data.
           2. Extracts the title and image URL of the article.
           3. Downloads the article image and saves it locally.
           4. Extracts the article description and publication date, if available.
           5. Checks if the publication date is within the specified date range.
           6. Creates a News object with the extracted data.
           7. Sets the word count of the specified search input in the article's content.
           8. Appends the News object to the news list.

       If the publication date is not found or is not within the specified range, the article is skipped.
           """
        for index, article in enumerate(articles):
            logger.info('Extracting news data')

            title = article.find_element(By.CLASS_NAME, AlJazeeraLocators.TITLE).text
            image = article.find_element(By.CLASS_NAME, AlJazeeraLocators.IMAGE)
            file_name = f"image_{index}"
            self.downloader.download(image.get_attribute('src'), f'images/{file_name}.jpg')
            image = f'images/{file_name}.jpg'
            description = ''
            date = None

            try:
                date = article.find_element(By.CLASS_NAME, AlJazeeraLocators.DATE).text
                if not is_date_in_given_range(date, self.month_range):
                    return None
            except NoSuchElementException:
                logger.warning('[process_news_articles] Date Element not found! Date will be set as Null')

            # Extracting description
            if article.find_element(By.CLASS_NAME, AlJazeeraLocators.DESCRIPTION).is_displayed():
                description_element = article.find_element(By.CLASS_NAME, AlJazeeraLocators.DESCRIPTION)
                description = description_element.text.split('...', 1)[-1]

            # news object
            news = News(
                title=title,
                image=image,
                date=date,
                description=description
            )

            # setting word count
            news.set_word_count(self.search_input)
            logger.info(f'NEWS: {news}')
            self.news_list.append(news)

    def get_articles_data(self) -> None:
        """
            Get news data from news lists.
        """
        try:
            self.browser.wait_until_element_is_visible(AlJazeeraLocators.MAIN_CONTENT_AREA, 5)
        except AssertionError as e:
            logger.error(f"[get_articles_data] Unable to find search results, {e}")

        articles_per_page = 10
        try:
            articles = self.browser.find_elements(locator=AlJazeeraLocators.CLICKABLE_CARD)
            self.process_news_articles(articles[self.article_counter:self.article_counter + articles_per_page])
            self.article_counter += articles_per_page
            try:
                self.browser.execute_javascript("window.scrollTo(0, document.body.scrollHeight);")
                self.browser.click_element_when_visible(AlJazeeraLocators.SHOW_MORE_BUTTON)
                self.browser.wait_until_element_is_visible(AlJazeeraLocators.SHOW_MORE_BUTTON)
                self.get_articles_data()
            except AssertionError as e:
                logger.info("Could not find the show more button.")
        except AljazeeraNewsDateReachedException:
            ...

    def create_report(self):
        """
            Create and save excel file and images zip
        """
        self.excel.create_workbook(path=NEWS_EXCEL_FILE, fmt="xlsx")
        self.excel.append_rows_to_worksheet(News.get_as_dict(self.news_list), header=True)
        self.excel.save_workbook()
        self.archive_lib.archive_folder_with_tar('./images', 'output/images.tar', recursive=True)
        shutil.rmtree("images")
        logger.info("Excel file created successfully.")
