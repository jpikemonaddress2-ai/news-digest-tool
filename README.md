# 雑学ニュースダイジェスト

RSSフィードからニュース・雑学記事を収集し、Gemini で日本語要約を付けてメール配信する自動ツール。

## 構成

```
news-digest-tool/
├── config.yaml                  ← キーワード・ソース・配信設定（ここだけ編集すればOK）
├── requirements.txt
├── src/
│   ├── main.py                  ← エントリポイント
│   ├── collect.py               ← RSS収集
│   ├── filter.py                ← キーワードフィルタ + Gemini 要約
│   └── email_sender.py          ← HTML メール生成・送信
└── .github/workflows/
    └── daily.yml                ← GitHub Actions 毎日自動実行
```

## セットアップ

### 1. ローカル環境

```bash
pip install -r requirements.txt
```

### 2. ドライラン（メール送信なし）

```bash
cd news-digest-tool
python src/main.py --dry-run
```

### 3. HTML確認

```bash
python src/main.py --save-html output/digest.html
# output/digest.html をブラウザで開く
```

## GitHub Secrets の設定

| シークレット名 | 内容 |
|---|---|
| `GMAIL_ADDRESS` | 送信元 Gmail アドレス |
| `GMAIL_APP_PASSWORD` | Gmail アプリパスワード |
| `TO_ADDRESSES` | 宛先（カンマ区切りで複数可） |
| `GEMINI_API_KEY` | Gemini API キー（任意・未設定時は原文掲載） |

## 配信スケジュール

デフォルトは毎日 07:00 JST（`cron: '0 22 * * *'`）。

週1に変更する場合は `.github/workflows/daily.yml` の cron を変更：
```yaml
- cron: '0 22 * * 0'  # 毎週日曜 07:00 JST
```

その場合は `config.yaml` の `days_back` も `7` に変更すること。

## カスタマイズ

`config.yaml` を編集するだけで挙動を変更できる：

- `interest_keywords` — 興味のあるトピックのキーワード
- `rss_feeds` — 収集するニュースサイトの RSS フィード
- `delivery.days_back` — 収集対象の日数（日次なら 1、週次なら 7）
- `delivery.min_score` — 配信するスコア閾値（1〜5）
- `delivery.max_rss_per_feed` — 1フィードあたりの最大取得件数
