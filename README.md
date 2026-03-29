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

## マニュアル運用

### Raycast

Raycast の設定は Cloud Sync が有料プランのため、手動で export/import します。

**設定を保存する（変更のたびに実行）**

1. Raycast を開く → `Settings → Advanced → Export Settings`
2. `Raycast-confg-export.rayconfig` として `~/dotfiles/` に上書き保存
3. `git add` して commit

**新しい Mac に移行する場合**

1. `git clone` 後、Raycast を開く → `Settings → Advanced → Import Settings`
2. `~/dotfiles/Raycast-confg-export.rayconfig` を選択
