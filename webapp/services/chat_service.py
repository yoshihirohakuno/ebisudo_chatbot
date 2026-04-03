from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo
import re

from google import genai

from .search_service import build_context_items, load_pages


FALLBACK_MESSAGE = "申し訳ありませんが、弊社サイト内では確認できませんでした。"
CONTACT_URL = "https://www.ebisudo.co.jp/#_3"
CONTACT_GUIDE = (
    "お問い合わせは、電話 050-5212-8111、FAX 03-6800-3193、"
    "メール ebisu002@bp.iij4u.or.jp でご案内しております。"
)


def build_friendly_fallback(question: str) -> str:
    normalized = question.replace("　", " ").strip().lower()

    person_keywords = [
        "人柄",
        "経歴",
        "人物像",
        "どんな人",
        "性格",
        "趣味",
        "好き",
    ]

    if any(keyword in normalized for keyword in person_keywords):
        return (
            "恐れ入りますが、弊社サイト内では確認できませんでした。\n\n"
            "人柄のような部分は、文字だけではなかなか伝わりにくいので、"
            "直接お会いしてお確かめいただくのがいちばんかもしれません。\n\n"
            f"{CONTACT_GUIDE}"
        )

    return f"{FALLBACK_MESSAGE}\n\n{CONTACT_GUIDE}"


def build_datetime_answer(question: str) -> str | None:
    normalized = question.replace("　", " ").strip().lower()
    keywords = ["今日", "日時", "日付", "今何時", "現在時刻", "何時", "時刻"]

    if not any(keyword in normalized for keyword in keywords):
        return None

    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    return (
        f"本日の日付と時刻は、{now.year}年{now.month}月{now.day}日 "
        f"{now.hour:02d}:{now.minute:02d}（日本時間）です。"
    )


def build_personality_answer(question: str, chunks: list[dict[str, Any]]) -> str | None:
    normalized = question.replace("　", " ").strip().lower()
    person_keywords = ["人柄", "経歴", "人物像", "どんな人", "性格", "趣味", "好き"]

    if not any(keyword in normalized for keyword in person_keywords):
        return None

    representative_name = None
    for chunk in chunks:
        content = chunk.get("content", "")
        if "代表取締役" in content:
            if "安藤英夫" in content:
                representative_name = "安藤英夫"
                break

    if representative_name:
        return (
            f"弊社サイトでご案内している範囲では、代表取締役は {representative_name} です。\n\n"
            "ただ、人柄や雰囲気のようなところは、文章だけではなかなか伝わりません。"
            "そのあたりは、直接お会いしてお確かめいただくのがいちばんかもしれません。"
        )

    return (
        "恐れ入りますが、弊社サイト内では確認できませんでした。\n\n"
        "人柄のような部分は、文字だけではなかなか伝わりにくいので、"
        "直接お会いしてお確かめいただくのがいちばんかもしれません。"
    )


def build_conversational_out_of_scope_answer(question: str) -> str | None:
    normalized = question.replace("　", " ").strip().lower()

    praise_keywords = [
        "すごい",
        "いいですね",
        "いいね",
        "助かる",
        "ありがとう",
        "ありがたい",
        "さすが",
        "便利",
    ]

    if any(keyword in normalized for keyword in praise_keywords):
        return (
            "ありがとうございます。そう言っていただけると嬉しいです。"
            "引き続き、えびす堂のことでしたらわかりやすくご案内します。"
        )

    short_reaction_keywords = [
        "ほんと",
        "本当",
        "なるほど",
        "いい感じ",
        "いいかも",
        "素敵",
    ]

    if any(keyword in normalized for keyword in short_reaction_keywords):
        return (
            "そう言っていただけると励みになります。"
            "気になることがあれば、そのまま続けて聞いてください。"
        )

    capability_keywords = [
        "どんな質問",
        "なんでも",
        "何でも",
        "答えられる",
        "できますか",
        "bot",
        "チャットボット",
        "あなたは",
    ]

    if any(keyword in normalized for keyword in capability_keywords):
        return (
            "できるだけお答えしようとは思いますが、いまは弊社サイトの内容をご案内する役目です。"
            "職務中ですので、えびす堂の事業内容やサービス、事例などについてご質問いただけると助かります。"
        )

    casual_keywords = ["天気", "占い", "雑談", "ゲーム", "好きな食べ物", "好きな映画"]
    if any(keyword in normalized for keyword in casual_keywords):
        return (
            "その話題もお付き合いしたいところですが、いまは弊社サイトのご案内に集中しています。"
            "えびす堂のサービスや印刷、データ処理に関することでしたら、お気軽にご質問ください。"
        )

    return None


