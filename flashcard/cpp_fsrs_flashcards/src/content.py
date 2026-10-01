from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import quote, urljoin, urlparse

import bleach
import markdown
import requests

from .storage import Deck


MERMAID_PATTERN = re.compile(r"```mermaid\s*\n(?P<diagram>.*?)```", re.DOTALL | re.IGNORECASE)
ASSET_IMAGE_PATTERN = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\(asset://(?P<name>[^\)]+)\)", re.IGNORECASE
)


@dataclass(frozen=True)
class LinkPreview:
    url: str
    title: str
    description: str
    image_url: str | None
    site_name: str | None


def _resolve_images(markdown_text: str, deck: Deck, card_id: str) -> str:
    def replace(match: re.Match[str]) -> str:
        filename = match.group("name")
        asset_url = "/asset/{}/{}/{}".format(
            quote(deck.deck_id, safe=""), quote(card_id, safe=""), quote(filename, safe="")
        )
        return f"![{match.group('alt')}]({asset_url})"

    return ASSET_IMAGE_PATTERN.sub(replace, markdown_text)


def render_rich_markdown(markdown_text: str, deck: Deck, card_id: str) -> str:
    rendered = markdown.markdown(
        _resolve_images(markdown_text, deck, card_id),
        extensions=["fenced_code", "tables", "sane_lists"],
    )
    return bleach.clean(
        rendered,
        tags={
            "a", "abbr", "b", "blockquote", "br", "code", "del", "dd", "div", "dl", "dt",
            "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "li", "ol",
            "p", "pre", "s", "span", "strong", "sub", "sup", "table", "tbody", "td", "th",
            "thead", "tr", "ul",
        },
        attributes={
            "a": ["href", "title"], "img": ["src", "alt", "title"],
            "code": ["class"], "pre": ["class"], "th": ["align"], "td": ["align"],
        },
        protocols={"http", "https", "mailto"},
        strip=True,
    )


def plain_speech_text(markdown_text: str) -> str:
    text = MERMAID_PATTERN.sub(" diagram omitted ", markdown_text)
    text = re.sub(r"```.*?```", " code example omitted ", text, flags=re.DOTALL)
    text = re.sub(r"!\[([^\]]*)\]\([^\)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", text)
    text = re.sub(r"[`*_>#~-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_plain_speech_text = plain_speech_text


class _MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.in_title = False
        self.metadata: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value for key, value in attrs if value is not None}
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "meta":
            key = (values.get("property") or values.get("name") or "").lower()
            if key and values.get("content"):
                self.metadata[key] = str(values["content"]).strip()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data


def _validate_public_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only public http:// and https:// links are supported")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    except socket.gaierror as exc:
        raise ValueError("The hostname could not be resolved") from exc
    if any(not ipaddress.ip_address(address[4][0]).is_global for address in addresses):
        raise ValueError("Private and local network links cannot be previewed")
    return parsed.geturl()


def fetch_link_preview(url: str) -> LinkPreview:
    current = _validate_public_url(url)
    response: requests.Response | None = None
    for _ in range(4):
        response = requests.get(
            current,
            headers={"User-Agent": "RecallStudio/1.0"},
            timeout=(3, 5),
            stream=True,
            allow_redirects=False,
        )
        if not response.is_redirect:
            break
        location = response.headers.get("Location")
        response.close()
        if not location:
            raise ValueError("Invalid redirect")
        current = _validate_public_url(urljoin(current, location))
    else:
        raise ValueError("Too many redirects")
    assert response is not None
    try:
        response.raise_for_status()
        if "text/html" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("Preview is available only for HTML pages")
        content = bytearray()
        for chunk in response.iter_content(16 * 1024):
            content.extend(chunk)
            if len(content) >= 512 * 1024:
                break
        page = bytes(content).decode(response.encoding or "utf-8", errors="replace")
    finally:
        response.close()
    parser = _MetadataParser()
    parser.feed(page)
    title = parser.metadata.get("og:title") or parser.metadata.get("twitter:title") or parser.title
    description = (
        parser.metadata.get("og:description")
        or parser.metadata.get("twitter:description")
        or parser.metadata.get("description")
        or ""
    )
    image = parser.metadata.get("og:image") or parser.metadata.get("twitter:image")
    return LinkPreview(
        current,
        title.strip() or urlparse(current).hostname or current,
        description[:500],
        urljoin(current, image) if image else None,
        parser.metadata.get("og:site_name"),
    )
