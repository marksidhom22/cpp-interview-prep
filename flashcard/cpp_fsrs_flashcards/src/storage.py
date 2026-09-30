from __future__ import annotations

import mimetypes
import os
import re
import sqlite3
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator
from zoneinfo import ZoneInfo

import yaml
from fsrs import Card, ReviewLog


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DECK_FILE_SUFFIX = ".deck.yaml"
MAX_DECK_BYTES = 100 * 1024 * 1024
MAX_IMAGE_BYTES = 15 * 1024 * 1024
DECK_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
CARD_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


@dataclass(frozen=True)
class AppConfig:
    learning_steps: tuple[timedelta, ...] = (timedelta(minutes=1), timedelta(minutes=10))
    relearning_steps: tuple[timedelta, ...] = (timedelta(minutes=10),)
    decks_directory: Path = Path(
        os.environ.get("FLASHCARDS_DECKS_DIR", PROJECT_ROOT / "decks")
    )
    database_path: Path = Path(
        os.environ.get("FLASHCARDS_DB_PATH", PROJECT_ROOT / "data" / "progress.db")
    )


CONFIG = AppConfig()


@dataclass(frozen=True)
class Deck:
    deck_id: str
    title: str
    description: str
    path: Path
    desired_retention: float = 0.90
    new_cards_per_day: int = 12
    timezone_name: str = "America/Los_Angeles"
    maximum_interval_days: int = 3650


@dataclass(frozen=True)
class StudyCard:
    card_id: str
    topic: str
    question: str
    answer: str
    tags: tuple[str, ...]
    links: tuple[str, ...]
    source: str | None
    path: Path


class _DeckDumper(yaml.SafeDumper):
    pass


def _represent_string(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str", value, style="|" if "\n" in value else None
    )


_DeckDumper.add_representer(str, _represent_string)


def _slug(value: str, maximum: int = 64) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return (re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()[:maximum] or "deck")


def _validate_document(data: object) -> dict[str, object]:
    if not isinstance(data, dict):
        raise ValueError("Deck file must contain a YAML mapping")
    if int(data.get("format_version", 0)) != 1:
        raise ValueError("Unsupported or missing deck format_version")
    deck_id = str(data.get("id", "")).strip()
    if not DECK_ID_PATTERN.fullmatch(deck_id):
        raise ValueError(f"Invalid deck ID: {deck_id!r}")
    if not str(data.get("title", "")).strip():
        raise ValueError("Deck title is required")
    if not isinstance(data.get("study_settings", {}), dict):
        raise ValueError("Deck study_settings must be a mapping")
    cards = data.get("cards", [])
    assets = data.get("assets", {})
    if not isinstance(cards, list) or not isinstance(assets, dict):
        raise ValueError("Deck cards must be a list and assets must be a mapping")
    seen: set[str] = set()
    for record in cards:
        if not isinstance(record, dict):
            raise ValueError("Every card must be a mapping")
        card_id = str(record.get("id", "")).strip()
        if not CARD_ID_PATTERN.fullmatch(card_id):
            raise ValueError(f"Invalid card ID: {card_id!r}")
        if card_id in seen:
            raise ValueError(f"Duplicate card ID: {card_id}")
        if not str(record.get("question", "")).strip() or not str(
            record.get("answer", "")
        ).strip():
            raise ValueError(f"Question and answer are required for card {card_id}")
        seen.add(card_id)
    return data


