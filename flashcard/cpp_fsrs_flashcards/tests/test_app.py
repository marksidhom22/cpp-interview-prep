from __future__ import annotations

import gc
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.storage import ProgressRepository, list_decks, read_deck_document


class StreamlitAppTests(unittest.TestCase):
    def test_reveal_and_rate_flow(self) -> None:
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
            try:
                app = AppTest.from_file(project_root / "app.py", default_timeout=15)
                app.run()
                self.assertEqual([], list(app.exception))

                reveal = next(button for button in app.button if button.label == "Reveal answer")
                reveal.click().run()
                self.assertEqual([], list(app.exception))

                current_card_id = app.session_state["current_card_id"]
                edit = next(button for button in app.button if button.label == "Edit this card")
                edit.click().run()
                self.assertEqual([], list(app.exception))

                question = next(
                    field for field in app.text_area if field.label == "Question (Markdown)"
                )
                edited_question = f"{question.value}\n\nEdited while studying."
                question.set_value(edited_question).run()
                save = next(button for button in app.button if button.label == "Save changes")
                save.click().run()
                self.assertEqual([], list(app.exception))
                self.assertEqual(current_card_id, app.session_state["current_card_id"])
                self.assertTrue(app.session_state["answer_revealed"])

                document = read_deck_document(copied_deck.path)
                edited_card = next(
                    card for card in document["cards"] if card["id"] == current_card_id
                )
                self.assertEqual(edited_question, edited_card["question"])
                self.assertEqual(0, len(document["study_progress"]["reviews"]))

                good = next(button for button in app.button if button.label.startswith("Good"))
                good.click().run()
                self.assertEqual([], list(app.exception))

                document = read_deck_document(copied_deck.path)
                self.assertEqual(1, len(document["study_progress"]["reviews"]))

                deleted_card_id = app.session_state["current_card_id"]
                card_count = len(document["cards"])
                delete = next(
                    button for button in app.button if button.label == "Delete this card"
                )
                delete.click().run()
                self.assertEqual([], list(app.exception))
                confirmation = next(
                    field
                    for field in app.checkbox
                    if field.label == f"I want to permanently delete {deleted_card_id}"
                )
                confirmation.set_value(True).run()
                delete_permanently = next(
                    button for button in app.button if button.label == "Delete permanently"
                )
                delete_permanently.click().run()
                self.assertEqual([], list(app.exception))

                document = read_deck_document(copied_deck.path)
                self.assertEqual(card_count - 1, len(document["cards"]))
                self.assertNotIn(deleted_card_id, [card["id"] for card in document["cards"]])
                self.assertNotIn(
                    deleted_card_id, document["study_progress"]["card_states"]
                )
                self.assertNotIn(
                    deleted_card_id,
                    [review["card_id"] for review in document["study_progress"]["reviews"]],
                )

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
                document = read_deck_document(copied_deck.path)
                progress_count = len(document["study_progress"]["card_states"])
                review_count = len(document["study_progress"]["reviews"])
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
