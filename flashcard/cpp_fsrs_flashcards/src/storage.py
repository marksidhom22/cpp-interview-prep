from __future__ import annotations

import json
import mimetypes
import os
import re
import sqlite3
import unicodedata
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
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
    study_progress = data.get("study_progress", {})
    if not isinstance(cards, list) or not isinstance(assets, dict):
        raise ValueError("Deck cards must be a list and assets must be a mapping")
    if not isinstance(study_progress, dict):
        raise ValueError("Deck study_progress must be a mapping")
    card_states = study_progress.get("card_states", {})
    reviews = study_progress.get("reviews", [])
    if not isinstance(card_states, dict) or not isinstance(reviews, list):
        raise ValueError("Deck progress card_states must be a mapping and reviews must be a list")
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
    for card_id, state in card_states.items():
        if not CARD_ID_PATTERN.fullmatch(str(card_id)) or not isinstance(state, dict):
            raise ValueError(f"Invalid progress record for card {card_id!r}")
        if not isinstance(state.get("fsrs"), dict):
            raise ValueError(f"Missing FSRS state for card {card_id}")
        if not state.get("introduced_at") or not state.get("due"):
            raise ValueError(f"Incomplete progress timestamps for card {card_id}")
    if any(not isinstance(review, dict) for review in reviews):
        raise ValueError("Every review history item must be a mapping")
    return data


def _deck_signature(path: Path) -> tuple[str, int, int]:
    if not path.is_file():
        raise ValueError(f"Deck file is missing or too large: {path}")
    stat = path.stat()
    if stat.st_size > MAX_DECK_BYTES:
        raise ValueError(f"Deck file is missing or too large: {path}")
    return str(path.resolve()), stat.st_mtime_ns, stat.st_size


@lru_cache(maxsize=64)
def _cached_deck_document(
    resolved_path: str, modified_ns: int, size: int
) -> dict[str, object]:
    del modified_ns, size
    path = Path(resolved_path)
    return _validate_document(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def read_deck_document(path: Path) -> dict[str, object]:
    # Callers intentionally mutate the returned mapping before an atomic write,
    # so keep the cached parse private and return an independent document.
    return deepcopy(_cached_deck_document(*_deck_signature(path)))


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
        "study_progress": existing.get(
            "study_progress", {"card_states": {}, "reviews": []}
        ),
    }


def save_deck(deck: Deck) -> None:
    current = read_deck_document(deck.path) if deck.path.exists() else None
    write_deck_document(deck.path, _deck_document(deck, current))


@lru_cache(maxsize=64)
def _cached_deck(resolved_path: str, modified_ns: int, size: int) -> Deck:
    data = _cached_deck_document(resolved_path, modified_ns, size)
    settings = data["study_settings"]
    assert isinstance(settings, dict)
    return Deck(
        deck_id=str(data["id"]),
        title=str(data["title"]),
        description=str(data.get("description", "")),
        path=Path(resolved_path),
        desired_retention=float(settings.get("desired_retention", 0.90)),
        new_cards_per_day=int(settings.get("new_cards_per_day", 12)),
        timezone_name=str(settings.get("timezone_name", "America/Los_Angeles")),
        maximum_interval_days=int(settings.get("maximum_interval_days", 3650)),
    )


def _load_deck(path: Path) -> Deck:
    return _cached_deck(*_deck_signature(path))


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
    data.setdefault("study_progress", {"card_states": {}, "reviews": []})
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


@lru_cache(maxsize=64)
def _cached_deck_cards(
    deck: Deck, resolved_path: str, modified_ns: int, size: int
) -> tuple[StudyCard, ...]:
    document = _cached_deck_document(resolved_path, modified_ns, size)
    cards = [_card_from_record(record, deck) for record in document["cards"]]
    return tuple(sorted(cards, key=lambda card: _card_sort_key(card.card_id)))


def load_deck_cards(deck: Deck) -> list[StudyCard]:
    return list(_cached_deck_cards(deck, *_deck_signature(deck.path)))


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


