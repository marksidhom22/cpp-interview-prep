from __future__ import annotations

import gc
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class StreamlitAppTests(unittest.TestCase):
    def test_reveal_and_rate_flow(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            temporary_root = Path(directory)
            database_path = temporary_root / "progress.db"
            decks_directory = temporary_root / "decks"
            decks_directory.mkdir()
            shutil.copy2(
                project_root / "decks" / "cpp-interview.deck.yaml",
                decks_directory / "cpp-interview.deck.yaml",
            )
            previous_database = os.environ.get("FLASHCARDS_DB_PATH")
            previous_decks = os.environ.get("FLASHCARDS_DECKS_DIR")
            os.environ["FLASHCARDS_DB_PATH"] = str(database_path)
            os.environ["FLASHCARDS_DECKS_DIR"] = str(decks_directory)
            try:
                app = AppTest.from_file(project_root / "app.py", default_timeout=15)
                app.run()
                self.assertEqual([], list(app.exception))

                reveal = next(button for button in app.button if button.label == "Reveal answer")
                reveal.click().run()
                self.assertEqual([], list(app.exception))

                good = next(button for button in app.button if button.label.startswith("Good"))
                good.click().run()
                self.assertEqual([], list(app.exception))

                with sqlite3.connect(database_path) as connection:
                    review_count = connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
                self.assertEqual(1, review_count)

                for workspace_name in ("Cards", "Statistics", "Study"):
                    workspace = next(
                        button for button in app.button if button.label == workspace_name
                    )
                    workspace.click().run()
                    self.assertEqual([], list(app.exception))

                manage_decks = next(
                    button for button in app.button if button.label == "Manage decks"
                )
                manage_decks.click().run()
                self.assertEqual([], list(app.exception))
                self.assertIn("Reset study progress", [button.label for button in app.button])
                reset_confirmation = next(
                    field
                    for field in app.text_input
                    if field.label.startswith("Type RESET to start")
                )
                reset_confirmation.set_value("RESET").run()
                reset_button = next(
                    button for button in app.button if button.label == "Reset study progress"
                )
                reset_button.click().run()
                self.assertEqual([], list(app.exception))
                with sqlite3.connect(database_path) as connection:
                    progress_count = connection.execute(
                        "SELECT COUNT(*) FROM card_progress"
                    ).fetchone()[0]
                    review_count = connection.execute(
                        "SELECT COUNT(*) FROM reviews"
                    ).fetchone()[0]
                self.assertEqual((0, 0), (progress_count, review_count))

                new_title = next(
                    field
                    for field in app.text_input
                    if field.label == "Title" and not field.value
                )
                new_title.set_value("Algorithms Practice").run()
                create_button = next(
                    button for button in app.button if button.label == "Create deck"
                )
                create_button.click().run()
                self.assertEqual([], list(app.exception))
                self.assertTrue((decks_directory / "algorithms-practice.deck.yaml").is_file())
                current_deck = next(
                    selectbox for selectbox in app.selectbox if selectbox.label == "Current deck"
                )
                self.assertEqual("algorithms-practice", current_deck.value)
            finally:
                if "app" in locals():
                    del app
                gc.collect()
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