def build_special_answer(question: str, chunks: list[dict[str, Any]]) -> str | None:
    normalized = question.replace("　", " ").strip().lower()

    if "問い合わせ" in normalized or "お問い合わせ" in normalized or "連絡先" in normalized:
        return CONTACT_GUIDE

    if any(keyword in normalized for keyword in ["どこ", "所在地", "住所"]) and "会社" in normalized:
        return (
            "弊社は、〒116-0001 東京都荒川区町屋8-22-10 にございます。\n\n"
            "お問い合わせ先にも同じ所在地を掲載しております。"
        )

    if "可変印刷" in normalized and any(keyword in normalized for keyword in ["何", "どんなこと", "使", "用途"]):
        return (
            "可変印刷は、1枚ごとに内容を変えて印刷できる仕組みです。\n\n"
            "かんたんに言うと、同じ紙を大量に刷るのではなく、1枚ずつ違う情報を載せられます。\n\n"
            "弊社サイトの掲載内容から見ると、主に次のような用途で活用できます。\n"
            "・店舗ごとに必要枚数や内容が違う印刷物への対応\n"
            "・ナンバリングやバリアブル印字が入る製品への対応\n"
            "・キャンペーン用カードや応募コードのように、1枚ごとに異なるコードを載せる用途\n"
            "・バーコードやQRコード、文字、数字、ビットマップを組み合わせた印字\n"
            "・個別マーケティング向けの印刷物への対応\n\n"
            "サイト内では、店舗数が数百あり、店舗ごとに必要数が異なるような小ロット多品種の案件や、"
            "キャンペーン用カードの乱数データ作成などが紹介されています。"
        )

    if "可変印刷" in normalized:
        return (
            "可変印刷（Variable Data Printing / VDP）は、\n"
            "1枚ごとに内容を変えて印刷できる仕組みのことです。\n\n"
            "■ わかりやすく言うと\n\n"
            "普通の印刷\n"
            "→ 全部同じ内容を大量に刷る\n\n"
            "可変印刷\n"
            "→ 1枚ずつ違う情報を入れて印刷する\n\n"
            "弊社サイトでは、こうした可変印刷を「バリアブル印字」やデータ印字として案内しており、"
            "ナンバリングやデータ処理、乱数生成、チェック処理などと組み合わせて対応しています。"
        )

    return None


