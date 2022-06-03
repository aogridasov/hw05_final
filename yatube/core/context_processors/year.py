import datetime


CURRENT_DATE = datetime.date.today()


def year(request):
    """Добавляет переменную с текущим годом."""
    return {'year': CURRENT_DATE.year}
