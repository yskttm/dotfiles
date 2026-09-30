#!/bin/bash

set -euo pipefail

DOTFILES_DIR="$1"
BREW_PREFIX="$2"
COMPOSE_PLUGIN="$BREW_PREFIX/lib/docker/cli-plugins/docker-compose"
DOCKER_CONFIG="$HOME/.docker/config.json"
COMPOSE_LINK="$HOME/.docker/cli-plugins/docker-compose"

if [ ! -f "$COMPOSE_PLUGIN" ]; then
  echo "Compose plugin が見つかりません: $COMPOSE_PLUGIN" >&2
  exit 1
fi

# 認証情報を失わずに、以前の dotfiles 管理から端末内のファイルへ移行する。
if [ -L "$DOCKER_CONFIG" ] && \
   [ "$(readlink "$DOCKER_CONFIG")" = "$DOTFILES_DIR/docker/config.json" ]; then
  if [ -f "$DOCKER_CONFIG" ]; then
    LOCAL_CONFIG=$(mktemp "$HOME/.docker/config.json.XXXXXX")
    trap 'rm -f "$LOCAL_CONFIG"' EXIT
    cp "$DOCKER_CONFIG" "$LOCAL_CONFIG"
    chmod 600 "$LOCAL_CONFIG"
    mv -f "$LOCAL_CONFIG" "$DOCKER_CONFIG"
    echo "Docker config を端末内の通常ファイルへ移行しました。"
  else
    rm "$DOCKER_CONFIG"
    echo "以前の Docker config のリンク切れを解消しました。"
  fi
fi

mkdir -p "$(dirname "$COMPOSE_LINK")"
if [ -L "$COMPOSE_LINK" ] && \
   [ "$(readlink "$COMPOSE_LINK")" = "$COMPOSE_PLUGIN" ]; then
  echo "Compose plugin は設定済みです。"
elif [ -e "$COMPOSE_LINK" ] || [ -L "$COMPOSE_LINK" ]; then
  echo "既存の Compose plugin を保持します: $COMPOSE_LINK"
else
  ln -s "$COMPOSE_PLUGIN" "$COMPOSE_LINK"
  echo "Compose plugin のリンクを作成しました。"
fi
