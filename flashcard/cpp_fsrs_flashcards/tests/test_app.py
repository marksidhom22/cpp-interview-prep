from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from app import app
from src.storage import ProgressRepository, list_decks, load_deck_cards, read_deck_document


class FlaskAppTests(unittest.TestCase):
    def test_study_navigation_deck_management_and_card_creation(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            temporary_root = Path(directory)
            legacy_database_path = temporary_root / "legacy-progress.db"
            decks_directory = temporary_root / "decks"
            decks_directory.mkdir()
            shutil.copy2(
                project_root / "decks" / "cpp-interview.deck.yaml",
                decks_directory / "cpp-interview.deck.yaml",
            )
            copied_deck = list_decks(decks_directory)[0]
            ProgressRepository(copied_deck).delete_deck_progress()
            previous_database = os.environ.get("FLASHCARDS_DB_PATH")
            previous_decks = os.environ.get("FLASHCARDS_DECKS_DIR")
            os.environ["FLASHCARDS_DB_PATH"] = str(legacy_database_path)
            os.environ["FLASHCARDS_DECKS_DIR"] = str(decks_directory)
            app.config.update(TESTING=True, SECRET_KEY="test-secret")
            try:
                client = app.test_client()
                response = client.get("/")
                self.assertEqual(200, response.status_code)
                self.assertIn(b"Reveal answer", response.data)

                response = client.post("/study", data={"action": "reveal"}, follow_redirects=True)
                self.assertEqual(200, response.status_code)
                self.assertIn(b"Rate what you recalled", response.data)
                client.post("/study", data={"action": "rate", "rating": "Good"}, follow_redirects=True)
                document = read_deck_document(copied_deck.path)
                self.assertEqual(1, len(document["study_progress"]["reviews"]))

                for view in ("Cards", "Statistics", "Study"):
                    response = client.get("/", query_string={"view": view})
                    self.assertEqual(200, response.status_code)

                response = client.get("/", query_string={"view": "Decks"})
                self.assertIn(b"Reset study progress", response.data)
                client.post(
                    "/decks",
                    data={"action": "reset", "deck_id": copied_deck.deck_id, "confirmation": "RESET"},
                    follow_redirects=True,
                )
                document = read_deck_document(copied_deck.path)
                self.assertEqual((0, 0), (
                    len(document["study_progress"]["card_states"]),
                    len(document["study_progress"]["reviews"]),
                ))

                client.post(
                    "/decks",
                    data={"action": "create", "title": "Algorithms Practice", "description": ""},
                    follow_redirects=True,
                )
                created_path = decks_directory / "algorithms-practice.deck.yaml"
                self.assertTrue(created_path.is_file())
                created_deck = next(deck for deck in list_decks(decks_directory) if deck.deck_id == "algorithms-practice")
                response = client.post(
                    "/cards",
                    data={
                        "action": "add", "card_id": "algo-001", "topic": "Sorting",
                        "question": "What does stable sorting preserve?", "answer": "The relative order of equivalent elements.",
                        "tags": "sorting, algorithms", "links": "",
                    },
                    follow_redirects=True,
                )
                self.assertEqual(200, response.status_code)
                self.assertIn(b"Saved algo-001", response.data)
                self.assertIn("algo-001", [card.card_id for card in load_deck_cards(created_deck)])
            finally:
                if previous_database is None:
                    os.environ.pop("FLASHCARDS_DB_PATH", None)
                else:
                    os.environ["FLASHCARDS_DB_PATH"] = previous_database
                if previous_decks is None:
                    os.environ.pop("FLASHCARDS_DECKS_DIR", None)
                else:
                    os.environ["FLASHCARDS_DECKS_DIR"] = previous_decks


if __name__ == "__main__":
    unittest.main()
