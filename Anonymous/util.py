import secrets
from datetime import datetime


def fetch_ip_address(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_username(user):
    if user == 'Anonymous':
        return f'Anon-{secrets.token_urlsafe(15)}'
    if user == 'Consultant':
        return f'Consult-{secrets.token_urlsafe(12)}'


def new_day(day):
    date_ = datetime.now().date()
    if (date_ - day).days > 0:
        return True
    return False
