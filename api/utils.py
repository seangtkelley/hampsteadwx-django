import datetime

def get_month_name(num):
    return datetime.date(1900, num, 1).strftime('%B')


def create_alert(color, body):
    return { 'color': color, 'body': body }

def add_alert(payload, color, body):
    alert = create_alert(color, body)
    if 'alerts' in payload:
        payload['alerts'].append(alert)
    else:
        payload['alerts'] = [ alert ]

    return payload