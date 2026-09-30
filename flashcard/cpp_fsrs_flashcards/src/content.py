from __future__ import annotations

import base64
import html
import ipaddress
import json
import re
import socket
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests
import streamlit as st

from .storage import Deck, load_embedded_asset


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


def _asset_data_url(deck: Deck, card_id: str, filename: str) -> str | None:
    asset = load_embedded_asset(deck, card_id, filename)
    if asset is None:
        return None
    mime_type, data = asset
    return f"data:{mime_type};base64,{base64.b64encode(data).decode('ascii')}"


def _resolve_images(markdown: str, deck: Deck, card_id: str) -> str:
    def replace(match: re.Match[str]) -> str:
        url = _asset_data_url(deck, card_id, match.group("name"))
        if url is None:
            return f"*Missing image: `{match.group('name')}`*"
        return f"![{match.group('alt')}]({url})"

    return ASSET_IMAGE_PATTERN.sub(replace, markdown)


def _render_mermaid(source: str) -> None:
    escaped = html.escape(source.strip())
    document = f"""
    <!doctype html><html><head><meta charset="utf-8"><style>
      html,body{{margin:0;background:#10242d;color:#e8f3f3}}
      body{{padding:18px;font-family:Inter,system-ui,sans-serif}}
      .frame{{border:1px solid #2c5663;border-radius:14px;padding:18px;overflow:auto}}
      .mermaid{{display:flex;justify-content:center;min-height:80px}}
      #fallback{{display:none;color:#f4ba68;white-space:pre-wrap;font-family:monospace}}
    </style></head><body><div class="frame"><pre class="mermaid">{escaped}</pre>
    <div id="fallback"></div></div><script type="module">
    try {{
      const module=await import('https://cdn.jsdelivr.net/npm/mermaid@12/dist/mermaid.esm.min.mjs');
      const mermaid=module.default;
      mermaid.initialize({{startOnLoad:false,securityLevel:'strict',theme:'dark'}});
      await mermaid.run({{nodes:document.querySelectorAll('.mermaid')}});
    }} catch(error) {{
      document.querySelector('.mermaid').style.display='none';
      const fallback=document.getElementById('fallback'); fallback.style.display='block';
      fallback.textContent='Diagram preview unavailable.\n\n'+{json.dumps(source)};
    }}
    </script></body></html>
    """
    st.iframe(document, height=430, width="stretch", tab_index=-1)


def render_rich_markdown(markdown: str, deck: Deck, card_id: str) -> None:
    position = 0
    for match in MERMAID_PATTERN.finditer(markdown):
        before = markdown[position : match.start()].strip()
        if before:
            st.markdown(_resolve_images(before, deck, card_id))
        _render_mermaid(match.group("diagram"))
        position = match.end()
    after = markdown[position:].strip()
    if after:
        st.markdown(_resolve_images(after, deck, card_id))


def _plain_speech_text(markdown: str) -> str:
    text = MERMAID_PATTERN.sub(" diagram omitted ", markdown)
    text = re.sub(r"```.*?```", " code example omitted ", text, flags=re.DOTALL)
    text = re.sub(r"!\[([^\]]*)\]\([^\)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", text)
    text = re.sub(r"[`*_>#~-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def render_speech_control(markdown: str, label: str, *, autoplay: bool = False) -> None:
    text = json.dumps(_plain_speech_text(markdown), ensure_ascii=False).replace("<", "\\u003c")
    document = f"""
    <!doctype html><html><head><style>
      html,body{{margin:0;background:transparent;font-family:Inter,system-ui,sans-serif}}
      .row{{display:flex;gap:8px}}button{{border:1px solid #2c5663;border-radius:9px;
      background:#10242d;color:#e8f3f3;padding:9px 13px;cursor:pointer;font-weight:700}}
    </style></head><body><div class="row"><button id="speak">🔊 {html.escape(label)}</button>
    <button id="stop">Stop</button></div><script>
      const text={text}; const speak=()=>{{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);
      u.rate=.95;speechSynthesis.speak(u)}};
      document.getElementById('speak').onclick=speak;
      document.getElementById('stop').onclick=()=>speechSynthesis.cancel();
      if({str(autoplay).lower()}) speak();
    </script></body></html>
    """
    st.iframe(document, height=54, width="stretch", tab_index=0)


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
        title.strip() or parsed.hostname or current,
        description[:500],
        urljoin(current, image) if image else None,
        parser.metadata.get("og:site_name"),
    )
