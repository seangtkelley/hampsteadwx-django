import datetime

def get_month_name(num):
    return datetime.date(1900, num, 1).strftime('%B')