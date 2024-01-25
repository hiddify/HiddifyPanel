from datetime import datetime


def date_to_json(d):
    return d.strftime("%Y-%m-%d") if d else None


def json_to_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return date_str


def time_to_json(d):

    return d.strftime("%Y-%m-%d %H:%M:%S") if d else None


def json_to_time(time_str):
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except:
        return time_str
