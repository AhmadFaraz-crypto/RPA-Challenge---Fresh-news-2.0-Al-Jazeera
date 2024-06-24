import dateutil.parser


def check_date(date, month_range):
    """
    Check if a given date is within a specified month range.

    Args:
        date (str): The date string to be checked, in a format supported by `convert_string_to_datetime`.
        month_range (datetime.datetime): The upper bound datetime object representing the end of the month range.

    Returns:
        bool: True if the date is within the specified month range, False otherwise.

    """
    date_time_object = convert_string_to_datetime(date)
    if date_time_object < month_range:
        return False
    return True


def convert_string_to_datetime(date):
    """
    Converts a string representation of a date/time into a datetime object.

    Args:
        date (str): A string containing the date/time information.

    Returns:
        datetime.datetime: A datetime object representing the parsed date/time.

    """
    if "on" in date.lower():
        date = date.lower().split('on')[-1]
    elif "updated" in date.lower():
        date = date.lower().split('updated')[-1]
    elif "update" in date.lower():
        date = date.lower().split('update')[-1]

    return dateutil.parser.parse(date)