def build_prompt(question: str, chunks: list[dict[str, Any]]) -> str:
    context_blocks = []
    for index, chunk in enumerate(chunks, start=1):
        label = "関連ページ全体" if chunk.get("kind") == "page" else "関連箇所"
        context_blocks.append(
            "\n".join(
                [
                    f"[資料{index}]",
                    f"種類: {label}",
                    f"タイトル: {chunk['title']}",
                    f"URL: {chunk['url']}",
                    f"本文: {chunk['content']}",
                ]
            )
        )

    context_text = "\n\n".join(context_blocks)

    return f"""あなたは、株式会社えびす堂の公開サイト https://www.ebisudo.co.jp/ の情報だけを使って答えるFAQチャットBotです。
利用者に対して、弊社の担当者として案内してください。

以下のルールを必ず守ってください。
- 回答は日本語で書く
- 一人称や主語は「弊社」「当社」を基本にする
- 「株式会社えびす堂のサイトでは」「このサイトでは」など、第三者のような言い方はできるだけ避ける
- ただし、書かれていないことを知っているふりはしない
- 資料に書かれている内容だけを根拠にする
- 書かれていないことを推測で断定しない
- わからない場合は必ず「{FALLBACK_MESSAGE}」を含めて案内する
- 可能なら根拠URLを文末に短く添える
- 丁寧で簡潔に答える
- 専門用語は、初心者にもわかる短い言い換えを添える
- 「つまり」「かんたんに言うと」などを使って、やさしく説明してよい
- 資料の周辺文脈から意味が読み取れる場合は、その範囲で控えめに補足してよい
- 資料どうしを見比べて、つながる内容はまとめて考えてよい
- 資料に見出ししかない場合は、その見出しから確認できる範囲だけを控えめに述べる
- 質問が「どんなことが可能か」の形でも、資料にある説明だけで答える
- 回答の基本構成は、必要に応じて次の順にする
  1. ひとことで結論
  2. やさしい説明
  3. サイト内で確認できる根拠
- 箇条書きにする場合も、初心者に伝わる言い回しを優先する
- たとえば「弊社では〜に対応しています」「かんたんに言うと〜です」のような案内調で書く
- 定義が明記されていない場合も、「弊社サイト上では定義そのものは詳しく書いていませんが、掲載内容から見ると〜」のように主体的に説明する
- すぐに「確認できませんでした」とせず、まず資料全体を見比べて答えられる範囲がないか丁寧に検討する
- ただし、資料にない断定はしない
- 回答本文の中に「[資料1]」「[資料2]」のような参照表記は入れない
- 回答本文の中にURLをそのまま書かない

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

    datetime_answer = build_datetime_answer(question)
    if datetime_answer:
        return {"answer": datetime_answer, "sources": []}

    conversational_answer = build_conversational_out_of_scope_answer(question)
    if conversational_answer:
        return {"answer": conversational_answer, "sources": []}

    chunks = build_context_items(question, pages)
    if not chunks:
        return {
            "answer": build_friendly_fallback(question),
            "sources": [],
        }
    if chunks[0].get("score", 0) < 0.45:
        return {
            "answer": build_friendly_fallback(question),
            "sources": [],
        }

    if not api_key:
        return {
            "answer": "GEMINI_API_KEY が設定されていません。",
            "sources": [],
        }

    special_answer = build_special_answer(question, chunks)
    if special_answer:
        unique_sources: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        for chunk in chunks:
            url = chunk["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            unique_sources.append({"title": chunk["title"], "url": url})
        return {"answer": special_answer, "sources": unique_sources}

    personality_answer = build_personality_answer(question, chunks)
    if personality_answer:
        unique_sources: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        for chunk in chunks:
            url = chunk["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            unique_sources.append({"title": chunk["title"], "url": url})
        return {
            "answer": personality_answer,
            "sources": unique_sources,
        }

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(question, chunks)

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    answer = (response.text or "").strip() or FALLBACK_MESSAGE
    answer = re.sub(r"\s*\[資料\d+\]\([^)]+\)", "", answer)
    answer = re.sub(r"\s*\[資料\d+\]", "", answer)
    answer = re.sub(r"（\s*https?://[^）]+\s*）", "", answer)
    answer = re.sub(r"\(\s*https?://[^)]+\s*\)", "", answer)
    answer = re.sub(r"https?://\S+", "", answer)
    answer = re.sub(r"\n{3,}", "\n\n", answer).strip()

    unique_sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for chunk in chunks:
        url = chunk["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        unique_sources.append({"title": chunk["title"], "url": url})

    result = {"answer": answer, "sources": unique_sources}
    if "確認できませんでした" in answer:
        result["answer"] = f"{answer}\n\n{CONTACT_GUIDE}"
    return result
