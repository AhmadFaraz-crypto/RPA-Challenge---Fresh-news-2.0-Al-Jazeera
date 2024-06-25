import re
from dataclasses import dataclass, asdict

from al_jazeera_news.utils import convert_string_to_datetime

amount_re_pattern = r'\$[\d,]+(?:\.\d+)?|\b\d+\s*dollars?\b|\b\d+\s*USD\b'


@dataclass
class News:
    title: str
    image: str
    date: str = None
    does_contain_amount: bool = False
    description: str = ''
    word_count: int = 0

    def __post_init__(self):
        """
        Post-initialization processing to convert the date string to a formatted date string
        and to check if the title or description contains a monetary amount.
        """
        self.date = convert_string_to_datetime(self.date).strftime('%Y/%m/%d') if self.date else None
        self.does_contain_amount = self._does_contain_amount()

    def _does_contain_amount(self) -> bool:
        """
        Checks if the title or description contains a monetary amount.

        Returns:
            bool: True if a monetary amount is found, False otherwise.
        """
        match = re.findall(amount_re_pattern, self.description + self.title)
        return bool(match)

    def set_word_count(self, search_input: str):
        """
      Sets the word count of a specific search term in the title and description combined.

      Args:
          search_input (str): The search term to count in the article's content.
      """
        self.word_count = (self.description + self.title).count(search_input)

    @staticmethod
    def get_as_dict(news_list: list['News']) -> list[dict]:
        """
          Converts a list of News objects into a list of dictionaries.

          Args:
              news_list (list[News]): A list of News objects.

          Returns:
              list[dict]: A list of dictionaries representing the News objects.
          """
        return [asdict(news) for news in news_list]
