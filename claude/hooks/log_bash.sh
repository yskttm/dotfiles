#!/bin/bash
# Claude Code の Bash ツール実行履歴をログに記録する hook

mkdir -p ~/.claude/logs

python3 - <<'EOF'
import sys, json, datetime

try:
    d = json.load(sys.stdin)
    cmd = d.get("command", "")
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_path = __import__("os").path.expanduser("~/.claude/logs/bash_history.log")
    with open(log_path, "a") as f:
        f.write(f"{timestamp} {cmd}\n")
except Exception:
    pass
EOF