def _progress_section(document: dict[str, object]) -> dict[str, object]:
    progress = document.setdefault(
        "study_progress", {"card_states": {}, "reviews": []}
    )
    if not isinstance(progress, dict):
        raise ValueError("Deck study_progress must be a mapping")
    progress.setdefault("card_states", {})
    progress.setdefault("reviews", [])
    if not isinstance(progress["card_states"], dict) or not isinstance(
        progress["reviews"], list
    ):
        raise ValueError("Deck progress card_states must be a mapping and reviews must be a list")
    return progress


_RATING_NAMES = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}
_RATING_NUMBERS = {name: number for number, name in _RATING_NAMES.items()}


def _rating_name(value: int) -> str:
    try:
        return _RATING_NAMES[value]
    except KeyError as exc:
        raise ValueError(f"Invalid review rating: {value}") from exc


def _rating_number(value: object) -> int:
    if isinstance(value, int) and value in _RATING_NAMES:
        return value
    try:
        return _RATING_NUMBERS[str(value)]
    except KeyError as exc:
        raise ValueError(f"Invalid review rating: {value!r}") from exc


def delete_card(deck: Deck, card: StudyCard) -> None:
    document = read_deck_document(deck.path)
    cards = document["cards"]
    assets = document["assets"]
    assert isinstance(cards, list) and isinstance(assets, dict)
    document["cards"] = [record for record in cards if record.get("id") != card.card_id]
    assets.pop(card.card_id, None)
    progress = _progress_section(document)
    progress["card_states"].pop(card.card_id, None)
    progress["reviews"] = [
        review for review in progress["reviews"] if review.get("card_id") != card.card_id
    ]
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
    def __init__(self, deck: Deck) -> None:
        self.deck = deck
        self.deck_id = deck.deck_id
        self._document_cache: dict[str, object] | None = None
        self._records_cache: dict[str, ProgressRecord] | None = None
        self._reviews_cache: tuple[RecentReview, ...] | None = None

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo != timezone.utc:
            raise ValueError("Progress timestamps must use UTC")
        return value

    @staticmethod
    def _datetime(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value) if value else None

    @classmethod
    def _record(cls, card_id: str, record: dict[str, object]) -> ProgressRecord:
        introduced = cls._datetime(str(record["introduced_at"]))
        due = cls._datetime(str(record["due"]))
        assert introduced is not None and due is not None
        fsrs_state = record["fsrs"]
        if not isinstance(fsrs_state, dict):
            raise ValueError(f"Invalid FSRS state for card {card_id}")
        return ProgressRecord(
            card_id,
            Card.from_json(json.dumps(fsrs_state)),
            introduced,
            cls._datetime(str(record["last_review"])) if record.get("last_review") else None,
            due,
        )

    def _read(self) -> tuple[dict[str, object], dict[str, object]]:
        if self._document_cache is None:
            self._document_cache = read_deck_document(self.deck.path)
        document = self._document_cache
        return document, _progress_section(document)

    def _write(self, document: dict[str, object]) -> None:
        write_deck_document(self.deck.path, document)
        self._document_cache = document
        self._records_cache = None
        self._reviews_cache = None

    def get(self, card_id: str) -> ProgressRecord | None:
        return self.get_all().get(card_id)

    def get_all(self) -> dict[str, ProgressRecord]:
        if self._records_cache is None:
            _, progress = self._read()
            self._records_cache = {
                str(card_id): self._record(str(card_id), record)
                for card_id, record in progress["card_states"].items()
                if isinstance(record, dict)
            }
        return dict(self._records_cache)

    def introduce(self, card_id: str, card: Card, now: datetime) -> ProgressRecord:
        self._utc(now)
        document, progress = self._read()
        states = progress["card_states"]
        existing = states.get(card_id)
        if not isinstance(existing, dict):
            fsrs_state = json.loads(card.to_json())
            states[card_id] = {
                "introduced_at": now.isoformat(),
                "last_review": None,
                "due": card.due.isoformat(),
                "fsrs": fsrs_state,
            }
            self._write(document)
            existing = states[card_id]
        return self._record(card_id, existing)

    def record_review(
        self, card_id: str, card: Card, review: ReviewLog, duration_ms: int | None
    ) -> None:
        reviewed_at = self._utc(review.review_datetime)
        document, progress = self._read()
        state = progress["card_states"].get(card_id)
        if not isinstance(state, dict):
            raise ValueError(f"Card {card_id} must be introduced before it can be reviewed")
        state.update(
            {
                "last_review": reviewed_at.isoformat(),
                "due": card.due.isoformat(),
                "fsrs": json.loads(card.to_json()),
            }
        )
        progress["reviews"].append(
            {
                "card_id": card_id,
                "reviewed_at": reviewed_at.isoformat(),
                "rating": _rating_name(int(review.rating)),
                "scheduled_due": card.due.isoformat(),
                "duration_ms": duration_ms,
                "fsrs_log": json.loads(review.to_json()),
            }
        )
        self._write(document)

    def due_records(self, now: datetime) -> list[ProgressRecord]:
        self._utc(now)
        return sorted(
            (record for record in self.get_all().values() if record.due <= now),
            key=lambda record: (record.due, record.card_id),
        )

    def next_due(self, now: datetime) -> datetime | None:
        self._utc(now)
        future = [record.due for record in self.get_all().values() if record.due > now]
        return min(future) if future else None

    def introduced_count(self) -> int:
        return len(self.get_all())

    def review_count(self) -> int:
        _, progress = self._read()
        return len(progress["reviews"])

    @staticmethod
    def _day_bounds(now: datetime, timezone_name: str) -> tuple[datetime, datetime]:
        local = now.astimezone(ZoneInfo(timezone_name))
        start = local.replace(hour=0, minute=0, second=0, microsecond=0)
        return start.astimezone(timezone.utc), (start + timedelta(days=1)).astimezone(timezone.utc)

    @classmethod
    def _count_today(
        cls, values: list[datetime], now: datetime, timezone_name: str
    ) -> int:
        start, end = cls._day_bounds(now, timezone_name)
        return sum(start <= value < end for value in values)

    def introduced_in_local_day(self, now: datetime, timezone_name: str) -> int:
        return self._count_today(
            [record.introduced_at for record in self.get_all().values()], now, timezone_name
        )

    def reviews_in_local_day(self, now: datetime, timezone_name: str) -> int:
        return self._count_today(
            [review.reviewed_at for review in self.recent_reviews(limit=None)], now, timezone_name
        )

    def rating_counts(self) -> dict[int, int]:
        counts: dict[int, int] = {}
        for review in self.recent_reviews(limit=None):
            counts[review.rating] = counts.get(review.rating, 0) + 1
        return counts

    def recent_reviews(self, limit: int | None = 20) -> list[RecentReview]:
        if self._reviews_cache is None:
            _, progress = self._read()
            reviews = [
                RecentReview(
                    str(record["card_id"]),
                    datetime.fromisoformat(str(record["reviewed_at"])),
                    _rating_number(record["rating"]),
                    datetime.fromisoformat(str(record["scheduled_due"])),
                )
                for record in progress["reviews"]
            ]
            reviews.sort(key=lambda review: review.reviewed_at, reverse=True)
            self._reviews_cache = tuple(reviews)
        reviews = list(self._reviews_cache)
        return reviews if limit is None else reviews[:limit]

    def delete_card_progress(self, card_id: str) -> None:
        document, progress = self._read()
        progress["card_states"].pop(card_id, None)
        progress["reviews"] = [
            review for review in progress["reviews"] if review.get("card_id") != card_id
        ]
        self._write(document)

    def delete_deck_progress(self) -> None:
        document, _ = self._read()
        document["study_progress"] = {"card_states": {}, "reviews": []}
        self._write(document)


