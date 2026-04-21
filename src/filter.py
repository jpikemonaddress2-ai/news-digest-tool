"""
フィルタリングモジュール
1. キーワード一次フィルタ（高速）
2. キーワードマッチ数によるスコアリング（★1〜5、API不要）
3. Gemini による日本語要約付加（オプション・失敗時は原文にフォールバック）
"""

from __future__ import annotations

import logging
import os
import time

from collect import Article

logger = logging.getLogger(__name__)


def keyword_filter(articles: list[Article], keywords: list[str]) -> list[Article]:
    """
    タイトルと要約にキーワードが1つでも含まれる記事だけを残す
    大文字小文字は区別しない
    """
    lower_keywords = [kw.lower() for kw in keywords]
    passed: list[Article] = []

    for article in articles:
        target = (article.title + " " + article.summary).lower()
        if any(kw in target for kw in lower_keywords):
            passed.append(article)

    logger.info("キーワードフィルタ: %d → %d 件", len(articles), len(passed))
    return passed


def _keyword_score(article: Article, keywords: list[str]) -> dict:
    """
    タイトル・要約にマッチするキーワード数でスコアを決める
    タイトルマッチは重み2、要約マッチは重み1
    """
    lower_keywords = [kw.lower() for kw in keywords]
    title_lower = article.title.lower()
    summary_lower = article.summary.lower()

    matched_kws: list[str] = []
    weighted_count = 0

    for kw in lower_keywords:
        in_title = kw in title_lower
        in_summary = kw in summary_lower
        if in_title or in_summary:
            matched_kws.append(kw)
            weighted_count += (2 if in_title else 0) + (1 if in_summary else 0)

    if weighted_count >= 5:
        score = 5
    elif weighted_count >= 3:
        score = 4
    else:
        score = 3

    matched_str = "、".join(matched_kws[:5])
    summary = (article.summary[:200] + "…") if len(article.summary) > 200 else article.summary
    if not summary:
        summary = article.title

    return {
        "relevance_score": score,
        "relevance_reason": f"キーワード {len(matched_kws)} 件マッチ（{matched_str}）",
        "summary": summary,
    }


def ai_score_filter(
    articles: list[Article],
    keywords: list[str],
    min_score: int = 3,
) -> list[Article]:
    """
    キーワードマッチ数でスコアリングし、min_score 以上の記事をスコア順に返す
    """
    passed: list[Article] = []
    logger.info("キーワードスコアリング中 (%d 件)...", len(articles))

    for i, article in enumerate(articles, 1):
        result = _keyword_score(article, keywords)
        score = result["relevance_score"]
        article.score = score
        article.score_reason = result["relevance_reason"]
        article.ai_summary = result["summary"]

        status = "✓" if score >= min_score else "✗"
        logger.info(
            "  [%d/%d] %s ★%d %s",
            i, len(articles), status, score, article.title[:50],
        )

        if score >= min_score:
            passed.append(article)

    passed.sort(key=lambda a: a.score or 0, reverse=True)
    logger.info("スコアリング完了: ★%d以上 %d 件 / %d 件", min_score, len(passed), len(articles))
    return passed


def _build_summary_prompt(article: Article, keywords: list[str]) -> str:
    keyword_str = "、".join(keywords[:8])
    score = article.score or 0
    return f"""あなたは化学・石油化学・材料まわりの業界ニュースをキュレーションする編集者です。
以下の記事を、新入社員にも通じる日本語の紹介文にしてください。

## 書き方
- 長さの目安: 全体で280〜450字程度（やや長くてよい）。最大2段落。段落の区切りは空行1行のみ（他の記号で段落分けしない）。
- 関心テーマとの関係: 「{keyword_str}」とどう結びつくかを、無理のない範囲で触れる。
- 専門用語は括弧や短い一文で噛み砕く。入力にない数字・固有名詞・因果を捏造しない。推測は「〜の可能性があります」に1回まで。
- 口調はフレンドリー（です・ます可）。業界・相場・制度などへの軽いユーモアや皮肉は1文まで。個人や特定企業を貶さない。
- 箇条書き・見出し記号は使わない。

## 関連度（編集メモ）
キーワードマッチの強さは ★{score} 相当（5が最も直結）。星と矛盾する過大な煽りは避ける。

## 記事
タイトル: {article.title}
抜粋: {article.summary[:900]}

紹介文のみ出力してください。"""


def add_ai_summaries(articles: list[Article], config: dict) -> None:
    """
    Gemini で日本語要約を生成して article.ai_summary に上書きする。
    GEMINI_API_KEY が未設定またはエラー時はスキップ（原文のまま）。
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.info("GEMINI_API_KEY が未設定のため日本語要約をスキップします")
        return

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.warning("google-genai がインストールされていません。日本語要約をスキップします")
        return

    model_name = config.get("gemini_model", "gemini-2.5-flash")
    keywords = config.get("interest_keywords", [])

    try:
        client = genai.Client(api_key=api_key)
    except Exception as exc:
        logger.warning("Gemini クライアント初期化失敗: %s", exc)
        return

    logger.info("Gemini 日本語要約中 (%d 件)...", len(articles))

    for i, article in enumerate(articles, 1):
        prompt = _build_summary_prompt(article, keywords)
        success = False

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=1024,
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                    ),
                )
                japanese_summary = response.text.strip()
                if japanese_summary:
                    article.ai_summary = japanese_summary
                    success = True
                    break
            except Exception as exc:
                logger.warning("要約失敗 (attempt %d/3) %s: %s", attempt + 1, article.title[:40], exc)
                if attempt < 2:
                    time.sleep(2 ** attempt)

        status = "✓" if success else "✗（原文）"
        logger.info("  [%d/%d] %s %s", i, len(articles), status, article.title[:50])
        time.sleep(0.5)


def run_filter(articles: list[Article], config: dict) -> list[Article]:
    """キーワードフィルタ → スコアリングの2段階フィルタを実行する"""
    keywords = config.get("interest_keywords", [])
    min_score = config["delivery"].get("min_score", 3)

    step1 = keyword_filter(articles, keywords)
    if not step1:
        logger.info("キーワードフィルタで0件になりました")
        return []

    step2 = ai_score_filter(step1, keywords, min_score)

    if step2:
        add_ai_summaries(step2, config)

    return step2
