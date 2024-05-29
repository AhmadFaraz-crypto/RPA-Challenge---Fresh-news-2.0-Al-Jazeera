import dateutil.parser


def check_date(date, month_range):
    if "on" in date.lower():
        date = date.lower().split('on')[-1]
    elif "updated" in date.lower():
        date = date.lower().split('updated')[-1]
    elif "update" in date.lower():
        date = date.lower().split('update')[-1]
    date_time_object = dateutil.parser.parse(date)
    if date_time_object < month_range:
        return False
    return True
