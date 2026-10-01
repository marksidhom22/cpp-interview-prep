# Recall Studio

A local, single-user spaced-repetition application built with Streamlit and FSRS-6. Every deck is one human-readable YAML file containing its settings, Markdown cards, links, embedded images, scheduling state, and review history. There is no separate database.

The included **C++ Interview Flashcards** deck contains 171 cards.

## Capabilities

- Create, edit, switch, export, import, and remove decks.
- Configure desired retention, daily new-card limits, timezone, and maximum interval per deck.
- Add, search, preview, edit, and remove cards, including editing or deleting the current card without leaving Study.
- Write questions and answers in Markdown, including code, tables, and links.
- Upload PNG, JPEG, WebP, and GIF images into a card.
- Display remote images when an internet connection is available.
- Render fenced Mermaid diagrams such as ` ```mermaid ` blocks.
- Fetch guarded title/description/image previews for public website links.
- Read questions and answers aloud with a single Read/Stop toggle button.
- Optionally auto-read each question and revealed answer.
- Prioritize due reviews before new cards.
- Preserve every Again, Hard, Good, and Easy review event.
- Reset one deck's study timing and history without changing its cards.
- View per-deck statistics and recent review history.

## First setup on Windows

From this directory:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

After setup, launch it with:

```powershell
.\run.ps1
```

Progress is stored inside the corresponding file in `decks/`.

## Library layout

```text
decks/
├── cpp-interview.deck.yaml
├── algorithms.deck.yaml
└── ... exactly one file per deck

src/
├── storage.py   # deck files, cards, images, and progress
├── study.py     # FSRS scheduling and card selection
└── content.py   # Markdown, Mermaid, speech, and link previews
```

Each deck file is completely portable. Use **Decks → Export deck file** to back it up or move it to another Recall Studio installation; its study progress travels with it.

When upgrading from the older SQLite-based version, the application migrates `data/progress.db` into the matching deck files once, verifies the card states, and removes the obsolete database.

## Deck file format

```yaml
format_version: 1
id: cpp-ownership
title: C++ Ownership
description: Ownership and lifetime practice
study_settings:
  desired_retention: 0.9
  new_cards_per_day: 12
  timezone_name: America/Los_Angeles
  maximum_interval_days: 3650
cards:
  - id: card-0001
    topic: Ownership
    question: Where does a `unique_ptr` live?
    answer: The smart pointer can have automatic storage while its pointee has dynamic storage.
    tags: [cpp, lifetime]
    links: [https://example.com/reference]
assets: {}
study_progress:
  card_states:
    card-0001:
      introduced_at: '2026-09-30T17:00:00+00:00'
      last_review: '2026-09-30T17:01:00+00:00'
      due: '2026-10-01T17:01:00+00:00'
      fsrs:
        card_id: 123456789
        state: 2
        step: null
        stability: 1.0
        difficulty: 5.0
        due: '2026-10-01T17:01:00+00:00'
        last_review: '2026-09-30T17:01:00+00:00'
  reviews:
    - card_id: card-0001
      reviewed_at: '2026-09-30T17:01:00+00:00'
      rating: Good
      scheduled_due: '2026-10-01T17:01:00+00:00'
      duration_ms: 1800
```

Questions and answers accept Markdown. Card IDs are permanent: editing wording does not reset review history. Uploaded images are represented as base64 YAML binary values because image bytes are not text; all other deck and progress data remains ordinary readable YAML.

## Mermaid diagrams

Add a fenced Mermaid block to either side of a card:

````markdown
```mermaid
flowchart LR
    Question --> Recall --> Reveal --> Rating
```
````

Mermaid rendering loads the official browser module from its CDN, so diagram previews require an internet connection. The source remains visible and editable offline.

## Images

The editor embeds uploaded image bytes in the same deck file and inserts an asset reference such as:

```markdown
![object lifetime](asset://object-lifetime.png)
```

It can also insert a normal remote image:

```markdown
![reference](https://example.com/image.png)
```

Remote images and website metadata previews require internet access.

## Refresh the bundled C++ deck

```powershell
.venv\Scripts\python.exe scripts\import_deck.py ..\..\cpp_flashcards_00_to_12.md
```

The importer requires exactly 171 unique cards before writing.

## Generate topic-specific decks

```powershell
.venv\Scripts\python.exe scripts\split_deck_by_topic.py
```

This creates 13 expanded, topic-specific deck files beside the original deck. Each topic deck has independent review progress; the original deck is left unchanged.

## Checks

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Use **Decks → Reset study progress** to start one deck from scratch while keeping its content. The action requires typing `RESET` and removes only that deck's FSRS timing and review history.
