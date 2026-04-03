from typing import Any

from google import genai

from .search_service import load_pages, search_relevant_chunks


FALLBACK_MESSAGE = "サイト内では確認できませんでした。"


def build_prompt(question: str, chunks: list[dict[str, Any]]) -> str:
    context_blocks = []
    for index, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[資料{index}]",
                    f"タイトル: {chunk['title']}",
                    f"URL: {chunk['url']}",
                    f"本文: {chunk['content']}",
                ]
            )
        )

    context_text = "\n\n".join(context_blocks)

    return f"""あなたは、株式会社えびす堂の公開サイト https://www.ebisudo.co.jp/ の情報だけを使って答えるFAQチャットBotです。

以下のルールを必ず守ってください。
- 回答は日本語で書く
- 資料に書かれている内容だけを根拠にする
- 書かれていないことを推測で断定しない
- わからない場合は必ず「{FALLBACK_MESSAGE}」と書く
- 可能なら根拠URLを文末に短く添える
- 丁寧で簡潔に答える

質問:
{question}

参考資料:
{context_text}
"""


def answer_question(
    question: str,
    data_file: str,
    api_key: str,
    model_name: str,
) -> dict[str, Any]:
    pages = load_pages(data_file)
    if not pages:
        return {
            "answer": "まだサイトデータがありません。先にクロールを実行してください。",
            "sources": [],
        }

    chunks = search_relevant_chunks(question, pages)
    if not chunks:
        return {"answer": FALLBACK_MESSAGE, "sources": []}
    if chunks[0].get("score", 0) < 1.0:
        return {"answer": FALLBACK_MESSAGE, "sources": []}

    if not api_key:
        return {
            "answer": "GEMINI_API_KEY が設定されていません。",
            "sources": [],
        }

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(question, chunks)

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    answer = (response.text or "").strip() or FALLBACK_MESSAGE

    unique_sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for chunk in chunks:
        url = chunk["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        unique_sources.append({"title": chunk["title"], "url": url})

    return {"answer": answer, "sources": unique_sources}
