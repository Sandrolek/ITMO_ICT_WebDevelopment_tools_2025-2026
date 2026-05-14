from __future__ import annotations

from html.parser import HTMLParser


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._inside_title = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag.lower() == "title":
            self._inside_title = True

    def handle_endtag(self, tag: str):
        if tag.lower() == "title":
            self._inside_title = False

    def handle_data(self, data: str):
        if self._inside_title:
            self._parts.append(data)

    @property
    def title(self) -> str:
        title = " ".join(part.strip() for part in self._parts if part.strip())
        return " ".join(title.split()) or "<no title>"


def extract_title(html: str) -> str:
    parser = TitleParser()
    parser.feed(html)
    return parser.title
