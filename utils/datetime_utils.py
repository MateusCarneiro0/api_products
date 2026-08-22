import datetime


def calculate_now():
    return datetime.datetime.now(datetime.timezone.utc)


def calculate_date_of_now(**kwargs):
    return calculate_now() + datetime.timedelta(**kwargs)
