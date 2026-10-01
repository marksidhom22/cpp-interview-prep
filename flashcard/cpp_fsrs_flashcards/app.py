from __future__ import annotations

import os
import secrets
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import Flask, abort, flash, g, make_response, redirect, render_template, request, session, url_for
from fsrs import Scheduler

from src.content import fetch_link_preview, plain_speech_text, render_rich_markdown
from src.storage import (
    CARD_ID_PATTERN,
    CONFIG,
    Deck,
    ProgressRepository,
    StudyCard,
    create_deck,
    delete_card,
    delete_deck,
    export_deck,
    import_deck,
    list_decks,
    load_deck_cards,
    load_embedded_asset,
    migrate_legacy_progress,
    next_card_id,
    save_card,
    save_uploaded_image,
    update_deck,
)
from src.study import RATING_BY_NAME, SessionCard, build_scheduler, choose_next_card, new_fsrs_card


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("FLASHCARDS_SECRET_KEY") or secrets.token_hex(32),
    MAX_CONTENT_LENGTH=110 * 1024 * 1024,
)

VIEWS = ("Study", "Cards", "Statistics", "Decks")
RATING_HELP = {
    "Again": "The core answer was missing or wrong.",
    "Hard": "Partial recall; an important rule or reason was missing.",
    "Good": "Substantially correct after some thought.",
    "Easy": "Immediate, complete, and well reasoned.",
}
RATING_LABELS = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def legacy_database_path() -> Path:
    override = os.environ.get("FLASHCARDS_DB_PATH") or os.environ.get("CPP_FLASHCARDS_DB_PATH")
    return Path(override) if override else Path(__file__).resolve().parent / "data" / "progress.db"


def decks_path() -> Path:
    override = os.environ.get("FLASHCARDS_DECKS_DIR")
    return Path(override) if override else CONFIG.decks_directory


def format_local(value: datetime, timezone_name: str) -> str:
    return value.astimezone(ZoneInfo(timezone_name)).strftime("%b %d, %I:%M %p").replace(" 0", " ")


def format_interval(due: datetime, now: datetime) -> str:
    seconds = max(0, int((due - now).total_seconds()))
    if seconds < 90:
        return "< 2 min"
    if seconds < 3600:
        return f"{round(seconds / 60)} min"
    if seconds < 172800:
        hours = seconds / 3600
        return f"{hours:.1f} hr" if hours < 10 else f"{round(hours)} hr"
    days = seconds / 86400
    return f"{days:.1f} d" if days < 10 else f"{round(days)} d"


def preview_scheduler(deck: Deck) -> Scheduler:
    return Scheduler(
        desired_retention=deck.desired_retention,
        learning_steps=CONFIG.learning_steps,
        relearning_steps=CONFIG.relearning_steps,
        maximum_interval=deck.maximum_interval_days,
        enable_fuzzing=False,
    )


def clear_study_state() -> None:
    for key in (
        "study_deck_id", "current_card_id", "current_card_kind", "answer_revealed",
        "card_started_at", "question_spoken_key", "answer_spoken_key",
    ):
        session.pop(key, None)


def get_library() -> list[Deck]:
    decks = list_decks(decks_path())
    migrate_legacy_progress(legacy_database_path(), decks)
    return decks


def get_deck(deck_id: str) -> Deck:
    deck = next((item for item in g.decks if item.deck_id == deck_id), None)
    if deck is None:
        abort(404)
    return deck


def render_page(view: str, *, deck: Deck | None = None, cards: list[StudyCard] | None = None, repository: ProgressRepository | None = None, **extra):
    decks = g.decks
    selected_id = session.get("selected_deck_id")
    if deck:
        selected_id = deck.deck_id
    return render_template(
        "page.html",
        view=view,
        views=VIEWS,
        decks=decks,
        selected_id=selected_id,
        deck=deck,
        cards=cards or [],
        repository=repository,
        now=utc_now(),
        rating_help=RATING_HELP,
        rating_labels=RATING_LABELS,
        **extra,
    )


def card_by_id(cards: list[StudyCard], card_id: str | None) -> StudyCard | None:
    return next((card for card in cards if card.card_id == card_id), None)


def valid_web_urls(raw: str) -> list[str]:
    urls = []
    for line in raw.splitlines():
        url = line.strip()
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"Invalid web URL: {url}")
        urls.append(url)
    return list(dict.fromkeys(urls))


