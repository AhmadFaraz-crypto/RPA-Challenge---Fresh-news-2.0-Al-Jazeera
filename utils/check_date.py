import dateutil.parser


def check_date(date, month_range):
    date_time_object = convert_string_to_datetime(date)
    if date_time_object < month_range:
        return False
    return True


def convert_string_to_datetime(date):
    if "on" in date.lower():
        date = date.lower().split('on')[-1]
    elif "updated" in date.lower():
        date = date.lower().split('updated')[-1]
    elif "update" in date.lower():
        date = date.lower().split('update')[-1]
    return dateutil.parser.parse(date)
