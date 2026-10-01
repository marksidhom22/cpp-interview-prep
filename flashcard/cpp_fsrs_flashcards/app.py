from __future__ import annotations

import html
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import streamlit as st
from fsrs import Scheduler

from src.content import LinkPreview, fetch_link_preview, render_rich_markdown, render_speech_control
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
    migrate_legacy_progress,
    next_card_id,
    save_card,
    save_uploaded_image,
    update_deck,
)
from src.study import RATING_BY_NAME, SessionCard, build_scheduler, choose_next_card, new_fsrs_card


st.set_page_config(
    page_title="Recall Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    :root {
        --ink: #07151c; --panel: #10242d; --panel-strong: #15313b;
        --line: #244551; --mint: #46d8c1; --cyan: #55bde8;
        --text: #e8f3f3; --muted: #9bb2b8; --amber: #f4ba68;
    }
    .stApp {
        background: radial-gradient(circle at 86% -8%, rgba(70,216,193,.10), transparent 34rem),
                    linear-gradient(180deg, #07151c 0%, #091920 100%);
    }
    .block-container { max-width: 1120px; padding-top: 3rem; padding-bottom: 5rem; }
    [data-testid="stSidebar"] { background: #0b1c24; border-right: 1px solid var(--line); }
    h1, h2, h3 { letter-spacing: -.025em; }
    .app-kicker { color: var(--mint); font-size: .78rem; font-weight: 800;
                  letter-spacing: .16em; text-transform: uppercase; margin-bottom: .35rem; }
    .app-title { color: var(--text); font-size: clamp(2.2rem, 6vw, 3.7rem);
                 font-weight: 760; letter-spacing: -.055em; line-height: .98; margin: 0 0 .55rem; }
    .app-subtitle { color: var(--muted); font-size: 1rem; margin-bottom: 1.25rem; }
    .card-meta { color: var(--mint); font-size: .78rem; font-weight: 800;
                 letter-spacing: .11em; text-transform: uppercase; margin-bottom: .8rem; }
    .answer-label { color: var(--mint); font-size: .78rem; font-weight: 800;
                    letter-spacing: .12em; text-transform: uppercase; margin: .4rem 0 .8rem; }
    .muted { color: var(--muted); }
    .link-card { border: 1px solid var(--line); border-radius: 12px; padding: 1rem;
                 background: rgba(16,36,45,.75); margin: .5rem 0; }
    .link-host { color: var(--mint); font-size: .78rem; font-weight: 750;
                 letter-spacing: .08em; text-transform: uppercase; }
    div[data-testid="stMetric"] { background: rgba(16,36,45,.8); border: 1px solid var(--line);
                                  border-radius: 12px; padding: .8rem 1rem; }
    div[data-testid="stMetricLabel"] { color: var(--muted); }
    div[data-testid="stMetricValue"] { color: var(--text); }
    .stButton > button, .stDownloadButton > button { min-height: 2.8rem; border-radius: 10px; font-weight: 700; }
    .session-done { text-align: center; padding: 3rem 1rem; border: 1px solid var(--line);
                    border-radius: 18px; background: rgba(16,36,45,.72); }
    .session-done-mark { color: var(--mint); font-size: 2.5rem; font-weight: 800; }
    code { color: #8de8d8; }
    @media (max-width: 640px) { .block-container { padding-top: 2.3rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def legacy_database_path() -> Path:
    override = os.environ.get("FLASHCARDS_DB_PATH") or os.environ.get("CPP_FLASHCARDS_DB_PATH")
    return Path(override) if override else Path(__file__).resolve().parent / "data" / "progress.db"


def decks_path() -> Path:
    override = os.environ.get("FLASHCARDS_DECKS_DIR")
    return Path(override) if override else CONFIG.decks_directory


def format_local(value: datetime, timezone_name: str) -> str:
    local = value.astimezone(ZoneInfo(timezone_name))
    return local.strftime("%b %d, %I:%M %p").replace(" 0", " ")


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


def page_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(f'<div class="app-kicker">{html.escape(kicker)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="app-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="app-subtitle">{html.escape(subtitle)}</div>', unsafe_allow_html=True)


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
        "study_deck_id",
        "current_card_id",
        "current_card_kind",
        "answer_revealed",
        "card_started_at",
        "editing_study_card_id",
        "deleting_study_card_id",
    ):
        st.session_state.pop(key, None)


def clear_deck_session_state(deck_id: str) -> None:
    clear_study_state()
    prefixes = (f"question-spoken:{deck_id}:", f"answer-spoken:{deck_id}:")
    for key in list(st.session_state):
        if key.startswith(prefixes):
            st.session_state.pop(key, None)


def valid_web_urls(raw: str) -> list[str]:
    urls: list[str] = []
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


@st.cache_data(ttl=3600, show_spinner=False)
def cached_link_preview(url: str) -> LinkPreview:
    return fetch_link_preview(url)


def render_link_previews(links: tuple[str, ...]) -> None:
    if not links:
        return
    st.markdown("#### Links")
    for url in links:
        try:
            preview = cached_link_preview(url)
            with st.container(border=True):
                if preview.site_name:
                    st.caption(preview.site_name)
                st.markdown(f"**{preview.title}**")
                if preview.description:
                    st.caption(preview.description)
                if preview.image_url:
                    st.image(preview.image_url, width=220)
                st.link_button("Open website", preview.url)
        except Exception as exc:
            with st.container(border=True):
                st.markdown(f"**{urlparse(url).hostname or url}**")
                st.caption(f"Preview unavailable: {exc}")
                st.link_button("Open website", url)


def render_question(deck: Deck, card: StudyCard, *, autoplay: bool) -> None:
    with st.container(border=True):
        st.markdown(
            f'<div class="card-meta">{html.escape(card.card_id)} · {html.escape(card.topic)}</div>',
            unsafe_allow_html=True,
        )
        render_rich_markdown(card.question, deck, card.card_id)
        render_speech_control(card.question, "Read question", autoplay=autoplay)


def render_answer(deck: Deck, card: StudyCard, *, autoplay: bool) -> None:
    st.markdown('<div class="answer-label">Answer</div>', unsafe_allow_html=True)
    with st.container(border=True):
        render_rich_markdown(card.answer, deck, card.card_id)
        render_speech_control(card.answer, "Read answer", autoplay=autoplay)
    render_link_previews(card.links)


def select_and_introduce(
    deck: Deck,
    cards: list[StudyCard],
    repository: ProgressRepository,
    now: datetime,
) -> SessionCard | None:
    selected = choose_next_card(cards, repository, deck, CONFIG, now)
    if selected and selected.kind == "New":
        repository.introduce(
            selected.card.card_id,
            new_fsrs_card(deck.deck_id, selected.card.card_id, now),
            now,
        )
    return selected


def render_study_page(deck: Deck, cards: list[StudyCard], repository: ProgressRepository) -> None:
    page_header("Adaptive review", deck.title, "Answer from memory, reveal, then rate your recall.")
    if message := st.session_state.pop("study_card_saved_message", None):
        st.success(message)
    if not cards:
        st.info("This deck has no cards yet.")
        if st.button("Add the first card", type="primary"):
            st.session_state.navigation = "Cards"
            st.session_state.card_workspace_tab = "Add card"
            st.rerun()
        return

    now = utc_now()
    scheduler = build_scheduler(deck, CONFIG)
    if st.session_state.get("study_deck_id") != deck.deck_id:
        clear_study_state()
        st.session_state.study_deck_id = deck.deck_id

    selected: SessionCard | None = None
    current_id = st.session_state.get("current_card_id")
    if current_id:
        current = next((card for card in cards if card.card_id == current_id), None)
        if current:
            selected = SessionCard(current, st.session_state.get("current_card_kind", "Review"))
        else:
            clear_study_state()
            st.session_state.study_deck_id = deck.deck_id

    if selected is None:
        selected = select_and_introduce(deck, cards, repository, now)
        if selected:
            st.session_state.current_card_id = selected.card.card_id
            st.session_state.current_card_kind = selected.kind
            st.session_state.answer_revealed = False
            st.session_state.card_started_at = time.monotonic()

    if result := st.session_state.pop("last_result", None):
        st.toast(
            f"{result['card_id']} · {result['rating']} · next in {result['interval']}",
            icon="✅",
        )

    if selected is None:
        next_due = repository.next_due(now)
        message = (
            f"Next review: {format_local(next_due, deck.timezone_name)}"
            if next_due
            else "Every card in this deck is complete for now."
        )
        st.markdown(
            f'<div class="session-done"><div class="session-done-mark">✓</div>'
            f'<h2>Session complete</h2><p>{html.escape(message)}</p></div>',
            unsafe_allow_html=True,
        )
        if st.button("Check for due cards", width="stretch"):
            st.rerun()
        return

    card = selected.card
    progress = repository.get(card.card_id)
    if progress is None:
        st.error(f"Progress state is missing for card {card.card_id}.")
        return

    auto_read = bool(st.session_state.get("auto_read", False))
    question_spoken_key = f"question-spoken:{deck.deck_id}:{card.card_id}"
    question_autoplay = auto_read and not st.session_state.get(question_spoken_key, False)
    if question_autoplay:
        st.session_state[question_spoken_key] = True

    st.caption(f"{selected.kind} · {card.card_id} · {card.topic}")
    render_question(deck, card, autoplay=question_autoplay)

    editing_card_id = st.session_state.get("editing_study_card_id")
    deleting_card_id = st.session_state.get("deleting_study_card_id")
    if editing_card_id == card.card_id:
        with st.container(border=True):
            heading, action = st.columns([4, 1])
            heading.markdown("### Edit this card")
            if action.button(
                "Cancel",
                key=f"cancel-study-edit:{deck.deck_id}:{card.card_id}",
                width="stretch",
            ):
                st.session_state.pop("editing_study_card_id", None)
                st.rerun()
            st.caption(
                "Saving changes the card content only. Its review timing, history, and "
                "position in this study session stay unchanged."
            )
            card_form(
                deck,
                cards,
                card,
                form_context="study",
                preserve_study=True,
            )
    elif deleting_card_id == card.card_id:
        with st.container(border=True):
            st.markdown("### Delete this card?")
            st.warning(
                "This removes the card, its study timing and review history, and any "
                "images uploaded specifically for it. This cannot be undone in the app."
            )
            confirmed = st.checkbox(
                f"I want to permanently delete {card.card_id}",
                key=f"confirm-study-delete:{deck.deck_id}:{card.card_id}",
            )
            cancel, remove = st.columns(2)
            if cancel.button(
                "Cancel",
                key=f"cancel-study-delete:{deck.deck_id}:{card.card_id}",
                width="stretch",
            ):
                st.session_state.pop("deleting_study_card_id", None)
                st.rerun()
            if remove.button(
                "Delete permanently",
                key=f"delete-study-card:{deck.deck_id}:{card.card_id}",
                type="primary",
                disabled=not confirmed,
                width="stretch",
            ):
                deleted_card_id = card.card_id
                delete_card(deck, card)
                clear_study_state()
                st.session_state.study_card_saved_message = (
                    f"Deleted {deleted_card_id}. Its study history was also removed."
                )
                st.rerun()
    else:
        edit_action, delete_action = st.columns(2)
        if edit_action.button(
            "Edit this card",
            key=f"edit-study-card:{deck.deck_id}:{card.card_id}",
            icon="✏️",
            width="stretch",
        ):
            st.session_state.editing_study_card_id = card.card_id
            st.rerun()
        if delete_action.button(
            "Delete this card",
            key=f"start-delete-study-card:{deck.deck_id}:{card.card_id}",
            width="stretch",
        ):
            st.session_state.deleting_study_card_id = card.card_id
            st.rerun()

    if not st.session_state.get("answer_revealed", False):
        if st.button("Reveal answer", type="primary", width="stretch"):
            st.session_state.answer_revealed = True
            st.rerun()
        st.caption("State the rule, the reason, and one relevant example before revealing.")
        return

    answer_spoken_key = f"answer-spoken:{deck.deck_id}:{card.card_id}"
    answer_autoplay = auto_read and not st.session_state.get(answer_spoken_key, False)
    if answer_autoplay:
        st.session_state[answer_spoken_key] = True
    render_answer(deck, card, autoplay=answer_autoplay)

    rating_now = utc_now()
    no_fuzz = preview_scheduler(deck)
    interval_by_rating: dict[str, str] = {}
    for name, rating in RATING_BY_NAME.items():
        preview, _ = no_fuzz.review_card(progress.fsrs_card, rating, review_datetime=rating_now)
        interval_by_rating[name] = format_interval(preview.due, rating_now)

    st.caption("Rate what you recalled before seeing the answer—not how familiar it looks now.")
    columns = st.columns(4)
    rating_help = {
        "Again": "The core answer was missing or wrong.",
        "Hard": "Partial recall; an important rule or reason was missing.",
        "Good": "Substantially correct after some thought.",
        "Easy": "Immediate, complete, and well reasoned.",
    }
    for column, name in zip(columns, ("Again", "Hard", "Good", "Easy")):
        with column:
            clicked = st.button(
                f"{name}\n\n{interval_by_rating[name]}",
                key=f"rate:{deck.deck_id}:{card.card_id}:{name}",
                type="primary" if name == "Good" else "secondary",
                help=rating_help[name],
                width="stretch",
            )
        if clicked:
            review_time = utc_now()
            duration_ms = max(
                0,
                int((time.monotonic() - st.session_state.get("card_started_at", time.monotonic())) * 1000),
            )
            updated_card, review_log = scheduler.review_card(
                progress.fsrs_card,
                RATING_BY_NAME[name],
                review_datetime=review_time,
                review_duration=duration_ms,
            )
            repository.record_review(card.card_id, updated_card, review_log, duration_ms)
            st.session_state.last_result = {
                "card_id": card.card_id,
                "rating": name,
                "interval": format_interval(updated_card.due, review_time),
            }
            clear_study_state()
            st.session_state.study_deck_id = deck.deck_id
            st.rerun()

    with st.expander("Memory details"):
        memory = progress.fsrs_card
        retrievability = None
        if memory.last_review is not None and memory.stability is not None:
            retrievability = scheduler.get_card_retrievability(memory, current_datetime=rating_now)
        left, right = st.columns(2)
        left.metric("Difficulty", f"{memory.difficulty:.2f}" if memory.difficulty else "New")
        right.metric("Stability", f"{memory.stability:.1f} days" if memory.stability else "New")
        if retrievability is not None:
            st.caption(f"Estimated retrievability now · {retrievability:.1%}")
    if card.source:
        st.caption(f"Source · {card.source}")


def card_form(
    deck: Deck,
    cards: list[StudyCard],
    card: StudyCard | None = None,
    *,
    form_context: str = "cards",
    preserve_study: bool = False,
) -> None:
    editing = card is not None
    suggested_id = card.card_id if card else next_card_id(cards)
    default_topic = card.topic if card else "General"

    with st.form(
        f"card-form:{form_context}:{deck.deck_id}:{suggested_id}",
        clear_on_submit=not editing,
    ):
        first, second = st.columns([1, 2])
        card_id = first.text_input("Stable card ID", value=suggested_id, disabled=editing)
        topic = second.text_input("Topic", value=default_topic)
        question = st.text_area(
            "Question (Markdown)",
            value=card.question if card else "",
            height=170,
            placeholder="What should you be able to recall?",
        )
        answer = st.text_area(
            "Answer (Markdown)",
            value=card.answer if card else "",
            height=230,
            placeholder="Give the answer, reasoning, tradeoffs, and examples.",
        )
        tags = st.text_input(
            "Tags (comma separated)", value=", ".join(card.tags) if card else ""
        )
        links = st.text_area(
            "Website links to preview (one per line)",
            value="\n".join(card.links) if card else "",
            height=90,
        )

        with st.expander("Rich media"):
            uploads = st.file_uploader(
                "Upload images",
                type=["png", "jpg", "jpeg", "webp", "gif"],
                accept_multiple_files=True,
                key=f"{form_context}:images:{deck.deck_id}:{suggested_id}",
            )
            upload_placement = st.radio(
                "Place uploaded images in",
                ("Answer", "Question"),
                horizontal=True,
                key=f"{form_context}:upload-placement:{deck.deck_id}:{suggested_id}",
            )
            remote_images = st.text_area(
                "Remote image URLs (one per line)",
                height=80,
                key=f"{form_context}:remote-images:{deck.deck_id}:{suggested_id}",
            )
            remote_placement = st.radio(
                "Place remote images in",
                ("Answer", "Question"),
                horizontal=True,
                key=f"{form_context}:remote-placement:{deck.deck_id}:{suggested_id}",
            )
            mermaid = st.text_area(
                "Mermaid diagram source",
                height=150,
                placeholder="flowchart LR\n  A[Question] --> B[Answer]",
                key=f"{form_context}:mermaid:{deck.deck_id}:{suggested_id}",
            )
            mermaid_placement = st.radio(
                "Place Mermaid diagram in",
                ("Answer", "Question"),
                horizontal=True,
                key=f"{form_context}:mermaid-placement:{deck.deck_id}:{suggested_id}",
            )

        submitted = st.form_submit_button(
            "Save changes" if editing else "Add card", type="primary", width="stretch"
        )

    if not submitted:
        return

    try:
        if not CARD_ID_PATTERN.fullmatch(card_id.strip()):
            raise ValueError("Card ID contains unsupported characters")
        if not editing and any(item.card_id == card_id.strip() for item in cards):
            raise ValueError(f"Card ID already exists: {card_id}")
        if not question.strip() or not answer.strip():
            raise ValueError("Question and answer are required")

        question_value = question.strip()
        answer_value = answer.strip()
        parsed_links = valid_web_urls(links)
        parsed_remote_images = valid_web_urls(remote_images)

        for image_url in parsed_remote_images:
            alt = urlparse(image_url).path.rsplit("/", 1)[-1] or "Remote image"
            block = f"![{alt}]({image_url})"
            if remote_placement == "Question":
                question_value = append_block(question_value, block)
            else:
                answer_value = append_block(answer_value, block)

        if mermaid.strip():
            block = f"```mermaid\n{mermaid.strip()}\n```"
            if mermaid_placement == "Question":
                question_value = append_block(question_value, block)
            else:
                answer_value = append_block(answer_value, block)

        for upload in uploads or []:
            asset_uri = save_uploaded_image(deck, card_id.strip(), upload.name, upload.getvalue())
            block = f"![{Path(upload.name).stem}]({asset_uri})"
            if upload_placement == "Question":
                question_value = append_block(question_value, block)
            else:
                answer_value = append_block(answer_value, block)

        save_card(
            deck,
            card_id=card_id,
            topic=topic,
            question=question_value,
            answer=answer_value,
            tags=[tag.strip() for tag in tags.split(",")],
            links=parsed_links,
            source=card.source if card else None,
            existing_path=card.path if card else None,
        )
        if preserve_study:
            st.session_state.pop("editing_study_card_id", None)
            st.session_state.pop(f"question-spoken:{deck.deck_id}:{card_id.strip()}", None)
            st.session_state.pop(f"answer-spoken:{deck.deck_id}:{card_id.strip()}", None)
            st.session_state.study_card_saved_message = (
                f"Saved {card_id}. Study progress and timing were preserved."
            )
        else:
            clear_study_state()
            st.session_state.card_saved_message = f"Saved {card_id}."
        st.rerun()
    except Exception as exc:
        st.error(str(exc))


def render_cards_page(deck: Deck, cards: list[StudyCard], repository: ProgressRepository) -> None:
    page_header("Deck workspace", "Cards", f"Create and maintain the content in {deck.title}.")
    if message := st.session_state.pop("card_saved_message", None):
        st.success(message)

    browse_tab, add_tab = st.tabs(["Browse & edit", "Add card"])
    with browse_tab:
        if not cards:
            st.info("No cards yet. Use the Add card tab to create one.")
        else:
            search = st.text_input("Search cards", placeholder="ID, topic, tag, question, or answer")
            topics = ["All topics"] + sorted({card.topic for card in cards}, key=str.casefold)
            topic_filter = st.selectbox("Topic", topics)
            query = search.casefold().strip()
            filtered = [
                card
                for card in cards
                if (topic_filter == "All topics" or card.topic == topic_filter)
                and (
                    not query
                    or query
                    in " ".join(
                        (card.card_id, card.topic, card.question, card.answer, " ".join(card.tags))
                    ).casefold()
                )
            ]
            st.caption(f"{len(filtered)} of {len(cards)} cards")
            if filtered:
                selected_id = st.selectbox(
                    "Card",
                    [card.card_id for card in filtered],
                    format_func=lambda card_id: next(
                        f"{item.card_id} — {re.sub(r'[`*_#]', '', item.question)[:80]}"
                        for item in filtered
                        if item.card_id == card_id
                    ),
                )
                selected = next(card for card in filtered if card.card_id == selected_id)
                preview_tab, edit_tab, delete_tab = st.tabs(["Preview", "Edit", "Delete"])
                with preview_tab:
                    st.markdown("#### Question")
                    render_rich_markdown(selected.question, deck, selected.card_id)
                    st.markdown("#### Answer")
                    render_rich_markdown(selected.answer, deck, selected.card_id)
                    render_link_previews(selected.links)
                    if selected.tags:
                        st.caption("Tags · " + " · ".join(selected.tags))
                with edit_tab:
                    card_form(deck, cards, selected)
                with delete_tab:
                    st.warning("Deleting a card also removes its review history and uploaded images.")
                    confirm = st.checkbox(
                        f"I want to delete {selected.card_id}",
                        key=f"confirm-delete-card:{deck.deck_id}:{selected.card_id}",
                    )
                    if st.button(
                        "Delete card",
                        disabled=not confirm,
                        key=f"delete-card:{deck.deck_id}:{selected.card_id}",
                    ):
                        delete_card(deck, selected)
                        clear_study_state()
                        st.success(f"Deleted {selected.card_id}.")
                        st.rerun()
    with add_tab:
        card_form(deck, cards)


def render_decks_page(deck: Deck | None, decks: list[Deck]) -> None:
    page_header("Library", "Decks", "Create, switch, configure, import, export, or remove decks.")
    if message := st.session_state.pop("deck_message", None):
        st.success(message)

    with st.container(border=True):
        st.markdown("### Create a deck")
        with st.form("create-deck", clear_on_submit=True):
            title = st.text_input("Title", placeholder="Algorithms, Spanish verbs, anatomy…")
            description = st.text_area("Description", height=80)
            left, right = st.columns(2)
            retention = left.slider("Desired retention", 0.70, 0.99, 0.90, 0.01)
            new_per_day = right.number_input("New cards per day", 0, 500, 12)
            create_clicked = st.form_submit_button("Create deck", type="primary")
        if create_clicked:
            try:
                created = create_deck(
                    decks_path(),
                    title,
                    description,
                    desired_retention=retention,
                    new_cards_per_day=int(new_per_day),
                )
                st.session_state.pending_selected_deck_id = created.deck_id
                st.session_state.navigation = "Cards"
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with st.container(border=True):
        st.markdown("### Import a deck")
        deck_file = st.file_uploader(
            "Deck file", type=["yaml", "yml"], key="import-deck-file"
        )
        st.caption("Each .deck.yaml file contains its settings, cards, links, and embedded images.")
        if st.button("Import deck", disabled=deck_file is None):
            try:
                imported = import_deck(decks_path(), deck_file.getvalue())
                st.session_state.pending_selected_deck_id = imported.deck_id
                st.session_state.deck_message = f"Imported {imported.title}."
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if deck is None:
        return

    with st.container(border=True):
        st.markdown("### Current deck")
        st.caption(f"Stored in one file: {deck.path.name}")
        with st.form(f"edit-deck:{deck.deck_id}"):
            title = st.text_input("Title", value=deck.title)
            description = st.text_area("Description", value=deck.description, height=90)
            first, second = st.columns(2)
            retention = first.slider(
                "Desired retention", 0.70, 0.99, float(deck.desired_retention), 0.01
            )
            new_per_day = second.number_input(
                "New cards per day", 0, 500, int(deck.new_cards_per_day)
            )
            third, fourth = st.columns(2)
            timezone_name = third.text_input("Timezone", value=deck.timezone_name)
            maximum_interval = fourth.number_input(
                "Maximum interval (days)", 1, 36500, int(deck.maximum_interval_days)
            )
            update_clicked = st.form_submit_button("Save deck settings", type="primary")
        if update_clicked:
            try:
                ZoneInfo(timezone_name)
                update_deck(
                    deck,
                    title=title.strip(),
                    description=description.strip(),
                    desired_retention=float(retention),
                    new_cards_per_day=int(new_per_day),
                    timezone_name=timezone_name.strip(),
                    maximum_interval_days=int(maximum_interval),
                )
                clear_study_state()
                st.success("Deck settings saved.")
                st.rerun()
            except (ValueError, ZoneInfoNotFoundError) as exc:
                st.error(str(exc))

        st.download_button(
            "Export deck file",
            data=export_deck(deck),
            file_name=deck.path.name,
            mime="application/yaml",
            width="stretch",
        )

    with st.expander("Reset study progress"):
        repository = ProgressRepository(deck)
        introduced = repository.introduced_count()
        reviews = repository.review_count()
        st.warning(
            "This resets every card to new and permanently removes this deck's review timing "
            "and history. Cards and other deck content stay unchanged."
        )
        st.caption(f"Current progress · {introduced} introduced cards · {reviews} reviews")
        reset_confirmation = st.text_input(
            f"Type RESET to start {deck.title!r} from scratch",
            key=f"reset-deck-confirm:{deck.deck_id}",
        )
        if st.button(
            "Reset study progress",
            disabled=reset_confirmation != "RESET",
            key=f"reset-deck:{deck.deck_id}",
            type="primary",
        ):
            repository.delete_deck_progress()
            clear_deck_session_state(deck.deck_id)
            st.session_state.deck_message = (
                f"Study progress for {deck.title} was reset. Every card is new again."
            )
            st.rerun()

    with st.expander("Delete this deck"):
        st.warning("This removes the deck, its cards, uploaded images, and review history.")
        confirmation = st.text_input(
            f"Type {deck.title!r} to confirm", key=f"delete-deck-confirm:{deck.deck_id}"
        )
        if st.button(
            "Delete deck",
            disabled=confirmation != deck.title,
            key=f"delete-deck:{deck.deck_id}",
        ):
            delete_deck(deck, decks_path())
            remaining = [item for item in decks if item.deck_id != deck.deck_id]
            if remaining:
                st.session_state.pending_selected_deck_id = remaining[0].deck_id
            clear_deck_session_state(deck.deck_id)
            st.rerun()


def render_stats_page(deck: Deck, cards: list[StudyCard], repository: ProgressRepository) -> None:
    page_header("Learning signal", "Statistics", f"Progress and review history for {deck.title}.")
    now = utc_now()
    introduced = repository.introduced_count()
    reviews = repository.review_count()
    due = len(repository.due_records(now))
    first, second, third, fourth = st.columns(4)
    first.metric("Cards", len(cards))
    second.metric("Introduced", introduced)
    third.metric("Due now", due)
    fourth.metric("Reviews", reviews)

    ratings = repository.rating_counts()
    st.markdown("### Recall ratings")
    rating_names = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}
    chart_data = {rating_names[number]: ratings.get(number, 0) for number in range(1, 5)}
    st.bar_chart(chart_data, horizontal=True)

    st.markdown("### Topics")
    topic_counts = Counter(card.topic for card in cards)
    st.dataframe(
        [{"Topic": topic, "Cards": count} for topic, count in topic_counts.most_common()],
        hide_index=True,
        width="stretch",
    )

    recent = repository.recent_reviews()
    st.markdown("### Recent reviews")
    if recent:
        st.dataframe(
            [
                {
                    "Card": review.card_id,
                    "Rating": rating_names[review.rating],
                    "Reviewed": format_local(review.reviewed_at, deck.timezone_name),
                    "Next due": format_local(review.scheduled_due, deck.timezone_name),
                }
                for review in recent
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No reviews recorded yet.")


try:
    decks = list_decks(decks_path())
    migrated_states, migrated_reviews = migrate_legacy_progress(legacy_database_path(), decks)
    if migrated_states or migrated_reviews:
        st.session_state.deck_message = (
            f"Moved {migrated_states} card states and {migrated_reviews} reviews into the deck files."
        )
except Exception as exc:
    st.error(f"Could not load the deck library: {exc}")
    st.stop()

deck_by_id = {deck.deck_id: deck for deck in decks}
pending_selected_id = st.session_state.pop("pending_selected_deck_id", None)
selected_id = pending_selected_id or st.session_state.get("selected_deck_id")
if selected_id not in deck_by_id:
    selected_id = decks[0].deck_id if decks else None
if st.session_state.get("selected_deck_id") != selected_id:
    st.session_state.selected_deck_id = selected_id

deck_views = ("Study", "Cards", "Statistics")
navigation = st.session_state.get("navigation", "Study")
if navigation not in (*deck_views, "Decks"):
    navigation = "Study"
    st.session_state.navigation = navigation

with st.sidebar:
    st.markdown("## Recall Studio")
    if decks:
        st.caption("CURRENT DECK")
        selected_id = st.selectbox(
            "Current deck",
            [deck.deck_id for deck in decks],
            index=[deck.deck_id for deck in decks].index(selected_id),
            format_func=lambda deck_id: deck_by_id[deck_id].title,
            key="selected_deck_id",
            label_visibility="collapsed",
        )
        st.caption("DECK WORKSPACE")
        for view in deck_views:
            if st.button(
                view,
                key=f"navigate:{view}",
                type="primary" if navigation == view else "secondary",
                width="stretch",
            ):
                st.session_state.navigation = view
                st.rerun()
        st.divider()
        st.caption("LIBRARY")
        if st.button(
            "Manage decks",
            type="primary" if navigation == "Decks" else "secondary",
            width="stretch",
        ):
            st.session_state.navigation = "Decks"
            st.rerun()
    else:
        st.caption("LIBRARY")
        st.info("Create or import a deck to begin.")

    if selected_id and navigation != "Decks":
        active = deck_by_id[selected_id]
        active_cards = load_deck_cards(active)
        active_repository = ProgressRepository(active)
        if navigation == "Study":
            st.divider()
            st.toggle("Auto-read question and answer", key="auto_read")
        now = utc_now()
        due_count = len(active_repository.due_records(now))
        introduced_today = active_repository.introduced_in_local_day(now, active.timezone_name)
        st.markdown("### Today")
        left, right = st.columns(2)
        left.metric("Due", due_count)
        right.metric("New left", max(0, active.new_cards_per_day - introduced_today))
        st.progress(active_repository.introduced_count() / len(active_cards) if active_cards else 0)
        st.caption(f"{active_repository.introduced_count()} of {len(active_cards)} introduced")

if not decks:
    render_decks_page(None, [])
    st.stop()

deck = deck_by_id[selected_id]
cards = load_deck_cards(deck)
repository = ProgressRepository(deck)

navigation = st.session_state.get("navigation", "Study")
if navigation == "Study":
    render_study_page(deck, cards, repository)
elif navigation == "Cards":
    render_cards_page(deck, cards, repository)
elif navigation == "Decks":
    render_decks_page(deck, decks)
else:
    render_stats_page(deck, cards, repository)
