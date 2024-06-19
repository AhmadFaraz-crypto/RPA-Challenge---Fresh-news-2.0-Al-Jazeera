import os

from RPA.Robocorp.WorkItems import WorkItems

from al_jazeera_news.al_jazeera import AlJazeera
from service_logger import logger

local_process = os.environ.get("RC_WORKSPACE_ID") is None
if not local_process:
    work_items = WorkItems()
    work_items.get_input_work_item()
    work_item = work_items.get_work_item_variables()
    variables = work_item.get("variables", dict())
    search_input = variables.get('search_phrase', 'Temperature in india')
    months = variables.get('months', 1)
else:
    search_input = "Temperature in india"
    months = 2

if not os.path.exists('output'):
    os.mkdir('output')

if not os.path.exists('images'):
    os.mkdir('images')

def news_scrapper():
    try:
        logger.info("Starting Process.")
        news_content = AlJazeera(search_input, months)
        logger.info("Opening website.")
        news_content.open_website()
        logger.info("Searching news.")
        news_content.search_news()
        logger.info("Reading News.")
        news_content.get_article_data()
        logger.info("Creating report.")
        news_content.create_report()
    except Exception as e:
        logger.error(f"An error occurred in automation task: {e}", exc_info=True)
    finally:
        logger.info("Process finished.")


if __name__ == '__main__':
    news_scrapper()
