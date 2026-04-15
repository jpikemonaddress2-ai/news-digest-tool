"""
メール送信モジュール
Outlook 対応の HTML メールを生成して Gmail SMTP 経由で送信する

設計方針:
- レイアウトはすべて <table> ベース（Flexbox/Grid 禁止）
- スタイルはすべてインライン（外部CSS/CDN 禁止）
- SVG アイコンなし（Outlook デスクトップで消えるため）
- グラデーション・box-shadow なし
"""

from __future__ import annotations

import html
import logging
import os
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from collect import Article

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))

# スコア別カラー定義
CARD_COLORS: dict[int, dict[str, str]] = {
    5: {
        "border":    "#f5222d",
        "header_bg": "#fff1f0",
        "stars":     "★★★★★",
        "star_color": "#d4380d",
    },
    4: {
        "border":    "#1677ff",
        "header_bg": "#eff6ff",
        "stars":     "★★★★☆",
        "star_color": "#1677ff",
    },
    3: {
        "border":    "#52c41a",
        "header_bg": "#f6ffed",
        "stars":     "★★★☆☆",
        "star_color": "#389e0d",
    },
    2: {
        "border":    "#8c8c8c",
        "header_bg": "#fafafa",
        "stars":     "★★☆☆☆",
        "star_color": "#8c8c8c",
    },
    1: {
        "border":    "#8c8c8c",
        "header_bg": "#fafafa",
        "stars":     "★☆☆☆☆",
        "star_color": "#8c8c8c",
    },
}


def _fmt_date(dt: datetime) -> str:
    """JST に変換して 'YYYY年M月D日（曜）' 形式で返す（ゼロ埋めなし）"""
    jst = dt.astimezone(JST)
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    w = weekdays[jst.weekday()]
    return f"{jst.year}年{jst.month}月{jst.day}日（{w}）"


def _article_table(article: Article) -> str:
    """1件の記事をメール用シンプルテーブルで返す（タイトル＋★のみ）"""
    score = article.score or 0
    colors = CARD_COLORS.get(score, CARD_COLORS[1])
    title_escaped = html.escape(article.title)
    source_escaped = html.escape(article.source_name)

    return f"""
<!--[if mso]><table width="100%" cellpadding="0" cellspacing="0"><tr><td><![endif]-->
<table width="100%" cellpadding="0" cellspacing="0"
       style="border-collapse:collapse;margin-bottom:8px;border:1px solid #e8e8e8;">
  <tr>
    <td width="4" style="background-color:{colors['border']};font-size:0;line-height:0;">&nbsp;</td>
    <td style="padding:0;vertical-align:top;">
      <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
        <tr>
          <td style="padding:6px 12px;background-color:{colors['header_bg']};
                     font-size:10px;font-weight:600;color:#595959;
                     border-bottom:1px solid #e8e8e8;">
            {source_escaped}
          </td>
          <td style="padding:6px 12px;background-color:{colors['header_bg']};
                     font-size:11px;font-weight:700;color:{colors['star_color']};
                     text-align:right;white-space:nowrap;
                     border-bottom:1px solid #e8e8e8;">
            {colors['stars']}
          </td>
        </tr>
        <tr>
          <td colspan="2" style="padding:8px 12px;font-size:13px;font-weight:600;
                                 color:#1d1d1f;line-height:1.5;">
            {title_escaped}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->"""


def _digest_article_table(article: Article) -> str:
    """1件の記事を図解ページ用テーブルで返す（要約・リンク付き詳細版）"""
    score = article.score or 0
    colors = CARD_COLORS.get(score, CARD_COLORS[1])
    raw_summary = article.ai_summary or article.summary[:400]
    summary = html.escape(raw_summary)
    title_escaped = html.escape(article.title)
    source_escaped = html.escape(article.source_name)

    return f"""
<!--[if mso]><table width="100%" cellpadding="0" cellspacing="0"><tr><td><![endif]-->
<table width="100%" cellpadding="0" cellspacing="0"
       style="border-collapse:collapse;margin-bottom:12px;border:1px solid #e8e8e8;">
  <tr>
    <td width="4" style="background-color:{colors['border']};font-size:0;line-height:0;">&nbsp;</td>
    <td style="padding:0;vertical-align:top;">
      <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
        <tr>
          <td style="padding:8px 12px;background-color:{colors['header_bg']};
                     font-size:11px;font-weight:600;color:#595959;
                     border-bottom:1px solid #e8e8e8;">
            {source_escaped}
          </td>
          <td style="padding:8px 12px;background-color:{colors['header_bg']};
                     font-size:12px;font-weight:700;color:{colors['star_color']};
                     text-align:right;white-space:nowrap;
                     border-bottom:1px solid #e8e8e8;">
            {colors['stars']}
          </td>
        </tr>
        <tr>
          <td colspan="2" style="padding:10px 12px 6px;">
            <a href="{article.url}"
               style="font-size:14px;font-weight:700;color:#1d1d1f;
                      text-decoration:none;line-height:1.5;">
              {title_escaped}
            </a>
          </td>
        </tr>
        <tr>
          <td colspan="2" style="padding:0 12px 10px;font-size:13px;color:#434343;line-height:1.7;">
            {summary}
          </td>
        </tr>
        <tr>
          <td colspan="2" style="padding:0 12px 12px;">
            <a href="{article.url}"
               style="font-size:12px;font-weight:600;color:#059669;text-decoration:none;">
              記事を読む &rarr;
            </a>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->"""


