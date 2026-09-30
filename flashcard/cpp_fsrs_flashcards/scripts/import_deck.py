from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT.parents[1] / "cpp_flashcards_00_to_12.md"
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage import read_deck_document, write_deck_document


@dataclass(frozen=True)
class ImportedCard:
    card_id: str
    topic: str
    question: str
    answer: str
    source: str


def parse_deck(source_path: Path) -> list[ImportedCard]:
    text = source_path.read_text(encoding="utf-8")
    section_pattern = re.compile(
        r"^## (?P<section>\d{2}) — (?P<topic>.+?)\n"
        r"(?P<section_body>.*?)(?=^## (?:\d{2} —|Mixed Final Drill)|\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    card_pattern = re.compile(
        r"<details>\s*\n"
        r"<summary><strong>(?P<id>\d{2}\.\d+) — (?P<question>.*?)</strong></summary>\s*\n"
        r"(?P<answer>.*?)\s*\n</details>",
        flags=re.DOTALL,
    )

    cards: list[ImportedCard] = []
    for section_match in section_pattern.finditer(text):
        section = section_match.group("section")
        topic = section_match.group("topic").strip()
        body = section_match.group("section_body")
        source_match = re.search(r"\[`([^`]+\.md)`\]", body)
        source = source_match.group(1) if source_match else source_path.name

        for card_match in card_pattern.finditer(body):
            card_id = card_match.group("id")
            if not card_id.startswith(f"{section}."):
                raise ValueError(f"Card {card_id} appears under section {section}")
            cards.append(
                ImportedCard(
                    card_id=card_id,
                    topic=topic,
                    question=card_match.group("question").strip(),
                    answer=card_match.group("answer").strip(),
                    source=source,
                )
            )

    ids = [card.card_id for card in cards]
    duplicates = sorted({card_id for card_id in ids if ids.count(card_id) > 1})
    if duplicates:
        raise ValueError(f"Duplicate card IDs: {', '.join(duplicates)}")
    return cards


def write_cards(cards: list[ImportedCard], deck_path: Path) -> None:
    if deck_path.exists():
        document = read_deck_document(deck_path)
    else:
        document = {
            "format_version": 1,
            "id": "cpp-interview",
            "title": "C++ Interview Flashcards",
            "description": "Modern C++ and embedded software interview preparation.",
            "study_settings": {
                "desired_retention": 0.90,
                "new_cards_per_day": 12,
                "timezone_name": "America/Los_Angeles",
                "maximum_interval_days": 3650,
            },
            "assets": {},
        }
    document["cards"] = [
        {
            "id": card.card_id,
            "topic": card.topic,
            "question": card.question,
            "answer": card.answer,
            "source": card.source,
        }
        for card in cards
    ]
    write_deck_document(deck_path, document)


def main() -> int:
    source_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source_path.exists():
        print(f"Deck not found: {source_path}", file=sys.stderr)
        return 1

    cards = parse_deck(source_path)
    if len(cards) != 171:
        print(f"Expected 171 cards, parsed {len(cards)}", file=sys.stderr)
        return 1

    deck_path = PROJECT_ROOT / "decks" / "cpp-interview.deck.yaml"
    write_cards(cards, deck_path)
    print(f"Imported {len(cards)} cards into {deck_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
