---
name: check-dotfiles
description: Brew パッケージの管理状況と、ホームディレクトリ配下の dotfiles 候補を確認する
---

以下の手順で dotfiles の状態を確認し、結果を報告してください。

## 1. Brew パッケージの確認

### 1-1. Brewfile に未記載だがインストール済みの formula
```bash
brew leaves | sort > /tmp/installed_leaves.txt
grep "^brew " ~/dotfiles/Brewfile | sed 's/brew "//;s/".*//' | sort > /tmp/brewfile_formulas.txt
comm -23 /tmp/installed_leaves.txt /tmp/brewfile_formulas.txt
```

### 1-2. tap 経由でインストール済みのパッケージが Brewfile の tap として記載されているか確認
```bash
brew tap
grep "^tap " ~/dotfiles/Brewfile 2>/dev/null || echo "tap の記載なし"
```

### 1-3. Brewfile に記載されているが未インストールのパッケージ
```bash
brew bundle check --file=~/dotfiles/Brewfile --verbose 2>/dev/null | grep -v "^Using"
```

## 2. シンボリックリンクの確認

`~/dotfiles/install.sh` に記載されているシンボリックリンクが全て正しく作成されているか確認する。
各リンク先が `-> ~/dotfiles/...` を指しているかチェックし、壊れているリンクや未作成のものを報告する。

## 3. dotfiles 候補の確認

以下の観点でホームディレクトリを調査し、dotfiles 管理に追加する価値があるものを提案する：

- `~/.config/` 配下で未管理のディレクトリ（既存のシンボリックリンク以外）
- ホームディレクトリ直下のドットファイル（既存のシンボリックリンク以外）
- 頻繁に更新されており、マシン移行時に持ち運びたそうなもの

以下は管理不要なので除外する：
- `.DS_Store`, `.Trash`, `.bash_history`, `.zsh_history`, `.zsh_sessions`, `.bash_sessions`
- `.lesshst`, `.viminfo`, `.irb_history`, `.CFUserTextEncoding`, `.claude.json`
- キャッシュ系ディレクトリ（`.cache`, `.cargo`, `.npm` 等）
- 認証情報系（`.aws`, `.gnupg`, `.ssh`, `.kube` 等）
- クラウド同期するツール（`raycast`, `warp`, `vscode` 等）

## 報告フォーマット

結果を以下の構造で報告する：

### Brew
- **Brewfile 未記載のインストール済みパッケージ**: 追加候補をリスト
- **tap の整合性**: tap 経由パッケージの Brewfile 記載漏れ
- **未インストールのパッケージ**: 本当に未インストールか `/Applications` も確認

### シンボリックリンク
- **正常**: 件数
- **問題あり**: 具体的なパス

### dotfiles 追加候補
- 候補をリストアップし、追加する価値があるか簡単にコメント

## 4. アクション選択

報告の最後に、dotfiles への追加・更新をユーザーが選びやすいよう以下の形式で提示する：

```
次のアクションを選んでください（複数選択可）：

[Brew]
  A. ollama を Brewfile に追加する

[dotfiles 追加候補]
  B. ~/.config/foo を dotfiles に追加する
  C. ~/.bar を dotfiles に追加する

[その他]
  Z. 何もしない
```

- 番号・記号で選べるようにする
- 報告した内容のみを選択肢に挙げる（空の場合はセクションごと省略）
