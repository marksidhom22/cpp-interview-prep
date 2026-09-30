from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

from fsrs import Card, Rating, Scheduler, State

from .storage import AppConfig, Deck, ProgressRepository, StudyCard


RATING_BY_NAME = {
    "Again": Rating.Again,
    "Hard": Rating.Hard,
    "Good": Rating.Good,
    "Easy": Rating.Easy,
}


@dataclass(frozen=True)
class SessionCard:
    card: StudyCard
    kind: str


def build_scheduler(deck: Deck, config: AppConfig) -> Scheduler:
    return Scheduler(
        desired_retention=deck.desired_retention,
        learning_steps=config.learning_steps,
        relearning_steps=config.relearning_steps,
        maximum_interval=deck.maximum_interval_days,
        enable_fuzzing=True,
    )


def new_fsrs_card(deck_id: str, card_id: str, now: datetime | None = None) -> Card:
    due = now or datetime.now(timezone.utc)
    if due.tzinfo != timezone.utc:
        raise ValueError("New FSRS cards must use UTC")
    digest = hashlib.blake2b(f"{deck_id}\0{card_id}".encode(), digest_size=8).digest()
    numeric_id = int.from_bytes(digest, "big") & ((1 << 63) - 1)
    return Card(card_id=numeric_id, due=due)


def choose_next_card(
    cards: list[StudyCard],
    repository: ProgressRepository,
    deck: Deck,
    config: AppConfig,
    now: datetime,
) -> SessionCard | None:
    cards_by_id = {card.card_id: card for card in cards}
    for progress in repository.due_records(now):
        card = cards_by_id.get(progress.card_id)
        if card is None:
            continue
        if progress.fsrs_card.stability is None:
            kind = "New"
        elif progress.fsrs_card.state == State.Learning:
            kind = "Learning"
        elif progress.fsrs_card.state == State.Relearning:
            kind = "Relearning"
        else:
            kind = "Review"
        return SessionCard(card, kind)

    if repository.introduced_in_local_day(now, deck.timezone_name) >= deck.new_cards_per_day:
        return None
    introduced = set(repository.get_all())
    return next(
        (SessionCard(card, "New") for card in cards if card.card_id not in introduced),
        None,
    )
