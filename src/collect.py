"""
情報収集モジュール
RSSフィードからニュース・雑学記事を収集する
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser
import yaml

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


@dataclass
class Article:
    """収集した記事の共通データ型"""
    source_type: str          # "rss"
    source_name: str          # フィード名
    title: str
    summary: str
    url: str
    published: Optional[datetime] = None
    authors: list[str] = field(default_factory=list)
    score: Optional[int] = None
    score_reason: Optional[str] = None
    ai_summary: Optional[str] = None


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_feed_date(entry) -> Optional[datetime]:
    """feedparser のエントリから公開日時を取得して UTC datetime に変換する"""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def collect_rss(config: dict, since: datetime) -> list[Article]:
    """
    config.rss_feeds に列挙された全フィードから記事を収集する
    since より新しい記事だけを返す。フィード間の重複URLは除去する。
    """
    articles: list[Article] = []
    seen_urls: set[str] = set()
    max_per_feed = config["delivery"].get("max_rss_per_feed", 20)

    for feed_cfg in config.get("rss_feeds", []):
        name = feed_cfg["name"]
        url = feed_cfg["url"]
        logger.info("RSS取得中: %s", name)

        try:
            parsed = feedparser.parse(url)
        except Exception as exc:
            logger.warning("RSS取得失敗 %s: %s", name, exc)
            continue

        count = 0
        for entry in parsed.entries:
            if count >= max_per_feed:
                break

            pub = _parse_feed_date(entry)
            if pub and pub < since:
                continue

            title = getattr(entry, "title", "").strip()
            summary = getattr(entry, "summary", "").strip()
            link = getattr(entry, "link", "")

            if not title or not link:
                continue

            if link in seen_urls:
                continue
            seen_urls.add(link)

            articles.append(Article(
                source_type="rss",
                source_name=name,
                title=title,
                summary=summary,
                url=link,
                published=pub,
            ))
            count += 1

        logger.info("  → %d 件取得", count)
        time.sleep(0.5)

    return articles


def collect_all(config: dict) -> list[Article]:
    """RSSフィードから記事を収集してまとめて返す"""
    days_back = config["delivery"].get("days_back", 1)
    since = datetime.now(tz=timezone.utc) - timedelta(days=days_back)
    logger.info("収集期間: 過去 %d 日（%s 以降）", days_back, since.strftime("%Y-%m-%d"))

    articles = collect_rss(config, since)
    logger.info("収集合計: %d 件", len(articles))
    return articles
