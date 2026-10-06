#!/usr/bin/env python3
"""
Helper for the daily-log skill (Claude Code and Codex).

  daily_log.py collect [YYYY-MM-DD]
      Scans Claude Code (~/.claude/projects/*/*.jsonl) and Codex
      (~/.codex/sessions/YYYY/MM/DD/*.jsonl) sessions with activity on that day
      (local time, default today), and writes:
        ~/.config/cc-daily-log/out/<date>.md    condensed transcripts to summarize
        ~/.config/cc-daily-log/out/<date>.json  one entry per session; fill in
                                                "title" and "summary" (or "skip": true)
  daily_log.py payload [YYYY-MM-DD]
      Prints the filled-in JSON as Notion page properties (JSON) for the Notion MCP.
      Refuses (exit 2) if a title/summary looks like it contains a credential.
      The agent upserts them into the "AIログ" database, keyed by セッションID
      (= session_id:date), so re-running the same day updates the same rows.
      The ツール property tells Claude Code and Codex sessions apart.
"""
from __future__ import annotations   # macOS system python3 is 3.9

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"
CODEX_SESSIONS_DIR = Path.home() / ".codex" / "sessions"
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"   # gitignored: workspace-specific values
DATA_DIR = Path.home() / ".config" / "cc-daily-log"
OUT_DIR = DATA_DIR / "out"
PER_SESSION_CHARS = 12000   # condensed transcript kept per session (head + tail)
SKILL_COMMAND = "daily-log"  # sessions that only ran this command are skipped
CLAUDE, CODEX = "Claude Code", "Codex"   # values of the ツール property


# ------------------------------------------------------------------ helpers
def local_day(arg: str | None) -> dt.date:
    return dt.date.fromisoformat(arg) if arg else dt.datetime.now().astimezone().date()


def parse_ts(ts: str | None) -> dt.datetime | None:
    if not ts:
        return None
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    if isinstance(content, list):
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "text":
                parts.append(c.get("text", ""))
            elif c.get("type") == "tool_use":
                inp = c.get("input", {}) or {}
                target = inp.get("file_path") or inp.get("command") or inp.get("pattern") or inp.get("url") or ""
                parts.append(f"[tool:{c.get('name', '')} {str(target)[:150]}]")
    return "\n".join(p for p in parts if p)


def git(cwd: str, *args: str) -> str:
    if not cwd or not Path(cwd).is_dir():
        return ""
    try:
        out = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def repo_from_url(url: str) -> str:
    name = url.rstrip("/")
    if name.endswith(".git"):
        name = name[:-4]
    return "/".join(name.replace(":", "/").split("/")[-2:])


def repo_name(cwd: str) -> str:
    remote = git(cwd, "config", "--get", "remote.origin.url")
    if remote:
        return repo_from_url(remote)
    top = git(cwd, "rev-parse", "--show-toplevel")
    return Path(top or cwd or "?").name


# ------------------------------------------------------------------ collect
def events(path: Path):
    try:
        f = path.open(encoding="utf-8")
    except OSError:
        return
    with f:
        for raw in f:
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(ev, dict):
                yield ev


def read_claude_session(path: Path, start: dt.datetime, end: dt.datetime) -> dict | None:
    lines, prompts = [], 0
    first = last = None
    session_id = path.stem
    cwd = branch = ""
    for ev in events(path):
        ts = parse_ts(ev.get("timestamp"))
        if ts is None or not (start <= ts < end):
            continue
        session_id = ev.get("sessionId") or session_id
        cwd = ev.get("cwd") or cwd
        branch = ev.get("gitBranch") or branch
        if ev.get("isMeta") or ev.get("isSidechain"):
            continue
        msg = ev.get("message") or {}
        kind = ev.get("type")
        if kind == "user":
            content = msg.get("content")
            if isinstance(content, list) and any(
                isinstance(c, dict) and c.get("type") == "tool_result" for c in content
            ):
                continue
            t = text_of(content).strip()
            if not t or t.startswith("<local-command") or t.startswith("<command-message"):
                continue
            if t.startswith("<command-name>"):
                if SKILL_COMMAND in t:
                    continue
                t = "（コマンド）" + t[:200]
            else:
                prompts += 1
            first = first or ts
            last = ts
            lines.append(f"[{ts:%H:%M}] USER: {t[:2000]}")
        elif kind == "assistant":
            t = text_of(msg.get("content")).strip()
            if t:
                first = first or ts
                last = ts
                lines.append(f"[{ts:%H:%M}] CLAUDE: {t[:1200]}")
    if prompts == 0:
        return None
    return finish_session(CLAUDE, session_id, cwd, branch, repo_name(cwd) if cwd else "", first, last, prompts, lines)


def codex_text(item: dict) -> str:
    return "\n".join(c.get("text", "") for c in item.get("content") or []
                     if isinstance(c, dict) and c.get("type") in ("text", "Text")).strip()