def build_html(
    articles: list[Article],
    keywords: list[str],
    config: dict,
    report_date: datetime,
    total_collected: int = 0,
) -> str:
    """Outlook 対応 HTML メール本文を構築する（タイトル＋★のシンプル版）"""
    date_str = _fmt_date(report_date)
    count = len(articles)
    min_score = config["delivery"].get("min_score", 3)
    subject_prefix = config.get("email", {}).get("subject_prefix", "化学業界ニュースダイジェスト")
    days_back = config["delivery"].get("days_back", 7)
    freq_label = "毎日" if days_back == 1 else f"過去{days_back}日分"

    source_count = len(config.get("rss_feeds", []))
    collected_str = str(total_collected) if total_collected > 0 else "-"
    article_tables = "".join(_article_table(a) for a in articles)

    return f"""<!DOCTYPE html>
<html lang="ja" xmlns:v="urn:schemas-microsoft-com:vml"
      xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<!--[if mso]>
<noscript>
<xml><o:OfficeDocumentSettings>
  <o:PixelsPerInch>96</o:PixelsPerInch>
</o:OfficeDocumentSettings></xml>
</noscript>
<![endif]-->
<title>{subject_prefix} {date_str}</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f5f5;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;background-color:#f5f5f5;">
  <tr>
    <td align="center" style="padding:20px 8px;">
      <table width="600" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;max-width:600px;width:100%;
                    background-color:#ffffff;border:1px solid #e8e8e8;">
        <tr>
          <td style="background-color:#059669;padding:20px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
              <tr>
                <td style="vertical-align:middle;">
                  <p style="margin:0 0 2px;font-size:11px;color:#a7f3d0;">{subject_prefix}</p>
                  <h1 style="margin:0;font-size:18px;font-weight:700;color:#ffffff;line-height:1.4;">{date_str}</h1>
                </td>
                <td style="text-align:right;vertical-align:middle;white-space:nowrap;">
                  <span style="font-size:24px;font-weight:700;color:#ffffff;">{count}</span>
                  <span style="font-size:12px;color:#a7f3d0;display:block;">件をピックアップ</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="background-color:#ecfdf5;border-bottom:1px solid #d1fae5;padding:0;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
              <tr>
                <td width="33%" style="padding:10px 0;text-align:center;border-right:1px solid #d1fae5;">
                  <div style="font-size:18px;font-weight:700;color:#059669;">{source_count}</div>
                  <div style="font-size:10px;color:#6b7280;margin-top:2px;">ソース</div>
                </td>
                <td width="34%" style="padding:10px 0;text-align:center;border-right:1px solid #d1fae5;">
                  <div style="font-size:18px;font-weight:700;color:#059669;">{collected_str}</div>
                  <div style="font-size:10px;color:#6b7280;margin-top:2px;">収集件数</div>
                </td>
                <td width="33%" style="padding:10px 0;text-align:center;">
                  <div style="font-size:18px;font-weight:700;color:#059669;">{count}</div>
                  <div style="font-size:10px;color:#6b7280;margin-top:2px;">配信件数</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:12px 16px 8px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
              <tr>
                <td style="font-size:13px;font-weight:700;color:#1d1d1f;">★ ピックアップ（★{min_score}以上）</td>
                <td style="text-align:right;font-size:10px;color:#9ca3af;">{freq_label}</td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:0 16px 12px;">
            {article_tables}
          </td>
        </tr>
        <tr>
          <td style="padding:14px 20px;background-color:#f9fafb;border-top:1px solid #e8e8e8;text-align:center;">
            <p style="margin:0;font-size:10px;color:#d1d5db;">
              {freq_label} 自動配信 by GitHub Actions
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""


def build_digest_html(
    articles: list[Article],
    keywords: list[str],
    config: dict,
    report_date: datetime,
    total_collected: int = 0,
) -> str:
    """週次アーカイブ用 HTML（要約・記事リンク付き詳細版）を構築する"""
    date_str = _fmt_date(report_date)
    count = len(articles)
    min_score = config["delivery"].get("min_score", 3)
    subject_prefix = config.get("email", {}).get("subject_prefix", "化学業界ニュースダイジェスト")
    days_back = config["delivery"].get("days_back", 7)
    freq_label = "毎日" if days_back == 1 else f"過去{days_back}日分"

    # キーワードタグ
    kw_spans = "&nbsp; ".join(
        f'<span style="background:#ecfdf5;color:#059669;padding:2px 6px;'
        f'font-size:11px;">{kw}</span>'
        for kw in keywords[:12]
    )

    source_count = len(config.get("rss_feeds", []))
    collected_str = str(total_collected) if total_collected > 0 else "-"
    article_tables = "".join(_digest_article_table(a) for a in articles)

    return f"""<!DOCTYPE html>