def append_block(content: str, block: str) -> str:
    return f"{content.rstrip()}\n\n{block.strip()}" if block.strip() else content.rstrip()


@app.before_request
def prepare_request() -> None:
    try:
        g.decks = get_library()
    except Exception as exc:
        g.decks = []
        flash(f"Could not load the deck library: {exc}", "error")
    ids = {deck.deck_id for deck in g.decks}
    if session.get("selected_deck_id") not in ids:
        session["selected_deck_id"] = g.decks[0].deck_id if g.decks else None
    if session.get("view") not in VIEWS:
        session["view"] = "Study"


@app.get("/")
def index():
    requested_view = request.args.get("view")
    if requested_view in VIEWS:
        session["view"] = requested_view
    view = session.get("view", "Study")
    selected_id = session.get("selected_deck_id")
    deck = next((item for item in g.decks if item.deck_id == selected_id), None)
    if deck is None:
        return render_page("Decks", deck=None)
    cards = load_deck_cards(deck)
    repository = ProgressRepository(deck)
    if view == "Decks":
        return render_page(view, deck=deck, cards=cards, repository=repository)
    if view == "Study":
        return study_page(deck, cards, repository)
    if view == "Cards":
        query = request.args.get("q", "")
        topic = request.args.get("topic", "All topics")
        filtered = [
            card for card in cards
            if (topic == "All topics" or card.topic == topic)
            and (not query or query.casefold() in " ".join((card.card_id, card.topic, card.question, card.answer, " ".join(card.tags))).casefold())
        ]
        chosen = card_by_id(filtered, request.args.get("card")) or (filtered[0] if filtered else None)
        return render_page(view, deck=deck, cards=cards, repository=repository, filtered_cards=filtered, selected_card=chosen, query=query, topic=topic, topics=["All topics", *sorted({card.topic for card in cards}, key=str.casefold)])
    return render_page("Statistics", deck=deck, cards=cards, repository=repository, topic_counts=Counter(card.topic for card in cards))


def study_page(deck: Deck, cards: list[StudyCard], repository: ProgressRepository):
    if not cards:
        return render_page("Study", deck=deck, cards=cards, repository=repository)
    now = utc_now()
    if session.get("study_deck_id") != deck.deck_id:
        clear_study_state()
        session["study_deck_id"] = deck.deck_id
    current = card_by_id(cards, session.get("current_card_id"))
    selected = SessionCard(current, session.get("current_card_kind", "Review")) if current else None
    if selected is None:
        selected = choose_next_card(cards, repository, deck, CONFIG, now)
        if selected:
            if selected.kind == "New":
                repository.introduce(selected.card.card_id, new_fsrs_card(deck.deck_id, selected.card.card_id, now), now)
            session.update(
                current_card_id=selected.card.card_id,
                current_card_kind=selected.kind,
                answer_revealed=False,
                card_started_at=time.time(),
            )
    if selected is None:
        next_due = repository.next_due(now)
        message = f"Next review: {format_local(next_due, deck.timezone_name)}" if next_due else "Every card in this deck is complete for now."
        return render_page("Study", deck=deck, cards=cards, repository=repository, session_complete=True, completion_message=message)
    progress = repository.get(selected.card.card_id)
    if progress is None:
        flash(f"Progress state is missing for card {selected.card.card_id}.", "error")
        return redirect(url_for("index"))
    intervals = {}
    rating_now = utc_now()
    scheduler = preview_scheduler(deck)
    for name, rating in RATING_BY_NAME.items():
        preview, _ = scheduler.review_card(progress.fsrs_card, rating, review_datetime=rating_now)
        intervals[name] = format_interval(preview.due, rating_now)
    memory = progress.fsrs_card
    retrievability = None
    if memory.last_review is not None and memory.stability is not None:
        retrievability = build_scheduler(deck, CONFIG).get_card_retrievability(memory, current_datetime=rating_now)
    spoken_key = f"{deck.deck_id}:{selected.card.card_id}"
    auto_read = bool(session.get("auto_read"))
    question_autoplay = auto_read and session.get("question_spoken_key") != spoken_key
    answer_autoplay = auto_read and session.get("answer_spoken_key") != spoken_key and bool(session.get("answer_revealed"))
    if question_autoplay:
        session["question_spoken_key"] = spoken_key
    if answer_autoplay:
        session["answer_spoken_key"] = spoken_key
    return render_page(
        "Study", deck=deck, cards=cards, repository=repository, selected=selected,
        progress=progress, intervals=intervals, retrievability=retrievability,
        revealed=bool(session.get("answer_revealed")), auto_read=auto_read,
        question_autoplay=question_autoplay, answer_autoplay=answer_autoplay,
    )