def read_codex_session(path: Path, start: dt.datetime, end: dt.datetime) -> dict | None:
    lines, prompts = [], 0
    first = last = None
    session_id, cwd, branch, repo = path.stem, "", "", ""
    for ev in events(path):
        payload = ev.get("payload") or {}
        kind = ev.get("type")
        if kind == "session_meta":
            source = payload.get("source")
            # subagents and guardian reviews get their own files; the parent session already covers them
            if payload.get("thread_source", "user") != "user" or (isinstance(source, dict) and "subagent" in source):
                return None
            session_id = payload.get("session_id") or payload.get("id") or session_id
            cwd = payload.get("cwd") or cwd
            git_info = payload.get("git") or {}
            branch = git_info.get("branch") or ""
            repo = repo_from_url(git_info["repository_url"]) if git_info.get("repository_url") else ""
            continue
        ts = parse_ts(ev.get("timestamp"))
        if ts is None or not (start <= ts < end):
            continue
        if kind == "turn_context":
            cwd = payload.get("cwd") or cwd
            continue
        # item_completed holds what the user typed; role=user response_items also carry injected AGENTS.md etc.
        if kind != "event_msg" or payload.get("type") != "item_completed":
            continue
        item = payload.get("item") or {}
        item_type = item.get("type")
        if item_type == "UserMessage":
            t = codex_text(item)
            invoked_self = any(isinstance(c, dict) and c.get("type") == "skill" and c.get("name") == SKILL_COMMAND
                               for c in item.get("content") or [])
            if not t or invoked_self or t.startswith(f"${SKILL_COMMAND}"):
                continue
            prompts += 1
            line = f"USER: {t[:2000]}"
        elif item_type == "AgentMessage":
            t = codex_text(item)
            if not t:
                continue
            line = f"CODEX: {t[:1200]}"
        elif item_type == "CommandExecution":
            command = item.get("command") or []
            line = f"CODEX: [tool:exec {str(command[-1] if command else '')[:150]}]"
        else:
            continue
        first = first or ts
        last = ts
        lines.append(f"[{ts:%H:%M}] {line}")
    if prompts == 0:
        return None
    return finish_session(CODEX, session_id, cwd, branch, repo or (repo_name(cwd) if cwd else ""),
                          first, last, prompts, lines)


def finish_session(tool: str, session_id: str, cwd: str, branch: str, repo: str,
                   first: dt.datetime, last: dt.datetime, prompts: int, lines: list[str]) -> dict:
    body = "\n".join(lines)
    if len(body) > PER_SESSION_CHARS:
        half = PER_SESSION_CHARS // 2
        body = body[:half] + "\n…（中略）…\n" + body[-half:]
    commits = ""
    if cwd:
        email = git(cwd, "config", "user.email")
        args = ["log", "--all", f"--since={first.isoformat()}", f"--until={(last + dt.timedelta(minutes=10)).isoformat()}",
                "--pretty=format:%h %s", "-n", "30"]
        if email:
            args.insert(2, f"--author={email}")
        commits = git(cwd, *args)
    return {
        "tool": tool,
        "session_id": session_id,
        "repo": repo,
        "branch": branch,
        "cwd": cwd,
        "start": first.isoformat(timespec="seconds"),
        "end": last.isoformat(timespec="seconds"),
        "prompts": prompts,
        "commits": commits,
        "body": body,
    }


def gather_sessions(day: dt.date, claude_dir: Path, codex_dir: Path) -> list[dict]:
    tz = dt.datetime.now().astimezone().tzinfo
    start = dt.datetime.combine(day, dt.time.min, tzinfo=tz)
    end = start + dt.timedelta(days=1)
    sources = [
        (claude_dir.glob("*/*.jsonl"), read_claude_session),   # top level only: skips subagent transcripts
        # files sit under the day the session started, so rely on mtime rather than the folder date
        (codex_dir.glob("*/*/*/*.jsonl"), read_codex_session),
    ]
    sessions = []
    for paths, reader in sources:
        for path in sorted(paths):
            try:
                if dt.datetime.fromtimestamp(path.stat().st_mtime, tz) < start:
                    continue
            except OSError:
                continue
            s = reader(path, start, end)
            if s:
                sessions.append(s)
    # a resumed session can live in two files; merge by session_id
    merged: dict[tuple[str, str], dict] = {}
    for s in sorted(sessions, key=lambda x: x["start"]):
        key = (s["tool"], s["session_id"])
        m = merged.get(key)
        if m:
            m["body"] += "\n" + s["body"]
            m["prompts"] += s["prompts"]
            m["end"] = max(m["end"], s["end"])
            m["commits"] = "\n".join(x for x in (m["commits"], s["commits"]) if x)
        else:
            merged[key] = s
    return list(merged.values())