<html lang="ja" xmlns:v="urn:schemas-microsoft-com:vml"
      xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<!--[if mso]>
<noscript>
<xml><o:OfficeDocumentSettings>
  <o:PixelsPerInch>96</o:PixelsPerInch>
</o:OfficeDocumentSettings></xml>
</noscript>
<![endif]-->
<title>{subject_prefix} {date_str}</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f5f5;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Arial,sans-serif;">

<!-- 外枠 -->
<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;background-color:#f5f5f5;">
  <tr>
    <td align="center" style="padding:20px 8px;">

      <!-- コンテンツ幅 -->
      <table width="600" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;max-width:600px;width:100%;
                    background-color:#ffffff;border:1px solid #e8e8e8;">

        <!-- ===== ヘッダー ===== -->
        <tr>
          <td style="background-color:#059669;padding:24px 20px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
              <tr>
                <td style="vertical-align:middle;">
                  <p style="margin:0 0 2px;font-size:11px;color:#a7f3d0;letter-spacing:0.5px;">
                    {subject_prefix}
                  </p>
                  <h1 style="margin:0;font-size:18px;font-weight:700;color:#ffffff;line-height:1.4;">
                    {date_str}
                  </h1>
                </td>
                <td style="text-align:right;vertical-align:middle;white-space:nowrap;">
                  <span style="font-size:24px;font-weight:700;color:#ffffff;">{count}</span>
                  <span style="font-size:12px;color:#a7f3d0;display:block;">件をピックアップ</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ===== 統計バー ===== -->
        <tr>
          <td style="background-color:#ecfdf5;border-bottom:1px solid #d1fae5;padding:0;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
              <tr>
                <td width="33%" style="padding:12px 0;text-align:center;
                                       border-right:1px solid #d1fae5;">
                  <div style="font-size:20px;font-weight:700;color:#059669;">{source_count}</div>
                  <div style="font-size:10px;color:#6b7280;margin-top:2px;">ソース</div>
                </td>
                <td width="34%" style="padding:12px 0;text-align:center;
                                       border-right:1px solid #d1fae5;">
                  <div style="font-size:20px;font-weight:700;color:#059669;">{collected_str}</div>
                  <div style="font-size:10px;color:#6b7280;margin-top:2px;">収集件数</div>
                </td>
                <td width="33%" style="padding:12px 0;text-align:center;">
                  <div style="font-size:20px;font-weight:700;color:#059669;">{count}</div>
                  <div style="font-size:10px;color:#6b7280;margin-top:2px;">配信件数</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ===== キーワード ===== -->
        <tr>
          <td style="padding:12px 16px;background-color:#fafafa;border-bottom:1px solid #e8e8e8;">
            <p style="margin:0 0 6px;font-size:10px;color:#9ca3af;">関心キーワード</p>
            <p style="margin:0 0 8px;line-height:1.8;">{kw_spans}</p>
            <p style="margin:0;font-size:11px;color:#9ca3af;">
              ★ 関連度:
              <span style="color:#d4380d;font-weight:600;">★★★★★ ドンピシャ</span> &nbsp;
              <span style="color:#1677ff;font-weight:600;">★★★★☆ 強く関連</span> &nbsp;
              <span style="color:#389e0d;font-weight:600;">★★★☆☆ 部分的（★{min_score}以上を配信）</span>
            </p>
          </td>
        </tr>

        <!-- ===== ピックアップ見出し ===== -->
        <tr>
          <td style="padding:16px 16px 12px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
              <tr>
                <td style="font-size:14px;font-weight:700;color:#1d1d1f;">
                  ★ ピックアップ
                </td>
                <td style="text-align:right;font-size:10px;color:#9ca3af;">
                  ★{min_score}以上のみ配信
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ===== 記事一覧 ===== -->
        <tr>
          <td style="padding:0 16px 8px;">
            {article_tables}
          </td>
        </tr>

        <!-- ===== フッター ===== -->
        <tr>
          <td style="padding:16px 20px;background-color:#f9fafb;border-top:1px solid #e8e8e8;
                     text-align:center;">
            <p style="margin:0 0 4px;font-size:11px;color:#9ca3af;">
              {freq_label} 自動配信 by GitHub Actions
            </p>
            <p style="margin:0;font-size:10px;color:#d1d5db;">
              キーワード・配信設定の変更は config.yaml を編集してください。
            </p>
          </td>
        </tr>

      </table><!-- /コンテンツ幅 -->
    </td>
  </tr>
