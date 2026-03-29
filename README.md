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

Raycast の設定は手動で export/import します。

**設定を保存する（変更のたびに実行）**

1. Raycast を開く → `Settings → Advanced → Export Settings`
2. `raycast-confg.rayconfig` として `~/dotfiles/` に上書き保存

**新しい Mac に移行する場合**

1. `git clone` 後、Raycast を開く → `Settings → Advanced → Import Settings`
2. `~/dotfiles/raycast-confg.rayconfig` を選択
3. password を入力

### VS Code, Warp, Chrome, etc

Cloud sync 機能を利用
