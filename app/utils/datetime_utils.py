import datetime


def calculate_now():
    return datetime.datetime.now(datetime.timezone.utc)


def calculate_date_of_now(**kwargs):
    return calculate_now() + datetime.timedelta(**kwargs)


def calculate_seconds_of_now_future_date(future_date):
    diference = datetime.datetime.fromisoformat(future_date) - calculate_now()
    return diference.total_seconds()