def migrate_legacy_progress(database_path: Path, decks: list[Deck]) -> tuple[int, int]:
    """Move the former shared SQLite progress into each deck YAML, then remove the DB."""
    if not database_path.is_file():
        return 0, 0

    connection = sqlite3.connect(database_path)
    try:
        connection.row_factory = sqlite3.Row
        tables = {
            str(row["name"])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not {"card_progress", "reviews"}.issubset(tables):
            raise ValueError(f"Legacy progress database has an unexpected format: {database_path}")
        state_rows = connection.execute(
            "SELECT deck_id, card_id, fsrs_state, introduced_at, last_review, due "
            "FROM card_progress ORDER BY deck_id, card_id"
        ).fetchall()
        review_rows = connection.execute(
            "SELECT deck_id, card_id, reviewed_at, rating, review_log, scheduled_due, "
            "review_duration_ms FROM reviews ORDER BY id"
        ).fetchall()
    finally:
        connection.close()

    deck_by_id = {deck.deck_id: deck for deck in decks}
    source_deck_ids = {
        str(row["deck_id"]) for row in [*state_rows, *review_rows]
    }
    unknown = sorted(source_deck_ids - set(deck_by_id))
    if unknown:
        raise ValueError(
            "Legacy progress belongs to missing decks and was not removed: "
            + ", ".join(unknown)
        )

    states_by_deck: dict[str, list[sqlite3.Row]] = {}
    reviews_by_deck: dict[str, list[sqlite3.Row]] = {}
    for row in state_rows:
        states_by_deck.setdefault(str(row["deck_id"]), []).append(row)
    for row in review_rows:
        reviews_by_deck.setdefault(str(row["deck_id"]), []).append(row)

    for deck in decks:
        document = read_deck_document(deck.path)
        progress = _progress_section(document)
        card_states = progress["card_states"]
        reviews = progress["reviews"]
        assert isinstance(card_states, dict) and isinstance(reviews, list)

        for row in states_by_deck.get(deck.deck_id, []):
            fsrs_state = json.loads(str(row["fsrs_state"]))
            if not isinstance(fsrs_state, dict):
                raise ValueError(f"Invalid legacy FSRS state for {deck.deck_id}/{row['card_id']}")
            card_states.setdefault(
                str(row["card_id"]),
                {
                    "introduced_at": str(row["introduced_at"]),
                    "last_review": str(row["last_review"]) if row["last_review"] else None,
                    "due": str(row["due"]),
                    "fsrs": fsrs_state,
                },
            )

        existing_reviews = {
            (
                str(review.get("card_id")),
                str(review.get("reviewed_at")),
                _rating_number(review.get("rating")),
                str(review.get("scheduled_due")),
            )
            for review in reviews
            if isinstance(review, dict)
        }
        for row in reviews_by_deck.get(deck.deck_id, []):
            signature = (
                str(row["card_id"]),
                str(row["reviewed_at"]),
                int(row["rating"]),
                str(row["scheduled_due"]),
            )
            if signature in existing_reviews:
                continue
            review_log = json.loads(str(row["review_log"]))
            if not isinstance(review_log, dict):
                raise ValueError(f"Invalid legacy review log for {deck.deck_id}/{row['card_id']}")
            reviews.append(
                {
                    "card_id": str(row["card_id"]),
                    "reviewed_at": str(row["reviewed_at"]),
                    "rating": _rating_name(int(row["rating"])),
                    "scheduled_due": str(row["scheduled_due"]),
                    "duration_ms": row["review_duration_ms"],
                    "fsrs_log": review_log,
                }
            )
            existing_reviews.add(signature)

        write_deck_document(deck.path, document)

    for row in state_rows:
        repository = ProgressRepository(deck_by_id[str(row["deck_id"])])
        if repository.get(str(row["card_id"])) is None:
            raise RuntimeError("Legacy progress verification failed; database was kept")

    for suffix in ("", "-wal", "-shm"):
        path = Path(f"{database_path}{suffix}")
        if path.exists():
            path.unlink()
    return len(state_rows), len(review_rows)
