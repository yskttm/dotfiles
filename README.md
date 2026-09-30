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
4. Docker Compose plugin のシンボリックリンクを `~/.docker/cli-plugins/` に作成
5. mise で言語ランタイムとツールをインストール

### Docker / Colima

Docker CLI、Compose、Colima は Homebrew でインストールします。Compose plugin は
`brew --prefix` から取得した配置先へリンクするため、Homebrew の配置先を固定する必要はありません。
既存の Compose plugin がある場合は上書きしません。

`~/.docker/config.json` は認証情報を含むため、Git 管理せず各端末で管理します。
以前の dotfiles 向けシンボリックリンクが残っている端末では、更新前にリンク先の内容を端末内の通常ファイルへコピーし、リンクを置き換えてください。

セットアップ後、次のコマンドで起動と接続を確認できます。

```sh
colima start
docker context show  # colima が選択されていることを確認
docker info
docker compose version
```

Colima の設定は `colima/default/colima.yaml` で管理します。
`Brewfile` の `restart_service: :changed` により、Colima のインストール・更新時にはサービスを起動または再起動します。

Compose plugin のセットアップのテストは `python3 install.test.py` で実行できます。

## マニュアル運用

### Kanary

- <https://kanary.download/ja> から直接ダウンロードしてインストール（Homebrew・Mac App Store 未対応）
- 設定は少ないため手動で再設定する（⌘ キー単体押しでの英数・かな切り替えに使用）

### Raycast

- Raycast の設定は手動で export/import
- 設定ファイルはパスワードが必須

### VS Code, Warp, Chrome, etc

- Cloud sync 機能を利用
