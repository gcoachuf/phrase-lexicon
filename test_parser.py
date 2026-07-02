"""Quick parser checks for the cloze card format."""

from parser import parse_cloze_block, parse_cloze_cards

EXAMPLE = """---
EN_DE
Front: to contribute to the well-being of others: zum Wohl anderer _____
Back: beitragen

DE_EN
Front: zum Wohl anderer beitragen: to _____ to the well-being of others
Back: contribute

---"""

if __name__ == "__main__":
    cards = parse_cloze_cards(EXAMPLE)
    assert len(cards) == 2
    en_de = next(c for c in cards if c["direction"] == "en_de")
    de_en = next(c for c in cards if c["direction"] == "de_en")
    assert "_____" in en_de["front"]
    assert en_de["back"] == "beitragen"
    assert de_en["back"] == "contribute"
    print("ok", cards)
