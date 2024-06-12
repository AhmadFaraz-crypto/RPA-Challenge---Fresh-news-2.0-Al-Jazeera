import os

from RPA.Robocorp.WorkItems import WorkItems

from al_jazeera_news.al_jazeera import AlJazeera
from service_logger import service_logger as logger


def news_robot_spare_bin_python():
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
        months = 1
    try:
        news_content = AlJazeera(search_input, months)
        news_content.open_website()
        news_content.open_search_field()
        news_content.should_visible_article_list()
        news_content.create_and_save_excel_file()
        news_content.download_image()
    except Exception as e:
        logger.error(f"An error occurred in automation task: {e}", exc_info=True)


if __name__ == '__main__':
    news_robot_spare_bin_python()
