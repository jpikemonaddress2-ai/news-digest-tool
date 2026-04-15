# 引き継ぎドキュメント：業界ニュースダイジェスト 図解ページ作成

## 現状

`news-digest-tool` は完成・稼働中。毎週月曜 07:00 JST に自動実行される。

### リポジトリ
```
https://github.com/jpikemonaddress2-ai/news-digest-tool
C:\Users\jpike\src\news-digest-tool
```

### 現在の動作フロー
```
GitHub Actions（週次）
  → RSS収集（Google News化学系 + MONOist）
  → キーワードフィルタ + スコアリング
  → メール送信（タイトル＋★のみのシンプル版）
  → 図解HTML生成 → Artifactに保存（90日間）
```

---

## 残タスク：図解ページのデザイン作成

### やること
`src/email_sender.py` の `build_digest_html()` 関数が生成するHTMLを
現在のシンプルなカード形式から、見やすい「図解ページ」に作り直す。

### 現在の図解HTML
- 関数：`build_digest_html()` in `src/email_sender.py`（280行目〜）
- 内容：タイトル・★スコア・Gemini要約・記事リンク付きのカード形式
- 制約：**なし**（メールと違いブラウザで開くのでCSSもJSも自由に使える）

### 目指すイメージ
- ブラウザで開いて読む「週次レポートページ」
- 記事カードをリッチに（サムネイル風・カテゴリタグ・スコアバー など）
- Gemini要約を読みやすく表示
- 記事リンクをクリックして元記事へ飛べる

### デザイン参考
`commit-report-tool` のダイアグラムガイドラインを参照：
```
C:\Users\jpike\src\commit-report-tool\.claude\skills\diagram-guidelines\SKILL.md
C:\Users\jpike\src\commit-report-tool\.claude\skills\diagram-guidelines\examples\
```

### 実装方針
1. `build_digest_html()` のreturn文のHTMLを書き直すだけでOK
2. `_digest_article_table()` も合わせて変更（各記事カードのHTML）
3. Gemini要約（`article.ai_summary`）を活用したレイアウトにする
4. ローカルテストは：
   ```bash
   cd C:\Users\jpike\src\news-digest-tool
   python src/main.py --dry-run
   # → output/digest-YYYY-MM-DD.html が生成される
   # ブラウザで開いて確認
   ```

### Article データ構造（使える情報）
```python
article.title        # タイトル
article.source_name  # ソース名（Google News: 化学業界 など）
article.url          # 記事URL
article.published    # 公開日時（datetime）
article.score        # 関連度スコア（3〜5）
article.score_reason # スコア理由（例：キーワード 2件マッチ）
article.ai_summary   # Gemini日本語要約（APIキー設定時）
article.summary      # RSS原文要約（フォールバック）
```

### GitHub Secrets（設定済み）
| シークレット名 | 内容 |
|---|---|
| `GMAIL_ADDRESS` | 送信元Gmail |
| `GMAIL_APP_PASSWORD` | Gmailアプリパスワード |
| `TO_ADDRESSES` | 宛先 |
| `GEMINI_API_KEY` | Gemini APIキー（要約ON） |

---

## 現在のファイル構成

```
news-digest-tool/
├── config.yaml              ← キーワード・RSS・配信設定
├── requirements.txt
├── src/
│   ├── main.py              ← エントリポイント
│   ├── collect.py           ← RSS収集（Google News + MONOist）
│   ├── filter.py            ← キーワードフィルタ + Gemini要約
│   └── email_sender.py      ← メールHTML + 図解HTML生成
│       ├── build_html()         ← メール用（タイトル+★のみ）
│       ├── build_digest_html()  ← 図解ページ用（★ここを改修）
│       └── build_empty_html()   ← 記事なし時のメール
└── .github/workflows/
    └── daily.yml            ← 毎週月曜実行・Artifact保存90日
```
