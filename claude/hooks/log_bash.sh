#!/bin/bash
# Claude Code の Bash ツール実行履歴をログに記録する hook

mkdir -p ~/.claude/logs

python3 -c "
import sys, json, datetime, os

try:
    d = json.load(sys.stdin)
    cmd = d.get('tool_input', {}).get('command', '')
    timestamp = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
    log_path = os.path.expanduser('~/.claude/logs/bash_history.log')
    with open(log_path, 'a') as f:
        f.write(f'{timestamp} {cmd}\n')
except Exception:
    pass
"