def read_deck_document(path: Path) -> dict[str, object]:
    if not path.is_file() or path.stat().st_size > MAX_DECK_BYTES:
        raise ValueError(f"Deck file is missing or too large: {path}")
    return _validate_document(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def write_deck_document(path: Path, data: dict[str, object]) -> None:
    _validate_document(data)
    rendered = yaml.dump(
        data,
        Dumper=_DeckDumper,
        sort_keys=False,
        allow_unicode=True,
        width=1000,
    ).encode("utf-8")
    if len(rendered) > MAX_DECK_BYTES:
        raise ValueError("Deck file would be larger than 100 MB")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(rendered)
    temporary.replace(path)


def _deck_document(deck: Deck, existing: dict[str, object] | None = None) -> dict[str, object]:
    existing = existing or {}
    return {
        "format_version": 1,
        "id": deck.deck_id,
        "title": deck.title,
        "description": deck.description,
        "study_settings": {
            "desired_retention": deck.desired_retention,
            "new_cards_per_day": deck.new_cards_per_day,
            "timezone_name": deck.timezone_name,
            "maximum_interval_days": deck.maximum_interval_days,
        },
        "cards": existing.get("cards", []),
        "assets": existing.get("assets", {}),
    }


def save_deck(deck: Deck) -> None:
    current = read_deck_document(deck.path) if deck.path.exists() else None
    write_deck_document(deck.path, _deck_document(deck, current))


def _load_deck(path: Path) -> Deck:
    data = read_deck_document(path)
    settings = data["study_settings"]
    assert isinstance(settings, dict)
    return Deck(
        deck_id=str(data["id"]),
        title=str(data["title"]),
        description=str(data.get("description", "")),
        path=path,
        desired_retention=float(settings.get("desired_retention", 0.90)),
        new_cards_per_day=int(settings.get("new_cards_per_day", 12)),
        timezone_name=str(settings.get("timezone_name", "America/Los_Angeles")),
        maximum_interval_days=int(settings.get("maximum_interval_days", 3650)),
    )


def list_decks(directory: Path) -> list[Deck]:
    directory.mkdir(parents=True, exist_ok=True)
    decks = [_load_deck(path) for path in directory.glob(f"*{DECK_FILE_SUFFIX}")]
    ids = [deck.deck_id for deck in decks]
    if len(ids) != len(set(ids)):
        raise ValueError("Deck IDs must be unique")
    return sorted(decks, key=lambda deck: deck.title.casefold())


def _unique_deck_id(directory: Path, title: str) -> str:
    existing = {deck.deck_id for deck in list_decks(directory)}
    base = _slug(title)
    candidate = base
    number = 2
    while candidate in existing:
        candidate = f"{base[:58]}-{number}"
        number += 1
    return candidate


def create_deck(
    directory: Path,
    title: str,
    description: str = "",
    *,
    desired_retention: float = 0.90,
    new_cards_per_day: int = 12,
) -> Deck:
    title = title.strip()
    if not title:
        raise ValueError("Deck title is required")
    deck_id = _unique_deck_id(directory, title)
    deck = Deck(
        deck_id,
        title,
        description.strip(),
        directory / f"{deck_id}{DECK_FILE_SUFFIX}",
        desired_retention,
        new_cards_per_day,
    )
    save_deck(deck)
    return deck


def update_deck(deck: Deck, **changes: object) -> Deck:
    updated = replace(deck, **changes)
    if not updated.title.strip():
        raise ValueError("Deck title is required")
    if not 0.70 <= updated.desired_retention <= 0.99:
        raise ValueError("Desired retention must be between 70% and 99%")
    if not 0 <= updated.new_cards_per_day <= 500:
        raise ValueError("New cards per day must be between 0 and 500")
    save_deck(updated)
    return updated


def delete_deck(deck: Deck, directory: Path) -> None:
    target = deck.path.resolve()
    if target.parent != directory.resolve() or target.suffix.lower() != ".yaml":
        raise ValueError("Deck path is outside the deck directory")
    target.unlink()


def export_deck(deck: Deck) -> bytes:
    return deck.path.read_bytes()


def import_deck(directory: Path, content: bytes) -> Deck:
    if len(content) > MAX_DECK_BYTES:
        raise ValueError("Deck file is larger than 100 MB")
    try:
        data = _validate_document(yaml.safe_load(content.decode("utf-8")) or {})
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError("Deck file is not valid UTF-8 YAML") from exc
    title = str(data["title"]).strip()
    deck_id = _unique_deck_id(directory, title)
    data["id"] = deck_id
    path = directory / f"{deck_id}{DECK_FILE_SUFFIX}"
    write_deck_document(path, data)
    return _load_deck(path)


def _card_from_record(record: object, deck: Deck) -> StudyCard:
    if not isinstance(record, dict):
        raise ValueError("Every card must be a mapping")
    tags = record.get("tags") or []
    links = record.get("links") or []
    if not isinstance(tags, list) or not isinstance(links, list):
        raise ValueError("Card tags and links must be lists")
    source = record.get("source")
    return StudyCard(
        card_id=str(record["id"]).strip(),
        topic=str(record.get("topic", "General")).strip() or "General",
        question=str(record["question"]).strip(),
        answer=str(record["answer"]).strip(),
        tags=tuple(str(value).strip() for value in tags if str(value).strip()),
        links=tuple(str(value).strip() for value in links if str(value).strip()),
        source=str(source).strip() if source else None,
        path=deck.path,
    )


def _card_sort_key(card_id: str) -> tuple[object, ...]:
    return tuple(
        int(part) if part.isdigit() else part
        for part in re.split(r"([0-9]+)", card_id.casefold())
    )


def load_deck_cards(deck: Deck) -> list[StudyCard]:
    document = read_deck_document(deck.path)
    cards = [_card_from_record(record, deck) for record in document["cards"]]
    return sorted(cards, key=lambda card: _card_sort_key(card.card_id))


def next_card_id(cards: list[StudyCard]) -> str:
    used = {card.card_id for card in cards}
    number = 1
    while f"card-{number:04d}" in used:
        number += 1
    return f"card-{number:04d}"


def save_card(
    deck: Deck,
    *,
    card_id: str,
    topic: str,
    question: str,
    answer: str,
    tags: list[str] | tuple[str, ...] = (),
    links: list[str] | tuple[str, ...] = (),
    source: str | None = None,
    existing_path: Path | None = None,
) -> StudyCard:
    del existing_path
    card_id, question, answer = card_id.strip(), question.strip(), answer.strip()
    if not CARD_ID_PATTERN.fullmatch(card_id):
        raise ValueError("Invalid card ID")
    if not question or not answer:
        raise ValueError("Question and answer are required")
    record: dict[str, object] = {
        "id": card_id,
        "topic": topic.strip() or "General",
        "question": question,
        "answer": answer,
    }
    cleaned_tags = sorted({value.strip() for value in tags if value.strip()}, key=str.casefold)
    cleaned_links = list(dict.fromkeys(value.strip() for value in links if value.strip()))
    if cleaned_tags:
        record["tags"] = cleaned_tags
    if cleaned_links:
        record["links"] = cleaned_links
    if source:
        record["source"] = source

    document = read_deck_document(deck.path)
    cards = document["cards"]
    assert isinstance(cards, list)
    indexes = [index for index, value in enumerate(cards) if value.get("id") == card_id]
    if indexes:
        cards[indexes[0]] = record
    else:
        cards.append(record)
    write_deck_document(deck.path, document)
    return _card_from_record(record, deck)


def save_uploaded_image(deck: Deck, card_id: str, name: str, data: bytes) -> str:
    suffix = Path(name).suffix.lower()
    mime_type, _ = mimetypes.guess_type(name)
    if suffix not in ALLOWED_IMAGE_SUFFIXES or mime_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValueError("Images must be PNG, JPEG, WebP, or GIF")
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Images must be non-empty and no larger than 15 MB")
    document = read_deck_document(deck.path)
    assets = document["assets"]
    assert isinstance(assets, dict)
    card_assets = assets.setdefault(card_id, {})
    if not isinstance(card_assets, dict):
        raise ValueError(f"Invalid assets for card {card_id}")
    stem = _slug(Path(name).stem, 56)
    filename = f"{stem}{suffix}"
    number = 2
    while filename in card_assets:
        filename = f"{stem}-{number}{suffix}"
        number += 1
    card_assets[filename] = {"media_type": mime_type, "data": data}
    write_deck_document(deck.path, document)
    return f"asset://{filename}"


def load_embedded_asset(deck: Deck, card_id: str, filename: str) -> tuple[str, bytes] | None:
    if Path(filename).name != filename:
        return None
    assets = read_deck_document(deck.path)["assets"]
    assert isinstance(assets, dict)
    card_assets = assets.get(card_id, {})
    asset = card_assets.get(filename) if isinstance(card_assets, dict) else None
    if not isinstance(asset, dict):
        return None
    media_type, data = asset.get("media_type"), asset.get("data")
    if media_type not in ALLOWED_IMAGE_MIME_TYPES or not isinstance(data, bytes):
        return None
    return str(media_type), data


def delete_card(deck: Deck, card: StudyCard) -> None:
    document = read_deck_document(deck.path)
    cards = document["cards"]
    assets = document["assets"]
    assert isinstance(cards, list) and isinstance(assets, dict)
    document["cards"] = [record for record in cards if record.get("id") != card.card_id]
    assets.pop(card.card_id, None)
    write_deck_document(deck.path, document)


@dataclass(frozen=True)
class ProgressRecord:
    card_id: str
    fsrs_card: Card
    introduced_at: datetime
    last_review: datetime | None
    due: datetime


@dataclass(frozen=True)
class RecentReview:
    card_id: str
    reviewed_at: datetime
    rating: int
    scheduled_due: datetime


class ProgressRepository:
    def __init__(self, database_path: Path, deck_id: str) -> None:
        self.database_path = database_path
        self.deck_id = deck_id
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS card_progress (
                    deck_id TEXT NOT NULL,
                    card_id TEXT NOT NULL,
                    fsrs_state TEXT NOT NULL,
                    introduced_at TEXT NOT NULL,
                    last_review TEXT,
                    due TEXT NOT NULL,
                    PRIMARY KEY (deck_id, card_id)
                );
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deck_id TEXT NOT NULL,
                    card_id TEXT NOT NULL,
                    reviewed_at TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    review_log TEXT NOT NULL,
                    scheduled_due TEXT NOT NULL,
                    review_duration_ms INTEGER,
                    FOREIGN KEY(deck_id, card_id) REFERENCES card_progress(deck_id, card_id)
                        ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_progress_due ON card_progress(deck_id, due);
                CREATE INDEX IF NOT EXISTS idx_reviews_time ON reviews(deck_id, reviewed_at);
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo != timezone.utc:
            raise ValueError("Progress timestamps must use UTC")
        return value

    @staticmethod
    def _datetime(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value) if value else None

    @classmethod
    def _record(cls, row: sqlite3.Row) -> ProgressRecord:
        introduced = cls._datetime(row["introduced_at"])
        due = cls._datetime(row["due"])
        assert introduced is not None and due is not None
        return ProgressRecord(
            row["card_id"],
            Card.from_json(row["fsrs_state"]),
            introduced,
            cls._datetime(row["last_review"]),
            due,
        )

    def get(self, card_id: str) -> ProgressRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM card_progress WHERE deck_id=? AND card_id=?",
                (self.deck_id, card_id),
            ).fetchone()
        return self._record(row) if row else None

    def get_all(self) -> dict[str, ProgressRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM card_progress WHERE deck_id=?", (self.deck_id,)
            ).fetchall()
        return {row["card_id"]: self._record(row) for row in rows}

    def introduce(self, card_id: str, card: Card, now: datetime) -> ProgressRecord:
        self._utc(now)
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO card_progress VALUES (?, ?, ?, ?, NULL, ?)",
                (self.deck_id, card_id, card.to_json(), now.isoformat(), card.due.isoformat()),
            )
        record = self.get(card_id)
        assert record is not None
        return record

    def record_review(
        self, card_id: str, card: Card, review: ReviewLog, duration_ms: int | None
    ) -> None:
        reviewed_at = self._utc(review.review_datetime)
        with self._connect() as connection:
            connection.execute(
                "UPDATE card_progress SET fsrs_state=?, last_review=?, due=? "
                "WHERE deck_id=? AND card_id=?",
                (
                    card.to_json(),
                    reviewed_at.isoformat(),
                    card.due.isoformat(),
                    self.deck_id,
                    card_id,
                ),
            )
            connection.execute(
                "INSERT INTO reviews "
                "(deck_id, card_id, reviewed_at, rating, review_log, scheduled_due, review_duration_ms) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    self.deck_id,
                    card_id,
                    reviewed_at.isoformat(),
                    int(review.rating),
                    review.to_json(),
                    card.due.isoformat(),
                    duration_ms,
                ),
            )

    def due_records(self, now: datetime) -> list[ProgressRecord]:
        self._utc(now)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM card_progress WHERE deck_id=? AND due<=? ORDER BY due, card_id",
                (self.deck_id, now.isoformat()),
            ).fetchall()
        return [self._record(row) for row in rows]

    def next_due(self, now: datetime) -> datetime | None:
        self._utc(now)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT due FROM card_progress WHERE deck_id=? AND due>? ORDER BY due LIMIT 1",
                (self.deck_id, now.isoformat()),
            ).fetchone()
        return self._datetime(row["due"]) if row else None

    def _count(self, table: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT COUNT(*) AS n FROM {table} WHERE deck_id=?", (self.deck_id,)
            ).fetchone()
        return int(row["n"])

    def introduced_count(self) -> int:
        return self._count("card_progress")

    def review_count(self) -> int:
        return self._count("reviews")

    @staticmethod
    def _day_bounds(now: datetime, timezone_name: str) -> tuple[datetime, datetime]:
        local = now.astimezone(ZoneInfo(timezone_name))
        start = local.replace(hour=0, minute=0, second=0, microsecond=0)
        return start.astimezone(timezone.utc), (start + timedelta(days=1)).astimezone(timezone.utc)

    def _count_today(self, table: str, column: str, now: datetime, timezone_name: str) -> int:
        start, end = self._day_bounds(now, timezone_name)
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT COUNT(*) AS n FROM {table} "
                f"WHERE deck_id=? AND {column}>=? AND {column}<?",
                (self.deck_id, start.isoformat(), end.isoformat()),
            ).fetchone()
        return int(row["n"])

    def introduced_in_local_day(self, now: datetime, timezone_name: str) -> int:
        return self._count_today("card_progress", "introduced_at", now, timezone_name)

    def reviews_in_local_day(self, now: datetime, timezone_name: str) -> int:
        return self._count_today("reviews", "reviewed_at", now, timezone_name)

    def rating_counts(self) -> dict[int, int]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT rating, COUNT(*) AS n FROM reviews WHERE deck_id=? GROUP BY rating",
                (self.deck_id,),
            ).fetchall()
        return {int(row["rating"]): int(row["n"]) for row in rows}

    def recent_reviews(self, limit: int = 20) -> list[RecentReview]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT card_id, reviewed_at, rating, scheduled_due FROM reviews "
                "WHERE deck_id=? ORDER BY reviewed_at DESC LIMIT ?",
                (self.deck_id, limit),
            ).fetchall()
        return [
            RecentReview(
                row["card_id"],
                datetime.fromisoformat(row["reviewed_at"]),
                int(row["rating"]),
                datetime.fromisoformat(row["scheduled_due"]),
            )
            for row in rows
        ]

    def delete_card_progress(self, card_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM card_progress WHERE deck_id=? AND card_id=?",
                (self.deck_id, card_id),
            )

    def delete_deck_progress(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM card_progress WHERE deck_id=?", (self.deck_id,))
