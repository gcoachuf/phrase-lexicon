"""Parse flashcards from the Deutsch Google Doc export."""

import re
import urllib.request

DOC_ID = "1TX2Qd17AJ9nQ_A3QUtNSNbQ5WEqt4hfFVoaAUD_ifCw"
EXPORT_URL = f"https://docs.google.com/document/d/{DOC_ID}/export?format=txt"

ENGLISH_LINE = re.compile(
    r"^(to |a |an |the |no |slow |social |free |fuel |perception|please )",
    re.I,
)


def fetch_doc(url: str = EXPORT_URL) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_phrase_lexicon(text: str) -> list[dict]:
    if "Phrase Lexicon" not in text:
        return []

    section = text.split("Phrase Lexicon", 1)[1]
    lines = [ln.strip() for ln in section.splitlines() if ln.strip()]

    cards = []
    i = 0
    while i < len(lines) - 1:
        front, back = lines[i], lines[i + 1]
        if ENGLISH_LINE.match(front) or "/" in front:
            cards.append(
                {
                    "english": front,
                    "german": back,
                    "deck": "phrase_lexicon",
                    "source": "phrase_lexicon",
                }
            )
            i += 2
        else:
            i += 1
    return cards


def parse_gwod_cards(text: str) -> list[dict]:
    cards = []
    for match in re.finditer(
        r"Today's GWoD:\s*(.+?)\s*\n(?:.*?\n){0,80}?^WU:\s*(.+)$",
        text,
        re.MULTILINE,
    ):
        word = re.sub(r"\s*\([^)]+\)\s*$", "", match.group(1)).strip()
        meaning = match.group(2).strip()
        if word and meaning:
            cards.append(
                {
                    "english": meaning,
                    "german": word,
                    "deck": "gwod",
                    "source": "gwod",
                }
            )
    return cards


def parse_all(text: str | None = None) -> list[dict]:
    if text is None:
        text = fetch_doc()
    seen: set[tuple[str, str]] = set()
    cards: list[dict] = []
    for card in parse_phrase_lexicon(text) + parse_gwod_cards(text):
        key = (card["english"], card["german"])
        if key not in seen:
            seen.add(key)
            cards.append(card)
    return cards
