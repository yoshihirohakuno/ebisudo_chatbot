import json
import math
import os
import re
from collections import Counter
from typing import Any


QUERY_HINTS = {
    "可変印刷": ["バリアブル印字", "データ印字", "ナンバリング", "1枚1枚を管理", "個別マーケティング"],
    "バリアブル印字": ["可変印刷", "データ印字", "1枚1枚を管理"],
    "何に使う": ["用途", "使い道", "個別マーケティング", "店舗", "乱数", "応募コード", "qrコード", "バーコード"],
    "用途": ["何に使う", "使い道", "個別マーケティング", "店舗", "乱数", "応募コード"],
    "使い道": ["何に使う", "用途", "個別マーケティング", "店舗", "乱数", "応募コード"],
    "どこ": ["所在地", "住所", "会社概要", "お問い合わせ", "荒川区", "町屋"],
    "所在地": ["住所", "会社概要", "お問い合わせ", "荒川区", "町屋"],
    "住所": ["所在地", "会社概要", "お問い合わせ", "荒川区", "町屋"],
    "会社": ["会社概要", "所在地", "住所"],
    "事業内容": ["事業", "事業目的", "サービス", "可変印刷", "バリアブル印字", "ナンバリング", "データ処理"],
    "事業": ["事業目的", "サービス", "可変印刷", "バリアブル印字", "ナンバリング", "データ処理"],
    "サービス": ["可変印刷", "バリアブル印字", "ナンバリング", "乱数", "qrコード", "データ処理"],
    "事例": ["事例紹介", "詳細", "導入事例"],
    "実績": ["事例紹介", "詳細", "実績"],
    "会社概要": ["所在地", "資本金", "創業", "役員構成"],
    "代表者": ["代表取締役", "会社概要", "役員構成"],
    "代表取締役": ["代表者", "会社概要", "役員構成"],
    "社長": ["代表取締役", "代表者", "会社概要"],
    "役員": ["役員構成", "代表取締役", "会社概要"],
    "個人情報": ["個人情報保護方針", "個人情報ファイル", "保護方針"],
    "プライバシー": ["個人情報保護方針", "個人情報"],
    "チェックデジット": ["チェックデジットの種類と必要性", "チェックデジット付き番号", "7dr", "9dsr", "mod10", "mod11"],
    "可変バーコード": ["可変qrコード", "qrコード", "バーコード"],
    "qrコード": ["可変qrコード", "可変バーコード"],
    "乱数印字": ["乱数作成", "乱数販売", "メルセンヌ", "重複チェック"],
    "乱数": ["乱数データ作成サービス", "乱数作成", "乱数販売", "重複チェック"],
    "初心者向け": ["わかりやすく", "やさしく", "簡単に"],
}


def load_pages(data_file: str) -> list[dict[str, Any]]:
    if not os.path.exists(data_file):
        return []

    with open(data_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("pages", [])


def split_into_chunks(text: str, chunk_size: int = 420, overlap: int = 80) -> list[str]:
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[。！？\n])", text)
        if sentence.strip()
    ]

    if not sentences:
        return []

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) <= chunk_size:
            current += sentence
            continue

        if current:
            chunks.append(current.strip())
        current = current[-overlap:] + sentence if current else sentence

    if current:
        chunks.append(current.strip())

    return chunks


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    ascii_words = re.findall(r"[a-z0-9]{2,}", normalized)
    compact = re.sub(r"[^ぁ-んァ-ヶ一-龥a-z0-9]", "", normalized)
    bigrams = [compact[index : index + 2] for index in range(len(compact) - 1)]
    trigrams = [compact[index : index + 3] for index in range(len(compact) - 2)]
    return ascii_words + bigrams + trigrams


def expand_question(question: str) -> str:
    expanded_parts = [question]
    normalized = normalize_text(question)

    for keyword, hints in QUERY_HINTS.items():
        if keyword.lower() in normalized:
            expanded_parts.extend(hints)

    return " ".join(expanded_parts)


