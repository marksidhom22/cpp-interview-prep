# Recall Studio

A local, single-user Flask spaced-repetition application built with FSRS-6. Every deck is one human-readable YAML file containing its settings, Markdown cards, links, embedded images, scheduling state, and review history. There is no separate database.

## Capabilities

- Create, edit, switch, export, import, and remove decks.
- Configure desired retention, daily new-card limits, timezone, and maximum interval per deck.
- Add, search, preview, edit, and remove cards.
- Write questions and answers in Markdown, including code, tables, and links.
- Upload PNG, JPEG, WebP, and GIF images into a card.
- Display remote images when an internet connection is available.
- Render fenced Mermaid diagrams.
- Fetch guarded metadata previews for public website links.
- Read questions and answers aloud with the browser's speech engine, with optional auto-read.
- Prioritize due reviews before new cards and preserve every rating event.
- Reset one deck's study timing and review history without changing its cards.
- View per-deck statistics and recent review history.

## First setup on Windows

From this directory:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

After setup, launch it with:

```powershell
.\run.ps1
```

Progress is stored inside the corresponding file in `decks/`.

## Raspberry Pi (32-bit) deployment

Use Raspberry Pi OS Lite 32-bit with Python 3.10 or newer. FSRS 6 requires Python 3.10+, and a 32-bit image may need to compile some packages during installation. Check the Pi before installing:

```bash
uname -m
getconf LONG_BIT
python3 --version
```

`getconf LONG_BIT` must print `32`, and `python3 --version` must be at least `3.10`. If your OS provides an older Python, install a current 32-bit Raspberry Pi OS image or install Python 3.10+ alongside the system Python; do not replace the OS-managed interpreter.

Install the prerequisites and clone the repository:

```bash
sudo apt update
sudo apt install --yes git python3 python3-venv python3-pip python3-dev build-essential libyaml-dev openssl
sudo useradd --system --home-dir /var/lib/recall-studio --create-home --shell /usr/sbin/nologin recall
sudo git clone https://github.com/marksidhom22/cpp-interview-prep.git /opt/recall-studio
cd /opt/recall-studio/flashcard/cpp_fsrs_flashcards
sudo python3 -m venv .venv
sudo .venv/bin/python -m pip install --upgrade pip
sudo .venv/bin/python -m pip install -r requirements.txt
```

Keep mutable deck data outside the checkout so code updates cannot overwrite study progress. Run this copy only on the first install; do not repeat it when upgrading:

```bash
sudo install -d -o recall -g recall /var/lib/recall-studio/decks
sudo cp -a decks/. /var/lib/recall-studio/decks/
sudo chown -R recall:recall /var/lib/recall-studio
sudo sh -c 'umask 077; printf "FLASHCARDS_SECRET_KEY=%s\nFLASHCARDS_DECKS_DIR=/var/lib/recall-studio/decks\n" "$(openssl rand -hex 32)" > /etc/recall-studio.env'
```

Install and start the provided production service. It runs Waitress as an unprivileged user and listens only on loopback:

```bash
sudo cp deploy/recall-studio.service /etc/systemd/system/recall-studio.service
sudo systemctl daemon-reload
sudo systemctl enable --now recall-studio
sudo systemctl status recall-studio
```

To inspect logs, use `sudo journalctl -u recall-studio -f`. For updates, pull the repository, reinstall requirements, and restart the service:

```bash
sudo git -C /opt/recall-studio pull --ff-only
sudo /opt/recall-studio/flashcard/cpp_fsrs_flashcards/.venv/bin/python -m pip install -r /opt/recall-studio/flashcard/cpp_fsrs_flashcards/requirements.txt
sudo systemctl restart recall-studio
```

### Private remote access

The app has no user login, so do not expose port 5000 to the internet, add a router port-forward, or change its listener to `0.0.0.0`. For secure access away from home, install Tailscale on the Pi and your client device, put them in a private tailnet, and restrict SSH access to your own devices. Enable SSH on the Pi and use SSH key authentication:

```bash
sudo systemctl enable --now ssh
```

From your client, open an SSH tunnel using the Pi's Tailscale name or IP (replace `pi-user` and `raspberrypi` with your account and Pi name):

```bash
ssh -N -L 5000:127.0.0.1:5000 pi-user@raspberrypi
```

Keep that command running and browse to <http://127.0.0.1:5000> on the client. Stop the tunnel with Ctrl+C. The app remains bound to Pi loopback; only the authenticated SSH connection carries remote traffic.

To run manually for a local test instead of installing the service, activate the same virtual environment and run `python app.py`. The default listener is `127.0.0.1:5000`; `FLASK_HOST`, `FLASK_PORT`, and `FLASK_THREADS` can override it.

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

The local server listens at <http://127.0.0.1:5000>. Set `FLASK_HOST`, `FLASK_PORT`, or `FLASHCARDS_SECRET_KEY` to override its bind address, port, or session signing key.
