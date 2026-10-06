---
name: daily-log
description: 退勤時に手動で実行する。今日のClaude Codeセッションを要約し、Notionの「Claude Code ログ」DBに送る。
argument-hint: "[YYYY-MM-DD]（省略時は今日）"
disable-model-invocation: true
allowed-tools: Bash(python3 ~/.claude/skills/daily-log/daily_log.py:*), Read, Edit, Write, ToolSearch, mcp__claude_ai_Notion__notion-query-data-sources, mcp__claude_ai_Notion__notion-create-pages, mcp__claude_ai_Notion__notion-update-page
---

# daily-log: 今日の Claude Code セッションを Notion に送る

ユーザーが退勤時に `/daily-log` で起動する。対象日は引数 `$ARGUMENTS`（空なら今日）。
途中で確認は取らず、最後まで進めてから結果を報告する。

## 初回セットアップ

送信先などワークスペース固有の値は、このスキルと同じディレクトリの `config.json`（`.gitignore` で管理外）に置く。

```json
{"data_source_url": "collection://<Notion DB の data source ID>", "report_time": "22:52"}
```

`report_time` は日報の自動生成時刻。不要なら省略してよい。

## 手順

1. **集める**
   ```bash
   python3 ~/.claude/skills/daily-log/daily_log.py collect $ARGUMENTS
   ```
   出力に表示される `transcripts:`（.md）と `fill in:`（.json）のパスを控える。
   `sessions: 0` なら「今日のセッションは見つかりませんでした」と伝えて終了。

2. **読む**
   `.md` を Read で読む。大きいときは offset/limit で分けて全部読む。
   各セッションは `## [番号] リポジトリ (ブランチ) 開始–終了` で区切られている。

3. **要約を書き込む**
   `.json` の各セッションの `title` と `summary` を埋める（Edit で書き換える。他のフィールドは変えない）。
   - `title`: 作業内容が分かる日本語30文字以内。例「PROJ-123 rakeタスク削除」
   - `summary`: 「- 」で始まる箇条書き3〜5行を改行区切りで。
     何を依頼し、何をして、結果どうなったか（**完了 / 途中 / 未解決** のどれかを必ず書く）。
     変更したファイル、コミット、PR番号、チケット番号（PROJ-123 など）があれば含める。
   - 中身のない短いセッション（挨拶だけ、設定確認だけ等）は `"skip": true` にする。
   - トークン、パスワード、APIキー、個人情報などの秘密情報は絶対に書かない。

4. **送る（Notion MCP）**
   ```bash
   python3 ~/.claude/skills/daily-log/daily_log.py payload $ARGUMENTS
   ```
   出力 JSON の `pages[].properties` を**そのまま**使う（値を書き換えない）。
   `✗ [番号] 秘密情報の可能性` で止まったら（exit 2、何も出力されない）、その番号の `title` / `summary` から
   該当部分を削るか一般的な言葉に言い換えて `.json` を直し、`payload` をやり直す。チェックを回避する目的で
   文字列を分割・伏せ字にして同じ値を残すことはしない。
   Notion MCP のツールが未ロードなら、ToolSearch で
   `select:mcp__claude_ai_Notion__notion-query-data-sources,mcp__claude_ai_Notion__notion-create-pages,mcp__claude_ai_Notion__notion-update-page`
   を読み込む。
   1. 既存行を 1 回で取得する（`notion-query-data-sources`、rows mode）:
      `data_source_url` は出力の値、filter は `セッションID`（propertyType `text`）が `key_suffix` で終わる（`string_ends_with`）、limit 100。
   2. 結果の `セッションID` と `properties.セッションID` が一致するページは
      `notion-update-page`（command `update_properties`、page_id は既存行の url の ID）で更新する。
   3. 一致しないものは `notion-create-pages` にまとめて渡して追加する
      （parent: `{"type": "data_source_id", "data_source_id": <collection:// を除いた ID>}`、content は付けない、allow_async は false）。
   同じ日に再実行すると、同じ行が更新される（重複しない）。

5. **報告する**
   送ったセッションを「時間帯 / リポジトリ / タイトル / 状態」の表で短く見せる。
   エラーが出たら内容を伝える（認証エラーなら `/mcp` で claude.ai Notion の接続を確認するよう案内する）。
   payload 出力の `report_time` が空でなければ、最後に「{report_time}の日報に反映されます」と一言添える
   （{report_time} 以降に実行した場合は「今日の日報の自動生成は終わっているので、翌日以降に手動で再生成が必要」と伝える）。
