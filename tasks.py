import os

from RPA.Robocorp.WorkItems import WorkItems

from al_jazeera_news.al_jazeera import AlJazeera


def news_robot_spare_bin_python():
    local_process = os.environ.get("RC_WORKSPACE_ID") is None
    if not local_process:
        work_items = WorkItems()
        work_items.get_input_work_item()
        work_item = work_items.get_work_item_variables()
        variables = work_item.get("variables", dict())
        search_input = variables.get('search_phrase', 'israel war iran')
        months = variables.get('months', 1)
    else:
        search_input = "US elections"
        months = 1
    news_content = AlJazeera(search_input, months)
    news_content.open_website()


news_robot_spare_bin_python()