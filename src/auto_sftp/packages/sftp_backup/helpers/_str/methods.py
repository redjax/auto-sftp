import pendulum


def get_year_month_str() -> str:
    _year: int = pendulum.now().year
    _month: int = pendulum.now().month

    _month: str = f"{_month:02d}"

    return f"{_year}/{_month}"