</table><!-- /外枠 -->

</body>
</html>"""


def send_email(
    html_body: str,
    subject: str,
    config: dict,
) -> None:
    """Gmail SMTP でHTMLメールを送信する"""
    email_cfg = config.get("email", {})
    from_addr = os.environ.get(email_cfg.get("from_env", "GMAIL_ADDRESS"), "")
    password = os.environ.get(email_cfg.get("password_env", "GMAIL_APP_PASSWORD"), "")
    to_raw = os.environ.get(email_cfg.get("to_env", "TO_ADDRESSES"), "")
    to_addrs = [addr.strip() for addr in to_raw.split(",") if addr.strip()]

    if not from_addr:
        raise RuntimeError("環境変数 GMAIL_ADDRESS が設定されていません")
    if not password:
        raise RuntimeError("環境変数 GMAIL_APP_PASSWORD が設定されていません")
    if not to_addrs:
        raise RuntimeError("環境変数 TO_ADDRESSES が設定されていません")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    logger.info("メール送信中 → %s", to_addrs)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(from_addr, password)
        smtp.sendmail(from_addr, to_addrs, msg.as_bytes())
    logger.info("メール送信完了 → %s", to_addrs)


def build_empty_html(config: dict, report_date: datetime, total_collected: int) -> str:
    """配信対象0件のときに送る通知メール本文を構築する"""
    subject_prefix = config.get("email", {}).get("subject_prefix", "雑学ニュースダイジェスト")
    date_str = _fmt_date(report_date)
    min_score = config["delivery"].get("min_score", 3)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>{subject_prefix} {date_str}</title></head>
<body style="margin:0;padding:0;background-color:#f5f5f5;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;background-color:#f5f5f5;">
  <tr><td align="center" style="padding:40px 8px;">
    <table width="600" cellpadding="0" cellspacing="0"
           style="border-collapse:collapse;max-width:600px;width:100%;
                  background-color:#ffffff;border:1px solid #e8e8e8;">
      <tr>
        <td style="background-color:#059669;padding:24px 20px;">
          <p style="margin:0 0 2px;font-size:11px;color:#a7f3d0;">{subject_prefix}</p>
          <h1 style="margin:0;font-size:18px;font-weight:700;color:#ffffff;">{date_str}</h1>
        </td>
      </tr>
      <tr>
        <td style="padding:32px 24px;text-align:center;">
          <p style="font-size:32px;margin:0 0 12px;">📭</p>
          <p style="font-size:16px;font-weight:700;color:#1d1d1f;margin:0 0 8px;">
            本日の配信対象記事はありませんでした
          </p>
          <p style="font-size:13px;color:#6b7280;margin:0;">
            {total_collected} 件を収集しましたが、★{min_score}以上に該当する記事がありませんでした。
          </p>
        </td>
      </tr>
      <tr>
        <td style="padding:16px 20px;background-color:#f9fafb;border-top:1px solid #e8e8e8;
                   text-align:center;">
          <p style="margin:0;font-size:10px;color:#d1d5db;">
            自動配信システム by GitHub Actions
          </p>
        </td>
      </tr>
    </table>
  </td></tr>
</table>
</body></html>"""


def deliver(articles: list[Article], config: dict, total_collected: int = 0) -> None:
    """HTML生成 + Gmail送信を一括実行する"""
    keywords = config.get("interest_keywords", [])
    now = datetime.now(tz=timezone.utc)

    subject_prefix = config.get("email", {}).get("subject_prefix", "雑学ニュースダイジェスト")
    dt = now.astimezone(JST)
    date_str = f"{dt.year}/{dt.month}/{dt.day}"

    if articles:
        html_body = build_html(articles, keywords, config, now, total_collected)
        subject = f"{subject_prefix} {date_str}（{len(articles)} 件）"
    else:
        html_body = build_empty_html(config, now, total_collected)
        subject = f"{subject_prefix} {date_str}（本日は該当なし）"

    send_email(html_body, subject, config)
