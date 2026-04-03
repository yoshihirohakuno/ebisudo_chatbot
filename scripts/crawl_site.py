import argparse
import json
import re
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


DEFAULT_BASE_URL = "https://www.ebisudo.co.jp/"
SKIP_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".pdf",
    ".zip",
    ".mp4",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
)


def is_same_site(url: str, base_netloc: str) -> bool:
    return urlparse(url).netloc == base_netloc


def is_html_page(url: str) -> bool:
    return not urlparse(url).path.lower().endswith(SKIP_EXTENSIONS)


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    clean_path = parsed.path or "/"
    if clean_path != "/" and clean_path.endswith("/"):
        clean_path = clean_path[:-1]
    return parsed._replace(fragment="", query="", path=clean_path).geturl()


def clean_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    for selector in [
        "header",
        "footer",
        "nav",
        "aside",
        "form",
        ".header",
        ".footer",
        ".nav",
        ".menu",
        ".breadcrumb",
        "#header",
        "#footer",
        "#nav",
    ]:
        for element in soup.select(selector):
            element.decompose()

    for element in soup.find_all(attrs={"role": re.compile("navigation|banner|contentinfo")}):
        element.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text(" ", strip=True)

    body = soup.body or soup
    text = body.get_text("\n", strip=True)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()

    return title, text


def build_public_anchor_map(soup: BeautifulSoup) -> dict[str, str]:
    anchor_map: dict[str, str] = {}

    for nav_link in soup.select(".nav.original-nav a[href^='#_']"):
        href = nav_link.get("href", "").strip()
        text = nav_link.get_text(" ", strip=True)
        if href:
            anchor_map[href] = text

    return anchor_map


def build_section_records(html: str, page_url: str, page_title: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    section_records: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str]] = set()
    public_anchor_map = build_public_anchor_map(soup)

    candidates = soup.select("li.slide[id], section[id], div[id^='section-']")

    for index, element in enumerate(candidates, start=1):
        section_id = element.get("id", "").strip()
        heading = element.find(["h1", "h2", "h3", "h4"])
        section_title = heading.get_text(" ", strip=True) if heading else ""
        section_text = element.get_text("\n", strip=True)
        section_text = re.sub(r"\n{2,}", "\n", section_text)
        section_text = re.sub(r"[ \t]{2,}", " ", section_text).strip()
        public_anchor = f"#_{index}"
        nav_title = public_anchor_map.get(public_anchor, "")

        if not section_text and not section_title and not nav_title:
            continue
        if section_title in {"Cookie Policy", "地図"}:
            continue

        canonical_title = section_title or nav_title
        if nav_title and nav_title not in section_text:
            section_text = f"{nav_title}\n{section_text}".strip()
        if canonical_title and canonical_title not in section_text:
            section_text = f"{canonical_title}\n{section_text}".strip()

        if not section_text and canonical_title:
            section_text = canonical_title

        if len(section_text) < 18 and not canonical_title:
            continue

        public_url = f"{page_url}{public_anchor}"
        record_title = f"{page_title} | {canonical_title}" if canonical_title else page_title
        key = (record_title, section_text[:160])
        if key in seen_keys:
            continue
        seen_keys.add(key)

        section_records.append(
            {
                "title": record_title,
                "url": public_url,
                "content": section_text,
            }
        )

    return section_records


def extract_links(html: str, current_url: str, base_netloc: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []

    for anchor in soup.find_all("a", href=True):
        absolute_url = normalize_url(urljoin(current_url, anchor["href"]))
        if not absolute_url.startswith("http"):
            continue
        if not is_same_site(absolute_url, base_netloc):
            continue
        if not is_html_page(absolute_url):
            continue
        links.append(absolute_url)

    return links


def crawl(base_url: str, max_pages: int, delay: float) -> list[dict[str, str]]:
    normalized_base_url = normalize_url(base_url)
    base_netloc = urlparse(normalized_base_url).netloc
    queue = deque([normalized_base_url])
    visited: set[str] = set()
    pages: list[dict[str, str]] = []
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; EbisudoChatBot/1.0; +https://www.ebisudo.co.jp/)"
        }
    )

    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            response = session.get(url, timeout=20)
            response.raise_for_status()
            if "text/html" not in response.headers.get("Content-Type", ""):
                continue
        except requests.RequestException as error:
            print(f"skip: {url} ({error})")
            continue

        title, text = clean_text(response.text)
        if text:
            pages.append({"title": title, "url": url, "content": text})
            print(f"saved: {url}")
            for section_record in build_section_records(response.text, url, title):
                pages.append(section_record)
                print(f"saved section: {section_record['url']}")

        for link in extract_links(response.text, url, base_netloc):
            if link not in visited:
                queue.append(link)

        time.sleep(delay)

    return pages


def save_pages(output_path: Path, base_url: str, pages: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "base_url": base_url,
        "page_count": len(pages),
        "pages": pages,
    }
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="えびす堂サイトを巡回して本文を保存します。")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--output", default="data/site_pages.json")
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    pages = crawl(args.base_url, args.max_pages, args.delay)
    save_pages(Path(args.output), args.base_url, pages)
    print(f"done: {len(pages)} pages -> {args.output}")


if __name__ == "__main__":
    main()
