# 引き継ぎ：Gemini 要約まわり（別チャット用）

## いま終わっていること（外観・UI）

- **手動テンプレ HTML**（特許ダイジェスト手オフの例として作成済み）:
  - パス: `output/patent-digest-handoff-page.html`
  - **モバイル優先**の長ページ、`<details>` で折りたたみ（一覧はタイトル＋関連度、展開で要約＋リンク枠）。
- **関連度の見せ方（確定）**
  - `data-relevance-stars="3" | "4" | "5"` を各 `<details>` に付与。
  - **ピル**: `commit-report-tool` の `.claude/skills/diagram-guidelines/SKILL.md` 内「ブランチタグのHTML」インライン版と同型（淡背景＋丸ドット＋★表記）。
  - **色**: ★3＝**緑**（`green-*`）、★4＝**青**（`blue-*`）、★5＝**橙**（`orange-*`）。関連度の**説明文本文**は `text-zinc-600`（ピルと枠だけ色）。
  - **カード枠**: `border-*-200` + `ring-*-200/80`。展開部の **上罫線** `border-t` も同系色。
- **ニュース版のイメージ**: 中身は後から **ニュース1件＝1カード**に差し替え。同じマークアップ規約で生成すればよい。

## このチャットでやるべきこと（Gemini 要約）

1. **プロンプト設計**
   - 入力に何を渡すか（タイトル、抜粋、ソース名、URL、既存スコアなど）。
   - 出力形式（プレーン要約、見出し付き、文字数上限、禁止事項・ハルシネーション対策）。
   - **日本語**トーン（読者：化学業界ニュース想定なら `digest.html` の文体も参考にできる）。
2. **関連度 ★3/4/5 と要約の整合**
   - スコアやルールから `data-relevance-stars` を決める条件を文書化。
   - 生成 HTML に **ピル＋枠色**が自動で付くよう、テンプレまたは生成ロジック側の仕様を決める。
3. **API・実装パス（リポジトリに応じて）**
   - `google-genai` 等、既存ツールに合わせるなら [chem-digest-tool](https://github.com/jpikemonaddress2-ai/chem-digest-tool) の `filter.py`（キーワード＋Gemini 要約）を参照する前提でよい（ローカルにクローンがあるなら直接読む）。
   - **特許版**の要約観点は [commit-report-tool の patent-digest-handoff.md](../commit-report-tool/patent-digest-handoff.md)（出願人・権利範囲・IPC 等）をニュース／特許どちら向けにするかで転用可否を判断。
4. **成果物の置き場**
   - 生成 HTML の出力はこれまでどおり **`output/`**（例: `digest-YYYY-MM-DD.html`）を想定。手動テンプレは `output/patent-digest-handoff-page.html` を参照用に残すか、生成物にマージするかは実装時に決める。

## 読むとよいファイル（パスはローカル例）

| 用途 | パス |
|------|------|
| UI 規約の実物 | `C:\Users\jpike\src\news-digest-tool\output\patent-digest-handoff-page.html` |
| 特許ツールの手オフ（メタデータ・プロンプト観点） | `C:\Users\jpike\src\commit-report-tool\patent-digest-handoff.md` |
| 図解スキル（ピルの HTML パターン） | `C:\Users\jpike\src\commit-report-tool\.claude\skills\diagram-guidelines\SKILL.md` |

## 新チャットへの一言プロンプト例

```
news-digest-tool の gemini-summary-handoff.md を読んで、
Gemini 要約のプロンプト・入出力仕様・★3/4/5 と data-relevance-stars の対応を詰める。
UI は output/patent-digest-handoff-page.html の規約に合わせる。
```

## メモ

- 外観・Tailwind CDN・静的単一 HTML は **確定済み**。次は **要約品質と生成パイプライン**がボトルネック。
- `digest-page-handoff.md` がリポジトリ内にある場合は、既存の digest 生成フローと矛盾しないよう併読すること。
