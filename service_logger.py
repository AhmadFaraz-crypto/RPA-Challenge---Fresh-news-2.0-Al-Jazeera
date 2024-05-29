import logging.handlers

from al_jazeera_news.constants import LOG_LOCATION, LOG_FILENAME


def __setup_logger():
    # logfile settings
    LOG_FORMAT = "%(asctime)s [%(levelname)-5.5s] %(message)s"

    progress_logger = logging.getLogger(LOG_FILENAME)
    progress_logger.setLevel(logging.DEBUG)
    rotating_file_handler = logging.handlers.RotatingFileHandler(LOG_LOCATION,
                                                               maxBytes=(1048576 * 5), backupCount=7)
    # log file handler
    log_formatter = logging.Formatter(LOG_FORMAT)
    rotating_file_handler.setFormatter(log_formatter)
    progress_logger.addHandler(rotating_file_handler)
    rotating_file_handler.setLevel(logging.INFO)

    # console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    progress_logger.addHandler(console_handler)
    console_handler.setLevel(logging.INFO)
    return progress_logger


service_logger = __setup_logger()
