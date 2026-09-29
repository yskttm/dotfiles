# dotfiles

macOS の開発環境設定を管理する dotfiles

## セットアップ

```bash
git clone https://github.com/yskttm/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh
```

`install.sh` は以下を実行します：

1. dotfiles のシンボリックリンクを `~/` に作成
2. Homebrew が未インストールの場合はインストール
3. `Brewfile` をもとにアプリケーションをインストール
4. mise で言語ランタイムとツールをインストール

## Agent Toolkit for AWS

AWS の skills は Codex と Claude Code の `aws-core` plugin で管理します。`install.sh` は plugin をインストールしないため、各ツールで次のコマンドを実行してください。

```bash
codex plugin marketplace add aws/agent-toolkit-for-aws
codex plugin add aws-core@agent-toolkit-for-aws
claude plugin install aws-core@claude-plugins-official --scope user
```

Claude Code は `claude/settings.json` の `AWS_PROFILE` で `personal` profile を指定し、plugin 付属の AWS MCP を使用します。Codex は既存の AWS MCP 接続で `personal` profile を指定し、plugin 付属の MCP を無効化しています。Codex の MCP 設定はこの repository では管理していません。

## マニュアル運用

### Kanary

- <https://kanary.download/ja> から直接ダウンロードしてインストール（Homebrew・Mac App Store 未対応）
- 設定は少ないため手動で再設定する（⌘ キー単体押しでの英数・かな切り替えに使用）

### Raycast

- Raycast の設定は手動で export/import
- 設定ファイルはパスワードが必須

### VS Code, Warp, Chrome, etc

- Cloud sync 機能を利用
