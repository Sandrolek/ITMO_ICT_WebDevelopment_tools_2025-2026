from __future__ import annotations

import requests

from db import init_db_sync, save_page_sync
from html_title_parser import extract_title
from web_config import USER_AGENT


def parse_and_store(url: str, parser_type: str = "http") -> dict[str, str]:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    response.raise_for_status()
    title = extract_title(response.text)
    save_page_sync(url, title, parser_type)
    return {"url": url, "title": title}


__all__ = ["parse_and_store", "init_db_sync"]
