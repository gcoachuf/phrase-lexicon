"""Simplified SM-2 spaced repetition scheduler."""

from datetime import date, timedelta


def today() -> date:
    return date.today()


def initial_card_state() -> dict:
    return {
        "interval": 0,
        "ease": 2.5,
        "due": today().isoformat(),
        "reps": 0,
        "lapses": 0,
    }


def review_card(card: dict, rating: int) -> dict:
    """
    Rating: 0=Again, 1=Hard, 2=Good, 3=Easy
    Returns updated scheduling fields.
    """
    interval = card.get("interval", 0)
    ease = card.get("ease", 2.5)
    reps = card.get("reps", 0)
    lapses = card.get("lapses", 0)

    if rating == 0:
        lapses += 1
        reps = 0
        interval = 0
        ease = max(1.3, ease - 0.2)
        due = today() + timedelta(days=1)
    elif rating == 1:
        reps += 1
        interval = max(1, round(interval * 1.2)) if interval else 1
        ease = max(1.3, ease - 0.15)
        due = today() + timedelta(days=interval)
    elif rating == 2:
        reps += 1
        if interval == 0:
            interval = 1
        elif interval == 1:
            interval = 3
        else:
            interval = round(interval * ease)
        due = today() + timedelta(days=interval)
    else:
        reps += 1
        ease += 0.15
        if interval == 0:
            interval = 4
        else:
            interval = round(interval * ease * 1.3)
        due = today() + timedelta(days=interval)

    return {
        "interval": interval,
        "ease": round(ease, 2),
        "due": due.isoformat(),
        "reps": reps,
        "lapses": lapses,
    }
