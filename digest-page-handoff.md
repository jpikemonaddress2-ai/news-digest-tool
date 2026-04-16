# 引き継ぎ：業界ニュース図解ページ デザイン改修

## 背景・目的

`news-digest-tool` は週1回、化学業界ニュースを収集してメール配信するツール。
メールはタイトル＋★のシンプルな一覧のみ。
詳細内容（要約・リンク）を見るための **図解ページ HTML** を別途生成している。

この図解ページのデザインを、現在の地味なテーブル形式から
**モダンでビジュアルリッチな形式**にリデザインする。

---

## リポジトリ

```
C:\Users\jpike\src\news-digest-tool
https://github.com/jpikemonaddress2-ai/news-digest-tool
```

---

## 現在の仕組み

### 図解ページの生成場所

`src/email_sender.py` の `build_digest_html()` 関数（280行目付近）が生成している。

```
email_sender.py
  └── build_digest_html()   ← ここを改修する
        └── _digest_article_table()  ← 記事1件分のHTML
```

### 呼び出し元（src/main.py）

```python
digest_path = Path("output") / f"digest-{now.strftime('%Y-%m-%d')}.html"
digest_html_content = build_digest_html(filtered, keywords, config, now, total_collected)
digest_path.write_text(digest_html_content, encoding="utf-8")
```

毎週の自動実行で `output/digest-2026-04-21.html` のような日付付きファイルを生成し、
GitHub Actions の Artifacts に90日間保存される。

---

## 渡されるデータ（関数シグネチャ）

```python
def build_digest_html(
    articles: list[Article],   # フィルタ後の配信記事リスト（0件の場合もある）
    keywords: list[str],       # config.yaml の interest_keywords
    config: dict,              # config.yaml 全体
    report_date: datetime,     # 実行日時（UTC）
    total_collected: int = 0,  # RSS収集総数（フィルタ前）
) -> str:
```

### Article データ構造

```python
@dataclass
class Article:
    source_type: str          # 常に "rss"
    source_name: str          # フィード名（例: "Google News：化学業界"）
    title: str                # 記事タイトル
    summary: str              # RSS原文の概要
    url: str                  # 記事URL
    published: Optional[datetime] = None  # 公開日時（UTC）
    score: Optional[int] = None           # 関連度スコア 3〜5
    score_reason: Optional[str] = None    # "キーワード N件マッチ（xxx）"
    ai_summary: Optional[str] = None      # Gemini日本語要約（未設定時はNone）
```

### 典型的なデータ例（週5〜10件）

```python
Article(
    source_name="Google News：化学業界",
    title="化学メーカー大手3社が原料高騰で値上げ発表",
    url="https://...",
    score=5,
    ai_summary="三菱ケミカルなど化学大手3社が..."  # Gemini要約（あれば）
    summary="..."  # RSS原文（ai_summaryがNoneのときに使う）
)
```

---

## デザイン要件

### 参考スタイル

`commit-report-tool` の図解ページスタイルを参考にする：
- `C:\Users\jpike\src\commit-report-tool\.claude\skills\diagram-guidelines\examples\daily-summary.html`

### 技術方針（メールと異なりブラウザ表示専用なのでモダンCSSが使える）

- **Tailwind CSS CDN** 使用可（`<script src="https://cdn.tailwindcss.com"></script>`）
- Flexbox / Grid 使用可
- グラデーション・box-shadow 使用可
- 固定幅（420px〜600px）でも全幅でもOK

### 盛り込む内容

| セクション | 内容 |
|---|---|
| ヘッダー | タイトル「業界ニュースダイジェスト」・日付 |
| 統計バー | 収集件数 / 配信件数 / ソース数 |
| 記事カード（繰り返し） | ★スコア・ソース名・タイトル（リンク）・要約 |
| 0件時 | 「今週の配信記事はありませんでした」メッセージ |

### スコア別カラー（現行踏襲でOK・変更も可）

| スコア | カラーイメージ |
|---|---|
| ★5 | 赤系（最重要） |
| ★4 | 青系 |
| ★3 | 緑系 |

---

## 改修作業

### やること

`src/email_sender.py` の以下の2関数を書き換えるだけ：

1. `build_digest_html()` → Tailwind使ったモダンHTMLを返す
2. `_digest_article_table()` → 不要になれば削除してOK

### やらないこと

- `build_html()`（メール用・シンプル版）は触らない
- `main.py` は触らない
- `collect.py` / `filter.py` は触らない

---

## 動作確認方法

```bash
cd C:\Users\jpike\src\news-digest-tool
python src/main.py --dry-run
# → output/digest-YYYY-MM-DD.html が生成される
# ブラウザで開いて確認
```

---

## 完成後

`git add src/email_sender.py` → `git commit` → `git push` で完了。
次回 GitHub Actions 実行時から新デザインの図解ページが生成される。