@app.post("/study")
def study_action():
    action = request.form.get("action", "")
    if action == "auto_read":
        session["auto_read"] = request.form.get("enabled") == "1"
        return redirect(url_for("index", view="Study"))
    deck = next((item for item in g.decks if item.deck_id == session.get("selected_deck_id")), None)
    if deck is None:
        return redirect(url_for("index", view="Decks"))
    cards = load_deck_cards(deck)
    card = card_by_id(cards, session.get("current_card_id"))
    if action == "reveal" and card:
        session["answer_revealed"] = True
    elif action == "rate" and card and session.get("answer_revealed"):
        rating_name = request.form.get("rating", "")
        if rating_name not in RATING_BY_NAME:
            abort(400)
        repository = ProgressRepository(deck)
        progress = repository.get(card.card_id)
        if progress is None:
            abort(409)
        review_time = utc_now()
        duration_ms = max(0, int((time.time() - float(session.get("card_started_at", time.time()))) * 1000))
        updated, log = build_scheduler(deck, CONFIG).review_card(
            progress.fsrs_card, RATING_BY_NAME[rating_name], review_datetime=review_time, review_duration=duration_ms
        )
        repository.record_review(card.card_id, updated, log, duration_ms)
        flash(f"{card.card_id} · {rating_name} · next in {format_interval(updated.due, review_time)}", "success")
        clear_study_state()
        session["study_deck_id"] = deck.deck_id
    return redirect(url_for("index", view="Study"))


@app.post("/deck/select")
def select_deck():
    deck_id = request.form.get("deck_id")
    if deck_id not in {deck.deck_id for deck in g.decks}:
        abort(404)
    session["selected_deck_id"] = deck_id
    clear_study_state()
    return redirect(url_for("index"))


@app.post("/cards")
def card_action():
    deck = get_deck(session.get("selected_deck_id", ""))
    cards = load_deck_cards(deck)
    action = request.form.get("action")
    card_id = request.form.get("card_id", "").strip()
    existing = card_by_id(cards, card_id)
    try:
        if action == "delete":
            if existing is None or request.form.get("confirm") != "yes":
                raise ValueError("Confirm the card deletion first")
            delete_card(deck, existing)
            clear_study_state()
            flash(f"Deleted {card_id}.", "success")
            return redirect(url_for("index", view="Cards"))
        editing = action == "edit"
        if action not in {"add", "edit"}:
            abort(400)
        if not editing and any(card.card_id == card_id for card in cards):
            raise ValueError(f"Card ID already exists: {card_id}")
        if editing and existing is None:
            raise ValueError(f"Card not found: {card_id}")
        question = request.form.get("question", "").strip()
        answer = request.form.get("answer", "").strip()
        if not CARD_ID_PATTERN.fullmatch(card_id):
            raise ValueError("Card ID contains unsupported characters")
        if not question or not answer:
            raise ValueError("Question and answer are required")
        parsed_links = valid_web_urls(request.form.get("links", ""))
        for image_url in valid_web_urls(request.form.get("remote_images", "")):
            alt = urlparse(image_url).path.rsplit("/", 1)[-1] or "Remote image"
            block = f"![{alt}]({image_url})"
            if request.form.get("remote_placement") == "Question":
                question = append_block(question, block)
            else:
                answer = append_block(answer, block)
        mermaid = request.form.get("mermaid", "").strip()
        if mermaid:
            block = f"```mermaid\n{mermaid}\n```"
            if request.form.get("mermaid_placement") == "Question":
                question = append_block(question, block)
            else:
                answer = append_block(answer, block)
        for upload in request.files.getlist("images"):
            if upload.filename:
                asset_uri = save_uploaded_image(deck, card_id, upload.filename, upload.read())
                block = f"![{Path(upload.filename).stem}]({asset_uri})"
                if request.form.get("upload_placement") == "Question":
                    question = append_block(question, block)
                else:
                    answer = append_block(answer, block)
        save_card(
            deck, card_id=card_id, topic=request.form.get("topic", "General"), question=question, answer=answer,
            tags=[tag.strip() for tag in request.form.get("tags", "").split(",")], links=parsed_links,
            source=existing.source if existing else None,
        )
        clear_study_state()
        flash(f"Saved {card_id}.", "success")
    except (ValueError, OSError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("index", view="Cards", card=card_id))


