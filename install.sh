#!/bin/bash

set -e

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$HOME/.dotfiles_backup/$(date +%Y%m%d_%H%M%S)"

echo "dotfiles のセットアップを開始します..."
echo "dotfiles ディレクトリ: $DOTFILES_DIR"

# ホームディレクトリのドットファイルをシンボリックリンクで展開
link_dotfile() {
  local src="$1"
  local dest="$2"

  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    mkdir -p "$BACKUP_DIR"
    echo "バックアップ: $dest -> $BACKUP_DIR/"
    cp -r "$dest" "$BACKUP_DIR/"
    rm -rf "$dest"
  fi

  mkdir -p "$(dirname "$dest")"
  ln -sfn "$src" "$dest"
  echo "リンク作成: $dest -> $src"
}

# ~/. ファイル
link_dotfile "$DOTFILES_DIR/.zshrc"       "$HOME/.zshrc"
link_dotfile "$DOTFILES_DIR/.gitconfig"   "$HOME/.gitconfig"
link_dotfile "$DOTFILES_DIR/.vimrc"       "$HOME/.vimrc"
link_dotfile "$DOTFILES_DIR/.bunfig.toml" "$HOME/.bunfig.toml"

# ~/.config/ 配下
link_dotfile "$DOTFILES_DIR/.config/git/ignore"          "$HOME/.config/git/ignore"
link_dotfile "$DOTFILES_DIR/.config/mise/config.toml"    "$HOME/.config/mise/config.toml"
link_dotfile "$DOTFILES_DIR/.config/gh/config.yml"       "$HOME/.config/gh/config.yml"
link_dotfile "$DOTFILES_DIR/.config/karabiner/karabiner.json" "$HOME/.config/karabiner/karabiner.json"

# ~/.cspell/ 配下
link_dotfile "$DOTFILES_DIR/.cspell/custom-dictionary.txt" "$HOME/.cspell/custom-dictionary.txt"


echo ""
echo "シンボリックリンクの作成が完了しました。"

# Homebrew のインストール確認
if ! command -v brew &>/dev/null; then
  echo ""
  echo "Homebrew をインストールしています..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Brewfile からアプリをインストール
echo ""
echo "brew bundle install を実行しています..."
brew bundle install --file="$DOTFILES_DIR/Brewfile"

echo ""
echo "セットアップ完了！"