def collect(day: dt.date) -> None:
    sessions = gather_sessions(day, PROJECTS_DIR, CODEX_SESSIONS_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # transcripts quote whole conversations, so keep them away from other local users
    DATA_DIR.chmod(0o700)
    OUT_DIR.chmod(0o700)
    md_path, json_path = OUT_DIR / f"{day}.md", OUT_DIR / f"{day}.json"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# Claude Code / Codex セッション {day}（{len(sessions)}件）\n\n")
        for i, s in enumerate(sessions, 1):
            f.write(f"## [{i}] {s['tool']} / {s['repo'] or '-'} ({s['branch'] or '-'}) {s['start'][11:16]}–{s['end'][11:16]}\n")
            f.write(f"session_id: {s['session_id']} / cwd: {s['cwd']} / 依頼数: {s['prompts']}\n")
            f.write(f"コミット:\n{s['commits'] or '(なし)'}\n\n{s['body']}\n\n")
    entries = [{
        "index": i, "tool": s["tool"], "session_id": s["session_id"], "repo": s["repo"], "branch": s["branch"],
        "start": s["start"], "end": s["end"], "title": "", "summary": "", "skip": False,
    } for i, s in enumerate(sessions, 1)]
    json_path.write_text(json.dumps({"date": str(day), "sessions": entries}, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    # write_text keeps the mode of an existing file, so tighten after writing
    md_path.chmod(0o600)
    json_path.chmod(0o600)
    size = md_path.stat().st_size
    print(f"date: {day}")
    print(f"sessions: {len(sessions)}")
    print(f"transcripts: {md_path} ({size // 1024} KB)")
    print(f"fill in: {json_path}")
    for s in sessions:
        print(f"  - {s['start'][11:16]}–{s['end'][11:16]} {s['tool']} {s['repo'] or '-'} ({s['branch'] or '-'}) 依頼{s['prompts']}件")


# ------------------------------------------------------------------ payload
TEXT_LIMIT = 1990   # Notion rich text allows 2000 chars per value

# The summaries are written by Claude; this is a mechanical last line of defence before they leave the Mac.
SECRET_PATTERNS = {
    "AWS アクセスキー": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "GitHub トークン": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})"),
    "Slack トークン": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "API キー（sk-）": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "Notion トークン": re.compile(r"\b(?:secret|ntn)_[A-Za-z0-9]{40,}"),
    "Google API キー": re.compile(r"\bAIza[0-9A-Za-z_-]{35}"),
    "秘密鍵": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "パスワード等の値": re.compile(
        r"(?i)(?:\b(?:password|passwd|pwd|secret|token|api[_-]?key)|パスワード)\s*[:：=]\s*\S{4,}"),
}
# Unknown token formats: long runs mixing upper, lower and digits (hex hashes and UUIDs don't qualify)
RANDOM_RUN = re.compile(r"[A-Za-z0-9+/]{32,}")


def find_secrets(text: str) -> list[str]:
    hits = [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(text)]
    if any(re.search(r"[A-Z]", m) and re.search(r"[a-z]", m) and re.search(r"[0-9]", m)
           for m in RANDOM_RUN.findall(text)):
        hits.append("ランダムな長い文字列")
    return hits


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"{CONFIG_PATH} がありません。"
                 '{"data_source_url": "collection://..."} の形式で作成してください')
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def page_properties(s: dict, date: str) -> dict:
    props = {
        "タイトル": s["title"][:TEXT_LIMIT],
        # entries collected before Codex support have no tool and were all Claude Code
        "ツール": s.get("tool", CLAUDE),
        "リポジトリ": s.get("repo", "")[:TEXT_LIMIT],
        "ブランチ": s.get("branch", "")[:TEXT_LIMIT],
        "要約": s["summary"][:TEXT_LIMIT],
        "セッションID": f"{s['session_id']}:{date}",
        "date:日時:start": s["start"],
        "date:日時:is_datetime": 1,
    }
    if s["end"] != s["start"]:
        props["date:日時:end"] = s["end"]
    return props


def payload(day: dt.date) -> None:
    config = load_config()
    json_path = OUT_DIR / f"{day}.json"
    if not json_path.exists():
        sys.exit(f"{json_path} がありません。先に collect を実行してください")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    pages, skipped, flagged = [], [], []
    for s in data["sessions"]:
        if s.get("skip"):
            skipped.append({"index": s["index"], "reason": "skip"})
            continue
        if not s.get("title") or not s.get("summary"):
            skipped.append({"index": s["index"], "reason": "title/summary が空"})
            continue
        hits = find_secrets(f"{s['title']}\n{s['summary']}")
        if hits:
            flagged.append((s["index"], hits))
            continue
        pages.append({"index": s["index"], "properties": page_properties(s, data["date"])})
    if flagged:
        # report only the kind of match, never the matched text itself
        for index, hits in flagged:
            print(f"✗ [{index}] 秘密情報の可能性: {'、'.join(hits)}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps({
        "data_source_url": config["data_source_url"],
        "key_suffix": f":{data['date']}",
        "pages": pages,
        "skipped": skipped,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("collect", "payload"):
        sys.exit("usage: daily_log.py collect|payload [YYYY-MM-DD]")
    day = local_day(sys.argv[2] if len(sys.argv) > 2 else None)
    collect(day) if sys.argv[1] == "collect" else payload(day)
