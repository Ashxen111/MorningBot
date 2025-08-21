from datetime import datetime, timedelta
import random


def get_time_info():
    now = datetime.now()
    day_period = "день" if 6 <= now.hour < 18 else "вечер"
    weekday = [
        "понедельник",
        "вторник",
        "среда",
        "четверг",
        "пятница",
        "суббота",
        "воскресенье",
    ][now.weekday()]
    return f"Сегодня {now.year} год, {now.day} {now.strftime('%B')}, {weekday}.\nВремя: {now.hour}:{now.minute:02d} — {day_period}."


def parse_hhmm(s: str):
    try:
        h, m = map(int, s.split(":"))
        return 0 <= h < 24 and 0 <= m < 60
    except:
        return False


def next_datetime_from_hhmm(s: str):
    h, m = map(int, s.split(":"))
    now = datetime.now()
    dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if dt <= now:
        dt += timedelta(days=1)
    return dt


def get_random_quote():
    try:
        with open("quotes.txt", "r", encoding="utf-8") as f:
            quotes = [line.strip() for line in f if line.strip()]
        return random.choice(quotes)
    except:
        return "Размышляй о великом и тайном."
