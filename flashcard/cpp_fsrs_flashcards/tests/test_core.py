from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fsrs import Rating

from src.content import MERMAID_PATTERN, _plain_speech_text, _validate_public_url
from src.storage import (
    CONFIG,
    ProgressRepository,
    create_deck,
    export_deck,
    import_deck,
    list_decks,
    load_deck_cards,
    load_embedded_asset,
    migrate_legacy_progress,
    save_card,
    save_uploaded_image,
)
from src.study import build_scheduler, choose_next_card, new_fsrs_card


def cpp_deck():
    return next(deck for deck in list_decks(CONFIG.decks_directory) if deck.deck_id == "cpp-interview")


class DeckTests(unittest.TestCase):
    def test_cpp_deck_has_unique_171_cards(self) -> None:
        cards = load_deck_cards(cpp_deck())
        self.assertEqual(171, len(cards))
        self.assertEqual(171, len({card.card_id for card in cards}))
        self.assertEqual("00.1", cards[0].card_id)
        self.assertEqual("12.18", cards[-1].card_id)

    def test_create_save_export_and_import_deck(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            root = Path(directory) / "decks"
            deck = create_deck(root, "Systems Design", "Architecture practice")
            save_card(
                deck,
                card_id="card-0001",
                topic="Caching",
                question="What is cache invalidation?",
                answer="Removing or refreshing stale cached data.",
                tags=["systems", "cache"],
                links=["https://example.com"],
            )
            self.assertEqual(1, len(load_deck_cards(deck)))
            self.assertEqual([deck.path], list(root.glob("*.deck.yaml")))
            self.assertEqual([], [path for path in root.iterdir() if path.is_dir()])

            asset_uri = save_uploaded_image(deck, "card-0001", "diagram.png", b"png-data")
            self.assertEqual("asset://diagram.png", asset_uri)
            self.assertEqual(("image/png", b"png-data"), load_embedded_asset(deck, "card-0001", "diagram.png"))

            now = datetime(2026, 9, 30, 17, 0, tzinfo=timezone.utc)
            repository = ProgressRepository(deck)
            state = repository.introduce(
                "card-0001", new_fsrs_card(deck.deck_id, "card-0001", now), now
            )
            updated, log = build_scheduler(deck, CONFIG).review_card(
                state.fsrs_card, Rating.Good, review_datetime=now
            )
            repository.record_review("card-0001", updated, log, 900)

            imported = import_deck(root, export_deck(deck))
            self.assertNotEqual(deck.deck_id, imported.deck_id)
            self.assertEqual(1, len(load_deck_cards(imported)))
            self.assertEqual(1, ProgressRepository(imported).review_count())
            self.assertEqual(
                ("image/png", b"png-data"),
                load_embedded_asset(imported, "card-0001", "diagram.png"),
            )

    def test_rich_content_is_detected_and_made_speech_friendly(self) -> None:
        content = "See [RAII](https://example.com).\n```mermaid\nflowchart LR\nA --> B\n```"
        match = MERMAID_PATTERN.search(content)
        self.assertIsNotNone(match)
        self.assertIn("flowchart LR", match.group("diagram"))
        self.assertEqual("See RAII. diagram omitted", _plain_speech_text(content))

    def test_website_preview_rejects_local_network_targets(self) -> None:
        with self.assertRaisesRegex(ValueError, "Private and local"):
            _validate_public_url("http://127.0.0.1/private")


class ProgressTests(unittest.TestCase):
    @staticmethod
    def _deck(directory: str, *, new_cards_per_day: int = 12):
        deck = create_deck(
            Path(directory) / "decks",
            "Progress test",
            new_cards_per_day=new_cards_per_day,
        )
        for number in range(1, 3):
            save_card(
                deck,
                card_id=f"card-{number:04d}",
                topic="Testing",
                question=f"Question {number}",
                answer=f"Answer {number}",
            )
        return deck

    def test_review_is_persisted_and_due_card_wins(self) -> None:
        now = datetime(2026, 9, 30, 17, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            deck = self._deck(directory)
            cards = load_deck_cards(deck)
            repository = ProgressRepository(deck)
            first = cards[0]
            repository.introduce(
                first.card_id,
                new_fsrs_card(deck.deck_id, first.card_id, now),
                now,
            )

            selected = choose_next_card(cards, repository, deck, CONFIG, now)
            self.assertIsNotNone(selected)
            self.assertEqual(first.card_id, selected.card.card_id)
            self.assertEqual("New", selected.kind)

            scheduler = build_scheduler(deck, CONFIG)
            state = repository.get(first.card_id)
            self.assertIsNotNone(state)
            updated, log = scheduler.review_card(
                state.fsrs_card,
                Rating.Good,
                review_datetime=now,
            )
            repository.record_review(first.card_id, updated, log, 1500)
            self.assertEqual(1, repository.review_count())
            self.assertEqual(updated.due, repository.get(first.card_id).due)

            repository.delete_deck_progress()
            self.assertEqual(0, repository.introduced_count())
            self.assertEqual(0, repository.review_count())
            self.assertIsNone(repository.get(first.card_id))

    def test_daily_new_card_limit(self) -> None:
        now = datetime(2026, 9, 30, 17, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            deck = self._deck(directory, new_cards_per_day=1)
            cards = load_deck_cards(deck)
            repository = ProgressRepository(deck)
            repository.introduce(
                cards[0].card_id,
                new_fsrs_card(deck.deck_id, cards[0].card_id, now),
                now,
            )
            scheduler = build_scheduler(deck, CONFIG)
            state = repository.get(cards[0].card_id)
            updated, log = scheduler.review_card(
                state.fsrs_card,
                Rating.Good,
                review_datetime=now,
            )
            repository.record_review(cards[0].card_id, updated, log, 500)
            later = now + timedelta(seconds=1)
            self.assertIsNone(choose_next_card(cards, repository, deck, CONFIG, later))

    def test_legacy_database_is_migrated_into_deck_yaml(self) -> None:
        now = datetime(2026, 9, 30, 17, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            deck = self._deck(directory)
            card = load_deck_cards(deck)[0]
            fsrs_card = new_fsrs_card(deck.deck_id, card.card_id, now)
            scheduler = build_scheduler(deck, CONFIG)
            updated, log = scheduler.review_card(fsrs_card, Rating.Good, review_datetime=now)
            database_path = Path(directory) / "progress.db"
            with sqlite3.connect(database_path) as connection:
                connection.executescript(
                    """
                    CREATE TABLE card_progress (
                        deck_id TEXT, card_id TEXT, fsrs_state TEXT, introduced_at TEXT,
                        last_review TEXT, due TEXT
                    );
                    CREATE TABLE reviews (
                        id INTEGER PRIMARY KEY, deck_id TEXT, card_id TEXT, reviewed_at TEXT,
                        rating INTEGER, review_log TEXT, scheduled_due TEXT,
                        review_duration_ms INTEGER
                    );
                    """
                )
                connection.execute(
                    "INSERT INTO card_progress VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        deck.deck_id,
                        card.card_id,
                        updated.to_json(),
                        now.isoformat(),
                        now.isoformat(),
                        updated.due.isoformat(),
                    ),
                )
                connection.execute(
                    "INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        1,
                        deck.deck_id,
                        card.card_id,
                        now.isoformat(),
                        int(Rating.Good),
                        log.to_json(),
                        updated.due.isoformat(),
                        1200,
                    ),
                )
            connection.close()

            self.assertEqual((1, 1), migrate_legacy_progress(database_path, [deck]))
            self.assertFalse(database_path.exists())
            repository = ProgressRepository(deck)
            self.assertEqual(1, repository.introduced_count())
            self.assertEqual(1, repository.review_count())
            self.assertEqual(updated.due, repository.get(card.card_id).due)


if __name__ == "__main__":
    unittest.main()