def build_search_index(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index: list[dict[str, Any]] = []

    for page in pages:
        body = page.get("content", "").strip()
        if not body:
            continue

        for chunk in split_into_chunks(body):
            tokens = tokenize(f"{page.get('title', '')} {chunk}")
            if not tokens:
                continue

            index.append(
                {
                    "title": page.get("title", ""),
                    "url": page.get("url", ""),
                    "content": chunk,
                    "token_counts": Counter(tokens),
                    "length": len(tokens),
                }
            )

    return index


def build_page_index(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index: list[dict[str, Any]] = []

    for page in pages:
        content = page.get("content", "").strip()
        if not content:
            continue

        tokens = tokenize(f"{page.get('title', '')} {content}")
        if not tokens:
            continue

        index.append(
            {
                "title": page.get("title", ""),
                "url": page.get("url", ""),
                "content": content,
                "token_counts": Counter(tokens),
                "length": len(tokens),
            }
        )

    return index


def score_chunk(question: str, chunk: dict[str, Any]) -> float:
    question_tokens = tokenize(expand_question(question))
    if not question_tokens:
        return 0.0

    question_counts = Counter(question_tokens)
    overlap = 0

    for token, count in question_counts.items():
        overlap += min(count, chunk["token_counts"].get(token, 0))

    if overlap == 0:
        return 0.0

    coverage = overlap / max(len(question_tokens), 1)
    density = overlap / max(math.sqrt(chunk["length"]), 1)
    title_bonus = 0.0
    title_tokens = tokenize(chunk["title"])
    if any(token in title_tokens for token in question_tokens):
        title_bonus = 0.7
    return coverage * 3 + density + title_bonus


def search_relevant_chunks(
    question: str,
    pages: list[dict[str, Any]],
    limit: int = 8,
) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []

    for chunk in build_search_index(pages):
        score = score_chunk(question, chunk)
        if score > 0:
            chunk_with_score = dict(chunk)
            chunk_with_score["score"] = score
            scored.append((score, chunk_with_score))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [item[1] for item in scored[:limit]]

    # 同じトップページ内の近い公開アンカーも補助資料として足す
    extra_chunks: list[dict[str, Any]] = []
    selected_urls = {chunk["url"] for chunk in selected}
    anchor_pattern = re.compile(r"#_(\d+)$")

    for chunk in selected:
        match = anchor_pattern.search(chunk["url"])
        if not match:
            continue

        anchor_number = int(match.group(1))
        neighbor_urls = {
            chunk["url"].rsplit("#_", 1)[0] + f"#_{anchor_number - 1}",
            chunk["url"].rsplit("#_", 1)[0] + f"#_{anchor_number + 1}",
        }

        for page in pages:
            if page.get("url") not in neighbor_urls:
                continue
            if page["url"] in selected_urls:
                continue

            extra_chunk = {
                "title": page.get("title", ""),
                "url": page.get("url", ""),
                "content": page.get("content", ""),
                "score": 0.2,
            }
            extra_chunks.append(extra_chunk)
            selected_urls.add(page["url"])

    return selected + extra_chunks[:3]


def search_relevant_pages(
    question: str,
    pages: list[dict[str, Any]],
    limit: int = 3,
) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []

    for page in build_page_index(pages):
        score = score_chunk(question, page)
        if score > 0:
            page_with_score = dict(page)
            page_with_score["score"] = score
            scored.append((score, page_with_score))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:limit]]


def build_context_items(question: str, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunk_items = search_relevant_chunks(question, pages)
    page_items = search_relevant_pages(question, pages)

    context_items: list[dict[str, Any]] = []
    seen_signatures: set[tuple[str, str]] = set()

    for item in chunk_items:
        signature = (item.get("url", ""), item.get("content", "")[:120])
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        context_items.append(
            {
                "kind": "chunk",
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score", 0.0),
            }
        )

    for item in page_items:
        signature = (item.get("url", ""), "__full_page__")
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        context_items.append(
            {
                "kind": "page",
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", "")[:2200],
                "score": item.get("score", 0.0),
            }
        )

    context_items.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    return context_items
