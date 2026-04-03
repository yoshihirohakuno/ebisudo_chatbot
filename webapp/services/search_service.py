import json
import math
import os
import re
from collections import Counter
from typing import Any


def load_pages(data_file: str) -> list[dict[str, Any]]:
    if not os.path.exists(data_file):
        return []

    with open(data_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("pages", [])


def split_into_chunks(text: str, chunk_size: int = 420, overlap: int = 80) -> list[str]:
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
    return ascii_words + bigrams


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


def score_chunk(question: str, chunk: dict[str, Any]) -> float:
    question_tokens = tokenize(question)
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
    return coverage * 3 + density


def search_relevant_chunks(
    question: str,
    pages: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []

    for chunk in build_search_index(pages):
        score = score_chunk(question, chunk)
        if score > 0:
            chunk_with_score = dict(chunk)
            chunk_with_score["score"] = score
            scored.append((score, chunk_with_score))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:limit]]