@app.post("/decks")
def deck_action():
    action = request.form.get("action")
    try:
        if action == "create":
            created = create_deck(
                decks_path(), request.form.get("title", ""), request.form.get("description", ""),
                desired_retention=float(request.form.get("desired_retention", 0.90)),
                new_cards_per_day=int(request.form.get("new_cards_per_day", 12)),
            )
            session["selected_deck_id"] = created.deck_id
            session["view"] = "Cards"
            clear_study_state()
            flash(f"Created {created.title}.", "success")
        elif action == "import":
            upload = request.files.get("deck_file")
            if upload is None or not upload.filename:
                raise ValueError("Choose a deck file to import")
            imported = import_deck(decks_path(), upload.read())
            session["selected_deck_id"] = imported.deck_id
            flash(f"Imported {imported.title}.", "success")
        else:
            deck = get_deck(request.form.get("deck_id", ""))
            if action == "update":
                timezone_name = request.form.get("timezone_name", "").strip()
                ZoneInfo(timezone_name)
                update_deck(
                    deck, title=request.form.get("title", "").strip(), description=request.form.get("description", "").strip(),
                    desired_retention=float(request.form.get("desired_retention", deck.desired_retention)),
                    new_cards_per_day=int(request.form.get("new_cards_per_day", deck.new_cards_per_day)),
                    timezone_name=timezone_name,
                    maximum_interval_days=int(request.form.get("maximum_interval_days", deck.maximum_interval_days)),
                )
                clear_study_state()
                flash("Deck settings saved.", "success")
            elif action == "reset":
                if request.form.get("confirmation") != "RESET":
                    raise ValueError("Type RESET to confirm")
                ProgressRepository(deck).delete_deck_progress()
                clear_study_state()
                flash(f"Study progress for {deck.title} was reset.", "success")
            elif action == "delete":
                if request.form.get("confirmation") != deck.title:
                    raise ValueError("Deck title did not match")
                delete_deck(deck, decks_path())
                remaining = [item for item in g.decks if item.deck_id != deck.deck_id]
                session["selected_deck_id"] = remaining[0].deck_id if remaining else None
                clear_study_state()
                flash(f"Deleted {deck.title}.", "success")
            else:
                abort(400)
    except (ValueError, ZoneInfoNotFoundError, OSError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("index", view=session.get("view", "Decks")))


@app.get("/export/<deck_id>")
def export(deck_id: str):
    deck = get_deck(deck_id)
    response = make_response(export_deck(deck))
    response.headers["Content-Type"] = "application/yaml"
    response.headers["Content-Disposition"] = f'attachment; filename="{deck.path.name}"'
    return response


@app.get("/asset/<deck_id>/<card_id>/<path:filename>")
def asset(deck_id: str, card_id: str, filename: str):
    deck = get_deck(deck_id)
    found = load_embedded_asset(deck, card_id, filename)
    if found is None:
        abort(404)
    media_type, data = found
    response = make_response(data)
    response.headers["Content-Type"] = media_type
    response.headers["Cache-Control"] = "private, max-age=3600"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/preview")
def preview():
    url = request.args.get("url", "")
    try:
        result = fetch_link_preview(url)
        return {
            "url": result.url, "title": result.title, "description": result.description,
            "image_url": result.image_url, "site_name": result.site_name,
        }
    except Exception as exc:
        return {"error": str(exc)}, 400


def markdown_filter(value: str, deck: Deck, card_id: str) -> str:
    return render_rich_markdown(value, deck, card_id)


app.jinja_env.filters["rich_markdown"] = markdown_filter
app.jinja_env.filters["plain_speech"] = plain_speech_text
app.jinja_env.filters["local_time"] = format_local
app.jinja_env.filters["url_host"] = lambda value: urlparse(value).hostname or value
app.jinja_env.globals["next_card_id"] = next_card_id


if __name__ == "__main__":
    app.run(host=os.environ.get("FLASK_HOST", "127.0.0.1"), port=int(os.environ.get("FLASK_PORT", "5000")), debug=False)
