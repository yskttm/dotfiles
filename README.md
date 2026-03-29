# dotfiles

macOS の開発環境設定を管理する dotfiles です。

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

## 管理対象ファイル

### dotfiles (`~/`)

| ファイル | 説明 |
|---|---|
| `.zshrc` | zsh 設定（エイリアス、PATH、mise/brew の初期化） |
| `.gitconfig` | Git グローバル設定 |
| `.vimrc` | Vim 設定 |
| `.bunfig.toml` | Bun パッケージマネージャ設定 |

### `~/.config/`

| パス | 説明 |
|---|---|
| `git/ignore` | グローバル .gitignore |
| `mise/config.toml` | mise によるランタイムバージョン管理設定 |
| `zellij/config.kdl` | Zellij ターミナルマルチプレクサ設定 |
| `gh/config.yml` | GitHub CLI 設定 |
| `karabiner/karabiner.json` | Karabiner-Elements キーボードカスタマイズ |

### `~/.cspell/`

| パス | 説明 |
|---|---|
| `custom-dictionary.txt` | cspell カスタム辞書 |

### アプリケーション (`Brewfile`)

Homebrew bundle で管理しています。

- **formula**: `mise`, `gh`, `git`, `eza`, `ripgrep`, `zellij`, `jq`, `k9s`, `stern` など
- **cask**: `amazon-workspaces`, `gcloud-cli`, `slack-cli`
- **Mac App Store**: `mas` でインストール（`Brewfile` に `mas` 行を追記して管理）

## 新しい Mac に移行する場合の注意点

- VS Code の設定は Settings Sync で管理しています（dotfiles 管理外）
-Mac App Store アプリは `Brewfile` の `mas` 行に App ID を追記することで管理できます
- `brew bundle dump --force` で現在の環境から `Brewfile` を再生成できます
