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

## マニュアル運用

### Raycast

- Raycast の設定は手動で export/import
- 設定ファイルはパスワードが必須

### VS Code, Warp, Chrome, etc

- Cloud sync 機能を利用
