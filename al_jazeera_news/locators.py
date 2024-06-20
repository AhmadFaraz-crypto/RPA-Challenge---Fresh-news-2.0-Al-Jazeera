"""
    Defines Locators used for interacting with the Al Jazeera website.
"""


class AlJazeeraLocators:
    """
        Locators related to search functionality.
    """

    SEARCH_READER_TEXT = "class:screen-reader-text"
    SEARCH_TRIGGER = "class:site-header__search-trigger .no-styles-button"
    SEARCH_INPUT = "class:search-bar__input"
    SEARCH_BUTTON = "class:css-sp7gd"

    """
        Locators related to search results.
    """

    SEARCH_RESULTS = "class:search-results__no-results"
    SEARCH_RESULTS_SUMMARY = "class:search-summary__options-title"

    GC_DATE = "class:gc__date__date .screen-reader-text"
    SHOW_MORE_BUTTON = "//button[contains(@class, 'show-more-button')]"
    CLICKABLE_CARD = "class:u-clickable-card"
    TITLE = "u-clickable-card__link span"
    DESCRIPTION = "gc__body-wrap .gc__excerpt p"
    DATE = "gc__date__date .screen-reader-text"
    IMAGE = "gc__image-wrap img"
    SORT = '//select[@id="search-sort-option"]'
    COOKIES_ACCEPT = '//button[@id="onetrust-accept-btn-handler"]'
