"""
送信 MIME が Outlook 切り分け（メッセージソース）で期待どおりか検証する。
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone
from email import message_from_bytes
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from collect import Article  # noqa: E402
from email_sender import (  # noqa: E402
    build_empty_plain,
    build_plain_digest,
    send_email,
)


class TestEmailMime(unittest.TestCase):
    """メール生データに text/plain と text/html が含まれることの自動検証。"""

    def setUp(self) -> None:
        self._env = {
            "GMAIL_ADDRESS": "from@example.com",
            "GMAIL_APP_PASSWORD": "secret",
            "TO_ADDRESSES": "to@example.com",
        }

    def test_sendmail_payload_is_multipart_plain_then_html(self) -> None:
        html = "<!DOCTYPE html><html><body><p>HTML本文</p></body></html>"
        plain = "プレーン本文\n2行目"
        config: dict = {"email": {}}

        mock_ctx = MagicMock()
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_ctx)
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch.dict(os.environ, self._env, clear=False):
            with patch("email_sender.smtplib.SMTP_SSL", return_value=mock_smtp):
                send_email(html, "件名テスト", config, plain)

        mock_ctx.login.assert_called_once()
        mock_ctx.sendmail.assert_called_once()
        _from, _to, raw = mock_ctx.sendmail.call_args[0]
        self.assertEqual(_from, "from@example.com")
        self.assertEqual(_to, ["to@example.com"])

        msg = message_from_bytes(raw)
        self.assertTrue(msg.is_multipart())
        parts = msg.get_payload()
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0].get_content_type(), "text/plain")
        self.assertEqual(parts[1].get_content_type(), "text/html")
        self.assertIn("プレーン本文", parts[0].get_payload(decode=True).decode("utf-8"))
        self.assertIn("HTML本文", parts[1].get_payload(decode=True).decode("utf-8"))

    def test_plain_digest_contains_title_and_url(self) -> None:
        now = datetime(2026, 4, 21, 12, 0, tzinfo=timezone.utc)
        article = Article(
            source_type="rss",
            source_name="テストソース",
            title="記事タイトル",
            summary="要約です。",
            url="https://example.com/article",
            score=4,
        )
        config = {
            "email": {"subject_prefix": "プレフィックス"},
            "delivery": {"min_score": 3, "days_back": 7},
            "rss_feeds": [{"name": "A", "url": "https://a"}],
        }
        plain = build_plain_digest([article], ["キーワード"], config, now, 5)
        self.assertIn("記事タイトル", plain)
        self.assertIn("https://example.com/article", plain)
        self.assertIn("要約です。", plain)
        self.assertIn("★★★★☆", plain)

    def test_empty_plain_has_policy_line(self) -> None:
        now = datetime(2026, 4, 21, 12, 0, tzinfo=timezone.utc)
        config = {
            "email": {"subject_prefix": "プレフィックス"},
            "delivery": {"min_score": 3},
        }
        plain = build_empty_plain(config, now, 10)
        self.assertIn("配信対象記事はありませんでした", plain)
        self.assertIn("10 件", plain)
